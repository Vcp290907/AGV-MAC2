from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    usuario = data.get("usuario")
    senha = data.get("senha")
    
    # Teste simples: usuário admin, senha 123
    
    if usuario == "admin" and senha == "123":
        return jsonify({"success": True, "perfil": "gerente"})
    return jsonify({"success": False, "message": "Credenciais inválidas"}), 401