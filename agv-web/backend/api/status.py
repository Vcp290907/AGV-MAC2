from flask import Blueprint, jsonify

status_bp = Blueprint('status', __name__)

@status_bp.route("/status")
def status():
    return {"bateria": 90, "conexao": "ok"}

@status_bp.route("/discovery/status")
def discovery_status():
    """Retorna status do sistema de descoberta automática"""
    try:
        from backend_announcer import get_announcer
        announcer = get_announcer()
        stats = announcer.get_stats()
        return jsonify({
            "success": True,
            "announcer": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500