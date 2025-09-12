from flask import Flask, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import threading
import time
from api.status import status_bp
from api.auth import auth_bp
from api.itens import itens_bp
from api.pedidos import pedidos_bp
from api.dispositivos import dispositivos_bp
from api.armazem import armazem_bp
from api.raspberry import raspberry_bp
from database import init_db, get_db_connection

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

STATIC_FOLDER = 'static'
IMAGES_FOLDER = os.path.join(STATIC_FOLDER, 'images')
os.makedirs(IMAGES_FOLDER, exist_ok=True)

# Global variable to store connected clients
connected_clients = set()

@app.route('/static/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGES_FOLDER, filename)

app.register_blueprint(status_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(itens_bp)
app.register_blueprint(pedidos_bp)
app.register_blueprint(dispositivos_bp)
app.register_blueprint(armazem_bp)
app.register_blueprint(raspberry_bp)

init_db()

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    connected_clients.add(request.sid)
    print(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to AGV System'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    connected_clients.discard(request.sid)
    print(f"Client disconnected: {request.sid}")

@socketio.on('join_room')
def handle_join_room(data):
    """Handle joining a specific room (e.g., for AGV monitoring)"""
    room = data.get('room')
    if room:
        join_room(room)
        emit('room_joined', {'room': room})

@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle leaving a specific room"""
    room = data.get('room')
    if room:
        leave_room(room)
        emit('room_left', {'room': room})

def broadcast_agv_status():
    """Broadcast AGV status updates to all connected clients"""
    while True:
        try:
            conn = get_db_connection()

            # Get all devices with their current status
            devices = conn.execute('''
                SELECT id, nome, codigo, status, bateria, localizacao
                FROM dispositivos
            ''').fetchall()

            # Get active orders with detailed item information
            active_orders = conn.execute('''
                SELECT p.id, p.status, p.created_at, p.dispositivo_id,
                       u.nome as usuario_nome, u.username,
                       d.nome as dispositivo_nome, d.codigo as dispositivo_codigo,
                       GROUP_CONCAT(i.nome) as itens,
                       GROUP_CONCAT(i.corredor) as corredores,
                       GROUP_CONCAT(i.sub_corredor) as sub_corredores,
                       GROUP_CONCAT(i.posicao_x) as posicoes_x,
                       COUNT(pi.id) as total_itens
                FROM pedidos p
                LEFT JOIN usuarios u ON p.usuario_id = u.id
                LEFT JOIN dispositivos d ON p.dispositivo_id = d.id
                LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
                LEFT JOIN itens i ON pi.item_id = i.id
                WHERE p.status IN ('pendente', 'em_andamento', 'coletando')
                GROUP BY p.id
                ORDER BY p.created_at DESC
            ''').fetchall()

            conn.close()

            # Prepare status data
            status_data = {
                'timestamp': time.time(),
                'devices': [dict(device) for device in devices],
                'active_orders': [dict(order) for order in active_orders],
                'total_clients': len(connected_clients)
            }

            # Broadcast to all connected clients
            socketio.emit('system_status', status_data)

        except Exception as e:
            print(f"Error broadcasting status: {e}")

        # Broadcast every 2 seconds
        socketio.sleep(2)

# Start background thread for status broadcasting
def start_status_broadcast():
    """Start the background thread for status broadcasting"""
    thread = threading.Thread(target=broadcast_agv_status, daemon=True)
    thread.start()

# Start the status broadcast thread when the app starts
start_status_broadcast()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)