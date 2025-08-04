from flask import Blueprint, jsonify, request
from database import get_db_connection

pedidos_bp = Blueprint('pedidos', __name__)

@pedidos_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    """Cria um novo pedido"""
    data = request.json
    usuario_id = data.get('usuario_id')  # Agora recebe ID do usuário
    itens_ids = data.get('itens', [])
    dispositivo_id = data.get('dispositivo_id')
    
    if not usuario_id or not itens_ids or not dispositivo_id:
        return jsonify({"error": "Usuario_id, itens e dispositivo são obrigatórios"}), 400
    
    if len(itens_ids) > 4:
        return jsonify({"error": "Máximo 4 itens por pedido"}), 400
    
    conn = get_db_connection()
    
    # Verificar se usuário existe
    usuario = conn.execute('SELECT id, nome FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    if not usuario:
        conn.close()
        return jsonify({"error": "Usuário não encontrado"}), 400
    
    # Verificar se dispositivo está disponível
    dispositivo = conn.execute('''
        SELECT status FROM dispositivos WHERE id = ?
    ''', (dispositivo_id,)).fetchone()
    
    if not dispositivo or dispositivo['status'] != 'disponivel':
        conn.close()
        return jsonify({"error": "Dispositivo não disponível"}), 400
    
    # Marcar dispositivo como ocupado
    conn.execute('''
        UPDATE dispositivos SET status = 'ocupado' WHERE id = ?
    ''', (dispositivo_id,))
    
    # Criar pedido
    cursor = conn.execute('''
        INSERT INTO pedidos (usuario_id, status, dispositivo_id) 
        VALUES (?, 'pendente', ?)
    ''', (usuario_id, dispositivo_id))
    
    pedido_id = cursor.lastrowid
    
    # Adicionar itens ao pedido
    for item_id in itens_ids:
        conn.execute('''
            INSERT INTO pedido_itens (pedido_id, item_id)
            VALUES (?, ?)
        ''', (pedido_id, item_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "pedido_id": pedido_id,
        "message": f"Pedido criado com sucesso para {usuario['nome']}!"
    })

@pedidos_bp.route("/pedidos", methods=["GET"])
def listar_pedidos():
    """Lista todos os pedidos"""
    conn = get_db_connection()
    pedidos = conn.execute('''
        SELECT p.id, u.nome as usuario_nome, u.username, p.status, p.created_at,
               d.nome as dispositivo_nome, d.codigo as dispositivo_codigo,
               GROUP_CONCAT(i.nome) as itens
        FROM pedidos p
        LEFT JOIN usuarios u ON p.usuario_id = u.id
        LEFT JOIN dispositivos d ON p.dispositivo_id = d.id
        LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
        LEFT JOIN itens i ON pi.item_id = i.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(pedido) for pedido in pedidos])