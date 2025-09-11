from flask import Blueprint, jsonify, request
from database import get_db_connection

itens_bp = Blueprint('itens', __name__)

@itens_bp.route("/itens", methods=["GET"])
def listar_itens():
    """Lista todos os itens disponíveis"""
    conn = get_db_connection()
    itens = conn.execute('''
        SELECT id, nome, tag, categoria, imagem, disponivel, posicao_x, posicao_y, corredor, sub_corredor
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
        SELECT id, nome, tag, categoria, imagem, disponivel, posicao_x, posicao_y, corredor, sub_corredor
        FROM itens
        WHERE disponivel = 1
        AND (nome LIKE ? OR tag LIKE ?)
        ORDER BY categoria, nome
    ''', (f'%{termo}%', f'%{termo}%')).fetchall()
    conn.close()

    return jsonify([dict(item) for item in itens])

@itens_bp.route("/itens/tag/<tag>", methods=["GET"])
def buscar_item_por_tag(tag):
    """Busca item específico por tag"""
    conn = get_db_connection()
    item = conn.execute('''
        SELECT id, nome, tag, categoria, imagem, disponivel, posicao_x, posicao_y, corredor, sub_corredor
        FROM itens
        WHERE tag = ? AND disponivel = 1
    ''', (tag,)).fetchone()
    conn.close()

    if item:
        return jsonify(dict(item))
    else:
        return jsonify({"error": "Item não encontrado"}), 404

@itens_bp.route("/itens/localizacao/<corredor>/<sub_corredor>", methods=["GET"])
def buscar_itens_por_localizacao(corredor, sub_corredor):
    """Busca itens por localização (corredor/sub-corredor)"""
    conn = get_db_connection()
    itens = conn.execute('''
        SELECT id, nome, tag, categoria, imagem, disponivel, posicao_x, posicao_y, corredor, sub_corredor
        FROM itens
        WHERE corredor = ? AND sub_corredor = ? AND disponivel = 1
        ORDER BY posicao_x
    ''', (corredor, sub_corredor)).fetchall()
    conn.close()

    return jsonify([dict(item) for item in itens])

@itens_bp.route("/itens/buscar", methods=["GET"])
def buscar_item_geral():
    """Busca geral de itens por qualquer critério"""
    termo = request.args.get('q', '').strip()

    conn = get_db_connection()
    itens = conn.execute('''
        SELECT id, nome, tag, categoria, imagem, disponivel, posicao_x, posicao_y, corredor, sub_corredor
        FROM itens
        WHERE disponivel = 1
        AND (nome LIKE ? OR tag LIKE ? OR categoria LIKE ? OR corredor LIKE ? OR sub_corredor LIKE ?)
        ORDER BY categoria, nome
    ''', (f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%')).fetchall()
    conn.close()

    return jsonify([dict(item) for item in itens])