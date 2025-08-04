from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
import os
import uuid
from database import get_db_connection

armazem_bp = Blueprint('armazem', __name__)

# Configurações de upload
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@armazem_bp.route("/armazem/categorias", methods=["GET"])
def listar_categorias():
    """Lista todas as categorias disponíveis"""
    conn = get_db_connection()
    categorias = conn.execute('''
        SELECT id, nome FROM categorias ORDER BY nome
    ''').fetchall()
    conn.close()
    
    # Se não houver categorias, retornar padrões
    if not categorias:
        return jsonify([
            {"id": 1, "nome": "Fixação"},
            {"id": 2, "nome": "Eletrônicos"},
            {"id": 3, "nome": "Ferramentas"},
            {"id": 4, "nome": "Diversos"}
        ])
    
    return jsonify([dict(categoria) for categoria in categorias])

@armazem_bp.route("/armazem/proxima-tag", methods=["GET"])
def gerar_proxima_tag():
    """Gera a próxima tag automática"""
    conn = get_db_connection()
    
    # Buscar a maior tag numérica atual
    result = conn.execute('''
        SELECT MAX(CAST(SUBSTR(tag, 4) AS INTEGER)) as max_num
        FROM itens 
        WHERE tag LIKE 'TAG%' AND SUBSTR(tag, 4) GLOB '[0-9]*'
    ''').fetchone()
    
    conn.close()
    
    proximo_numero = (result['max_num'] or 0) + 1
    proxima_tag = f"TAG{proximo_numero:04d}"  # TAG0001, TAG0002, etc.
    
    return jsonify({"tag": proxima_tag})

@armazem_bp.route("/armazem/upload-imagem", methods=["POST"])
def upload_imagem():
    """Faz upload de uma imagem"""
    if 'imagem' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['imagem']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    if file and allowed_file(file.filename):
        # Gerar nome único para o arquivo
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Garantir que a pasta existe
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Salvar arquivo
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        return jsonify({
            "success": True,
            "filename": unique_filename,
            "message": "Imagem enviada com sucesso"
        })
    
    return jsonify({"error": "Tipo de arquivo não permitido"}), 400

@armazem_bp.route("/armazem/itens", methods=["GET"])
def listar_itens_armazem():
    """Lista todos os itens do armazém com localização"""
    conn = get_db_connection()
    itens = conn.execute('''
        SELECT id, nome, tag, categoria, imagem, disponivel, 
               posicao_x, posicao_y, corredor, sub_corredor
        FROM itens 
        ORDER BY corredor, sub_corredor, posicao_x, posicao_y
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(item) for item in itens])

@armazem_bp.route("/armazem/itens", methods=["POST"])
def criar_item_armazem():
    """Cria um novo item no armazém"""
    data = request.json
    
    # Validações
    nome = data.get('nome', '').strip()
    tag = data.get('tag', '').strip()
    categoria = data.get('categoria', 'Diversos').strip()
    imagem = data.get('imagem')
    corredor = data.get('corredor', '1')
    sub_corredor = data.get('sub_corredor', '1')
    posicao_x = data.get('posicao_x', 1)
    posicao_y = data.get('posicao_y', 1)
    
    if not nome:
        return jsonify({"error": "Nome é obrigatório"}), 400
    
    if not tag:
        return jsonify({"error": "Tag é obrigatória"}), 400
    
    if posicao_x not in [1, 2, 3, 4]:
        return jsonify({"error": "Posição deve ser entre 1 e 4"}), 400
    
    conn = get_db_connection()
    
    # Verificar se tag já existe
    existing_tag = conn.execute('SELECT id FROM itens WHERE tag = ?', (tag,)).fetchone()
    if existing_tag:
        conn.close()
        return jsonify({"error": "Tag já existe"}), 400
    
    # Verificar se posição já está ocupada
    existing_pos = conn.execute('''
        SELECT id FROM itens 
        WHERE corredor = ? AND sub_corredor = ? AND posicao_x = ?
    ''', (corredor, sub_corredor, posicao_x)).fetchone()
    
    if existing_pos:
        conn.close()
        return jsonify({"error": "Posição já ocupada"}), 400
    
    # Criar item
    cursor = conn.execute('''
        INSERT INTO itens (nome, tag, categoria, imagem, corredor, sub_corredor, posicao_x, posicao_y, disponivel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
    ''', (nome, tag, categoria, imagem, corredor, sub_corredor, posicao_x, posicao_y))
    
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "Item criado com sucesso",
        "item_id": item_id
    })

@armazem_bp.route("/armazem/itens/<int:item_id>", methods=["PUT"])
def atualizar_item_armazem(item_id):
    """Atualiza informações de um item do armazém"""
    data = request.json
    
    conn = get_db_connection()
    
    # Verificar se item existe
    item = conn.execute('SELECT id FROM itens WHERE id = ?', (item_id,)).fetchone()
    if not item:
        conn.close()
        return jsonify({"error": "Item não encontrado"}), 404
    
    # Verificar se tag já existe em outro item
    if 'tag' in data:
        existing = conn.execute('''
            SELECT id FROM itens WHERE tag = ? AND id != ?
        ''', (data['tag'], item_id)).fetchone()
        
        if existing:
            conn.close()
            return jsonify({"error": "Tag já existe em outro item"}), 400
    
    # Verificar se nova posição já está ocupada
    if all(k in data for k in ['corredor', 'sub_corredor', 'posicao_x']):
        existing_pos = conn.execute('''
            SELECT id FROM itens 
            WHERE corredor = ? AND sub_corredor = ? AND posicao_x = ? AND id != ?
        ''', (data['corredor'], data['sub_corredor'], data['posicao_x'], item_id)).fetchone()
        
        if existing_pos:
            conn.close()
            return jsonify({"error": "Posição já ocupada"}), 400
    
    # Atualizar item
    campos = []
    valores = []
    
    for campo in ['nome', 'tag', 'categoria', 'imagem', 'corredor', 'sub_corredor', 'posicao_x', 'posicao_y']:
        if campo in data:
            campos.append(f'{campo} = ?')
            valores.append(data[campo])
    
    if campos:
        valores.append(item_id)
        query = f"UPDATE itens SET {', '.join(campos)} WHERE id = ?"
        conn.execute(query, valores)
        conn.commit()
    
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "Item atualizado com sucesso"
    })

@armazem_bp.route("/armazem/itens/<int:item_id>", methods=["DELETE"])
def excluir_item_armazem(item_id):
    """Exclui um item do armazém"""
    conn = get_db_connection()
    
    # Verificar se item existe e pegar nome da imagem
    item = conn.execute('SELECT id, imagem FROM itens WHERE id = ?', (item_id,)).fetchone()
    if not item:
        conn.close()
        return jsonify({"error": "Item não encontrado"}), 404
    
    # Excluir arquivo de imagem se existir
    if item['imagem']:
        image_path = os.path.join(UPLOAD_FOLDER, item['imagem'])
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass  # Ignorar erros na exclusão do arquivo
    
    # Excluir item do banco
    conn.execute('DELETE FROM itens WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "Item excluído com sucesso"
    })