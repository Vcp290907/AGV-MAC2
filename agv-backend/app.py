from flask import Flask
from flask_cors import CORS
from api.status import status_bp
from api.auth import auth_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(status_bp)
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)