from flask import Blueprint

status_bp = Blueprint('status', __name__)

@status_bp.route("/status")
def status():
    return {"bateria": 87, "conexao": "ok"}