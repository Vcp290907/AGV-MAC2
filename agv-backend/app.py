from flask import Flask, send_from_directory
from flask_cors import CORS
import os
from api.status import status_bp
from api.auth import auth_bp
from api.itens import itens_bp
from api.pedidos import pedidos_bp
from api.dispositivos import dispositivos_bp
from api.armazem import armazem_bp  # ← Adicionar
from database import init_db

app = Flask(__name__)
CORS(app)

# Criar pasta para imagens se não existir
STATIC_FOLDER = 'static'
IMAGES_FOLDER = os.path.join(STATIC_FOLDER, 'images')
os.makedirs(IMAGES_FOLDER, exist_ok=True)

# Rota para servir imagens
@app.route('/static/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGES_FOLDER, filename)

# Registrar blueprints
app.register_blueprint(status_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(itens_bp)
app.register_blueprint(pedidos_bp)
app.register_blueprint(dispositivos_bp)
app.register_blueprint(armazem_bp)  # ← Adicionar

# Inicializar banco de dados
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)