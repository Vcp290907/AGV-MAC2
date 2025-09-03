"""
API para comunicação com o Raspberry Pi
Adicione este arquivo ao backend web em: agv-web/backend/api/raspberry.py
"""

from flask import Blueprint, request, jsonify
import requests
import logging
import sys
import os

# Adicionar pasta compartilhada ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'agv-shared'))

from protocolos.comunicacao import (
    criar_comando_mover, 
    criar_comando_parar, 
    validar_comando,
    ConfiguracaoRede
)

raspberry_bp = Blueprint('raspberry', __name__, url_prefix='/agv')
logger = logging.getLogger(__name__)

# Configuração do IP do Raspberry Pi
RASPBERRY_IP = "192.168.1.100"  # Altere para o IP real do seu Raspberry
RASPBERRY_URL = f"http://{RASPBERRY_IP}:{ConfiguracaoRede.PORTA_RASPBERRY}"

@raspberry_bp.route('/enviar_comando', methods=['POST'])
def enviar_comando():
    """Envia comando para o Raspberry Pi"""
    try:
        data = request.get_json()
        
        # Extrair dados do pedido
        destino = data.get('destino')
        itens = data.get('itens', [])
        tipo = data.get('tipo', 'mover')
        
        # Criar comando baseado no tipo
        if tipo == 'mover':
            comando = criar_comando_mover(destino, itens)
        elif tipo == 'parar':
            comando = criar_comando_parar()
        else:
            return jsonify({
                "success": False, 
                "error": "Tipo de comando inválido"
            }), 400
            
        # Validar comando
        if not validar_comando(comando):
            return jsonify({
                "success": False, 
                "error": "Comando inválido"
            }), 400
            
        # Enviar para o Raspberry Pi
        logger.info(f"📤 Enviando comando para Raspberry: {comando}")
        
        response = requests.post(
            f"{RASPBERRY_URL}/executar",
            json=comando,
            timeout=ConfiguracaoRede.TIMEOUT_COMANDO
        )
        
        if response.status_code == 200:
            resultado = response.json()
            logger.info(f"✅ Comando executado: {resultado}")
            
            return jsonify({
                "success": True,
                "resultado": resultado
            })
        else:
            logger.error(f"❌ Erro na resposta do Raspberry: {response.status_code}")
            return jsonify({
                "success": False,
                "error": f"Erro na comunicação: {response.status_code}"
            }), 500
            
    except requests.exceptions.Timeout:
        logger.error("⏰ Timeout na comunicação com Raspberry")
        return jsonify({
            "success": False,
            "error": "Timeout na comunicação com o AGV"
        }), 408
        
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Erro de conexão com Raspberry")
        return jsonify({
            "success": False,
            "error": "AGV não está acessível na rede"
        }), 503
        
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return jsonify({
            "success": False,
            "error": "Erro interno do servidor"
        }), 500

@raspberry_bp.route('/status', methods=['GET'])
def obter_status_agv():
    """Obtém status atual do AGV no Raspberry Pi"""
    try:
        logger.debug("📡 Consultando status do AGV...")
        
        response = requests.get(
            f"{RASPBERRY_URL}/status",
            timeout=ConfiguracaoRede.TIMEOUT_STATUS
        )
        
        if response.status_code == 200:
            status = response.json()
            return jsonify(status)
        else:
            return jsonify({
                "error": f"Erro na comunicação: {response.status_code}"
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Timeout na comunicação com o AGV"
        }), 408
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "AGV não está acessível na rede",
            "offline": True
        }), 503
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        return jsonify({
            "error": "Erro interno do servidor"
        }), 500

@raspberry_bp.route('/parar_emergencia', methods=['POST'])
def parar_emergencia():
    """Para o AGV imediatamente (botão de emergência)"""
    try:
        comando = criar_comando_parar("emergencia")
        
        logger.warning("🚨 COMANDO DE EMERGÊNCIA - Parando AGV!")
        
        response = requests.post(
            f"{RASPBERRY_URL}/executar",
            json=comando,
            timeout=5  # Timeout reduzido para emergência
        )
        
        if response.status_code == 200:
            return jsonify({
                "success": True,
                "message": "AGV parado com sucesso"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Falha ao parar AGV"
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Erro na parada de emergência: {e}")
        return jsonify({
            "success": False,
            "error": "Falha crítica na parada de emergência"
        }), 500

@raspberry_bp.route('/configurar_ip', methods=['POST'])
def configurar_ip_raspberry():
    """Configura o IP do Raspberry Pi dinamicamente"""
    global RASPBERRY_IP, RASPBERRY_URL
    
    try:
        data = request.get_json()
        novo_ip = data.get('ip')
        
        if not novo_ip:
            return jsonify({
                "success": False,
                "error": "IP não fornecido"
            }), 400
            
        # Validar formato do IP (básico)
        partes = novo_ip.split('.')
        if len(partes) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in partes):
            return jsonify({
                "success": False,
                "error": "Formato de IP inválido"
            }), 400
            
        # Atualizar configuração
        RASPBERRY_IP = novo_ip
        RASPBERRY_URL = f"http://{RASPBERRY_IP}:{ConfiguracaoRede.PORTA_RASPBERRY}"
        
        logger.info(f"🔧 IP do Raspberry atualizado para: {RASPBERRY_IP}")
        
        return jsonify({
            "success": True,
            "message": f"IP configurado para {RASPBERRY_IP}"
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar IP: {e}")
        return jsonify({
            "success": False,
            "error": "Erro ao configurar IP"
        }), 500
