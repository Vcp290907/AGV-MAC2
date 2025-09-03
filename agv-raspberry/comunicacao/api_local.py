"""
API Local do Raspberry Pi
Recebe comandos da interface web via HTTP
"""

from flask import Flask, request, jsonify
import asyncio
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
agv_system = None

@app.route('/executar', methods=['POST'])
def executar_comando():
    """Endpoint para executar comandos vindos da interface web"""
    try:
        comando = request.get_json()
        logger.info(f"📨 Comando recebido: {comando}")
        
        # Executar comando de forma assíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resultado = loop.run_until_complete(agv_system.executar_comando(comando))
        
        return jsonify({
            "success": True,
            "resultado": resultado
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao executar comando: {e}")
        return jsonify({
            "success": False,
            "erro": str(e)
        }), 500

@app.route('/status', methods=['GET'])
def obter_status():
    """Endpoint para obter status do AGV"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status = loop.run_until_complete(agv_system.obter_status())
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/camera', methods=['GET'])
def stream_camera():
    """Endpoint para stream da câmera (futuro)"""
    return jsonify({"status": "Em desenvolvimento"})

async def iniciar_servidor(agv_instance):
    """Inicia o servidor Flask com referência ao sistema AGV"""
    global agv_system
    agv_system = agv_instance
    
    logger.info("🌐 Iniciando servidor de comunicação na porta 8080...")
    app.run(host='0.0.0.0', port=8080, debug=False)
