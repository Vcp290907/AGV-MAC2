from flask import Blueprint, request, jsonify
from database import verificar_usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    """Autenticar usuário"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username e senha são obrigatórios"
        }), 400
    
    usuario = verificar_usuario(username, password)
    
    if usuario:
        return jsonify({
            "success": True,
            "message": "Login realizado com sucesso",
            "usuario": {
                "id": usuario['id'],
                "nome": usuario['nome'],
                "username": usuario['username'],
                "perfil": usuario['perfil']
            }
        })
    else:
        return jsonify({
            "success": False,
            "message": "Credenciais inválidas"
        }), 401

@auth_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    """Lista todos os usuários (apenas para gerentes)"""
    from database import get_db_connection
    
    conn = get_db_connection()
    usuarios = conn.execute('''
        SELECT id, nome, username, perfil, ativo, created_at
        FROM usuarios 
        ORDER BY nome
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(usuario) for usuario in usuarios])

@auth_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    """Criar novo usuário"""
    from database import hash_password, get_db_connection
    
    data = request.json
    nome = data.get('nome', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    perfil = data.get('perfil', '').strip()
    
    if not all([nome, username, password, perfil]):
        return jsonify({
            "success": False,
            "message": "Todos os campos são obrigatórios"
        }), 400
    
    if perfil not in ['gerente', 'funcionario']:
        return jsonify({
            "success": False,
            "message": "Perfil deve ser 'gerente' ou 'funcionario'"
        }), 400
    
    conn = get_db_connection()
    
    # Verificar se username já existe
    existing = conn.execute('SELECT id FROM usuarios WHERE username = ?', (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({
            "success": False,
            "message": "Username já existe"
        }), 400
    
    # Criar usuário
    password_hash = hash_password(password)
    cursor = conn.execute('''
        INSERT INTO usuarios (nome, username, password_hash, perfil)
        VALUES (?, ?, ?, ?)
    ''', (nome, username, password_hash, perfil))
    
    usuario_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "Usuário criado com sucesso",
        "usuario_id": usuario_id
    })

@auth_bp.route("/usuarios/<int:usuario_id>", methods=["PUT"])
def editar_usuario(usuario_id):
    """Editar usuário existente"""
    from database import hash_password, get_db_connection
    
    data = request.json
    
    conn = get_db_connection()
    
    # Verificar se o usuário existe
    usuario_atual = conn.execute(
        'SELECT nome, username, perfil, ativo FROM usuarios WHERE id = ?', 
        (usuario_id,)
    ).fetchone()
    
    if not usuario_atual:
        conn.close()
        return jsonify({
            "success": False,
            "message": "Usuário não encontrado"
        }), 404
    
    # Se apenas o status 'ativo' foi enviado (para alternar status)
    if len(data) == 1 and 'ativo' in data:
        conn.execute(
            'UPDATE usuarios SET ativo = ? WHERE id = ?',
            (data['ativo'], usuario_id)
        )
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "message": "Status do usuário atualizado com sucesso"
        })
    
    # Validação completa para edição completa
    nome = data.get('nome', '').strip()
    username = data.get('username', '').strip()
    perfil = data.get('perfil', '').strip()
    password = data.get('password', '').strip()
    ativo = data.get('ativo', True)
    
    if not all([nome, username, perfil]):
        conn.close()
        return jsonify({
            "success": False,
            "message": "Nome, username e perfil são obrigatórios"
        }), 400
    
    if perfil not in ['gerente', 'funcionario']:
        conn.close()
        return jsonify({
            "success": False,
            "message": "Perfil deve ser 'gerente' ou 'funcionario'"
        }), 400
    
    # Verificar se username já existe (excluindo o usuário atual)
    existing = conn.execute(
        'SELECT id FROM usuarios WHERE username = ? AND id != ?', 
        (username, usuario_id)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({
            "success": False,
            "message": "Username já existe"
        }), 400
    
    # Atualizar usuário
    if password:
        # Se senha foi fornecida, atualizar com nova senha
        password_hash = hash_password(password)
        conn.execute('''
            UPDATE usuarios 
            SET nome = ?, username = ?, password_hash = ?, perfil = ?, ativo = ?
            WHERE id = ?
        ''', (nome, username, password_hash, perfil, ativo, usuario_id))
    else:
        # Se senha não foi fornecida, manter a senha atual
        conn.execute('''
            UPDATE usuarios 
            SET nome = ?, username = ?, perfil = ?, ativo = ?
            WHERE id = ?
        ''', (nome, username, perfil, ativo, usuario_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "Usuário atualizado com sucesso"
    })

@auth_bp.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
def excluir_usuario(usuario_id):
    """Excluir usuário"""
    from database import get_db_connection
    
    conn = get_db_connection()
    
    # Verificar se o usuário existe
    usuario = conn.execute('SELECT id, username FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    if not usuario:
        conn.close()
        return jsonify({
            "success": False,
            "message": "Usuário não encontrado"
        }), 404
    
    # Verificar se não é o último gerente (pelo menos um gerente deve existir)
    gerentes_count = conn.execute(
        'SELECT COUNT(*) as count FROM usuarios WHERE perfil = "gerente" AND ativo = 1'
    ).fetchone()['count']
    
    usuario_perfil = conn.execute(
        'SELECT perfil FROM usuarios WHERE id = ?', (usuario_id,)
    ).fetchone()['perfil']
    
    if usuario_perfil == 'gerente' and gerentes_count <= 1:
        conn.close()
        return jsonify({
            "success": False,
            "message": "Não é possível excluir o último gerente do sistema"
        }), 400
    
    # Excluir usuário
    conn.execute('DELETE FROM usuarios WHERE id = ?', (usuario_id,))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "Usuário excluído com sucesso"
    })