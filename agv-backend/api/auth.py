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