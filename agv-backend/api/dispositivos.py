from flask import Blueprint, jsonify, request
from database import get_db_connection

dispositivos_bp = Blueprint('dispositivos', __name__)

@dispositivos_bp.route("/dispositivos", methods=["GET"])
def listar_dispositivos():
    """Lista todos os dispositivos"""
    conn = get_db_connection()
    dispositivos = conn.execute('''
        SELECT id, nome, codigo, status, bateria, localizacao
        FROM dispositivos 
        ORDER BY nome
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(dispositivo) for dispositivo in dispositivos])

@dispositivos_bp.route("/dispositivos/disponiveis", methods=["GET"])
def listar_dispositivos_disponiveis():
    """Lista apenas dispositivos disponíveis"""
    conn = get_db_connection()
    dispositivos = conn.execute('''
        SELECT id, nome, codigo, status, bateria, localizacao
        FROM dispositivos 
        WHERE status = 'disponivel'
        ORDER BY nome
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(dispositivo) for dispositivo in dispositivos])

@dispositivos_bp.route("/dispositivos/<int:dispositivo_id>/status", methods=["PUT"])
def atualizar_status_dispositivo(dispositivo_id):
    """Atualiza status do dispositivo"""
    data = request.json
    novo_status = data.get('status')
    
    if novo_status not in ['disponivel', 'ocupado', 'manutencao']:
        return jsonify({"error": "Status inválido"}), 400
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE dispositivos 
        SET status = ?
        WHERE id = ?
    ''', (novo_status, dispositivo_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Status atualizado"})

@dispositivos_bp.route("/dispositivos/<int:dispositivo_id>", methods=["GET"])
def obter_dispositivo(dispositivo_id):
    """Obtém informações de um dispositivo específico"""
    conn = get_db_connection()
    dispositivo = conn.execute('''
        SELECT id, nome, codigo, status, bateria, localizacao
        FROM dispositivos 
        WHERE id = ?
    ''', (dispositivo_id,)).fetchone()
    conn.close()
    
    if dispositivo:
        return jsonify(dict(dispositivo))
    else:
        return jsonify({"error": "Dispositivo não encontrado"}), 404