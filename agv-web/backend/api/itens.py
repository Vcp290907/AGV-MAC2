from flask import Blueprint, jsonify, request
from database import get_db_connection

itens_bp = Blueprint('itens', __name__)

@itens_bp.route("/itens", methods=["GET"])
def listar_itens():
    """Lista todos os itens disponíveis"""
    conn = get_db_connection()
    itens = conn.execute('''
        SELECT id, nome, tag, categoria, imagem, disponivel, posicao_x, posicao_y
        FROM itens 
        WHERE disponivel = 1
        ORDER BY categoria, nome
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(item) for item in itens])

@itens_bp.route("/itens/pesquisar", methods=["GET"])
def pesquisar_itens():
    """Pesquisa itens por nome ou tag"""
    termo = request.args.get('q', '').strip()
    
    conn = get_db_connection()
    itens = conn.execute('''
        SELECT id, nome, tag, categoria, imagem, disponivel, posicao_x, posicao_y
        FROM itens 
        WHERE disponivel = 1 
        AND (nome LIKE ? OR tag LIKE ?)
        ORDER BY categoria, nome
    ''', (f'%{termo}%', f'%{termo}%')).fetchall()
    conn.close()
    
    return jsonify([dict(item) for item in itens])