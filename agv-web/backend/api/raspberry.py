#!/usr/bin/env python3
"""
API para comunicação com Raspberry Pi
Gerencia comandos, status e sincronização com AGVs
"""

from flask import Blueprint, request, jsonify
import logging
import json
from datetime import datetime
from database import get_db_connection

logger = logging.getLogger(__name__)

raspberry_bp = Blueprint('raspberry', __name__)

# Armazenamento temporário de Raspberry Pis conectados
connected_raspberries = {}

@raspberry_bp.route('/agv/register', methods=['POST'])
def register_raspberry():
    """Registra um Raspberry Pi no sistema"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados de registro vazios'
            }), 400

        raspberry_id = f"raspberry_{data.get('ip', 'unknown')}"

        # Registrar Raspberry Pi
        connected_raspberries[raspberry_id] = {
            'ip': data.get('ip'),
            'port': data.get('port', 8080),
            'status': data.get('status', {}),
            'last_seen': datetime.now().isoformat(),
            'registered': True
        }

        logger.info(f"Raspberry Pi registrado: {raspberry_id} - {data.get('ip')}")

        return jsonify({
            'success': True,
            'message': f'Raspberry Pi {raspberry_id} registrado com sucesso',
            'raspberry_id': raspberry_id
        })

    except Exception as e:
        logger.error(f"Erro ao registrar Raspberry Pi: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raspberry_bp.route('/agv/disconnect', methods=['POST'])
def disconnect_raspberry():
    """Desconecta um Raspberry Pi"""
    try:
        data = request.get_json()
        raspberry_ip = data.get('ip') if data else None

        # Encontrar e remover Raspberry Pi
        raspberry_to_remove = None
        for raspberry_id, raspberry_data in connected_raspberries.items():
            if raspberry_data['ip'] == raspberry_ip:
                raspberry_to_remove = raspberry_id
                break

        if raspberry_to_remove:
            del connected_raspberries[raspberry_to_remove]
            logger.info(f"Raspberry Pi desconectado: {raspberry_to_remove}")
            return jsonify({
                'success': True,
                'message': f'Raspberry Pi {raspberry_to_remove} desconectado'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Raspberry Pi não encontrado'
            }), 404

    except Exception as e:
        logger.error(f"Erro ao desconectar Raspberry Pi: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raspberry_bp.route('/agv/status', methods=['POST'])
def receive_agv_status():
    """Recebe atualização de status do AGV"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados de status vazios'
            }), 400

        agv_id = data.get('agv_id', 'unknown')
        status_data = data.get('status', {})

        logger.info(f"Status recebido do AGV {agv_id}: {status_data}")

        # Atualizar status no banco de dados se necessário
        # TODO: Implementar atualização de status do dispositivo

        # Broadcast status via WebSocket
        from app import socketio
        socketio.emit('agv_status_update', {
            'agv_id': agv_id,
            'status': status_data,
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'success': True,
            'message': f'Status do AGV {agv_id} atualizado'
        })

    except Exception as e:
        logger.error(f"Erro ao receber status do AGV: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raspberry_bp.route('/agv/command_ack', methods=['POST'])
def receive_command_acknowledgment():
    """Recebe confirmação de execução de comando"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados de confirmação vazios'
            }), 400

        command_id = data.get('command_id')
        success = data.get('success', False)
        result = data.get('result', {})

        logger.info(f"Confirmação de comando recebida: {command_id} - Success: {success}")

        # Atualizar status do pedido se necessário
        if command_id and success:
            # TODO: Implementar atualização de status do pedido
            pass

        # Broadcast confirmação via WebSocket
        from app import socketio
        socketio.emit('command_acknowledgment', {
            'command_id': command_id,
            'success': success,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'success': True,
            'message': f'Confirmação de comando {command_id} processada'
        })

    except Exception as e:
        logger.error(f"Erro ao processar confirmação de comando: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raspberry_bp.route('/agv/next_command', methods=['GET'])
def get_next_command():
    """Retorna próximo comando para o AGV"""
    try:
        agv_ip = request.remote_addr
        logger.info(f"Solicitando próximo comando para AGV: {agv_ip}")

        # Encontrar pedidos pendentes
        conn = get_db_connection()

        # Buscar pedido pendente mais antigo
        pending_order = conn.execute('''
            SELECT p.id, p.usuario_id, p.dispositivo_id,
                   u.nome as usuario_nome, u.username,
                   d.nome as dispositivo_nome, d.codigo as dispositivo_codigo,
                   GROUP_CONCAT(i.id) as item_ids,
                   GROUP_CONCAT(i.nome) as item_names,
                   GROUP_CONCAT(i.corredor) as corredores,
                   GROUP_CONCAT(i.sub_corredor) as sub_corredores,
                   GROUP_CONCAT(i.posicao_x) as posicoes_x,
                   COUNT(pi.id) as total_itens
            FROM pedidos p
            LEFT JOIN usuarios u ON p.usuario_id = u.id
            LEFT JOIN dispositivos d ON p.dispositivo_id = d.id
            LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
            LEFT JOIN itens i ON pi.item_id = i.id
            WHERE p.status = 'pendente'
            GROUP BY p.id
            ORDER BY p.created_at ASC
            LIMIT 1
        ''').fetchone()

        if pending_order:
            # Atualizar status para em_andamento
            conn.execute(
                'UPDATE pedidos SET status = ? WHERE id = ?',
                ('em_andamento', pending_order['id'])
            )
            conn.commit()

            # Preparar dados do comando
            command_data = {
                'id': f"cmd_{pending_order['id']}_{datetime.now().timestamp()}",
                'type': 'pickup_order',
                'order_id': pending_order['id'],
                'user': {
                    'id': pending_order['usuario_id'],
                    'name': pending_order['usuario_nome'],
                    'username': pending_order['usuario_username']
                },
                'device': {
                    'id': pending_order['dispositivo_id'],
                    'name': pending_order['dispositivo_nome'],
                    'code': pending_order['dispositivo_codigo']
                },
                'items': []
            }

            # Adicionar itens
            if pending_order['item_ids']:
                item_ids = pending_order['item_ids'].split(',')
                item_names = pending_order['item_names'].split(',')
                corredores = pending_order['corredores'].split(',')
                sub_corredores = pending_order['sub_corredores'].split(',')
                posicoes_x = pending_order['posicoes_x'].split(',')

                for i, item_id in enumerate(item_ids):
                    command_data['items'].append({
                        'id': int(item_id),
                        'name': item_names[i] if i < len(item_names) else 'Unknown',
                        'location': {
                            'corredor': int(corredores[i]) if i < len(corredores) else 1,
                            'sub_corredor': int(sub_corredores[i]) if i < len(sub_corredores) else 1,
                            'posicao_x': int(posicoes_x[i]) if i < len(posicoes_x) else 1
                        }
                    })

            conn.close()

            logger.info(f"Comando preparado para pedido {pending_order['id']}")

            return jsonify({
                'success': True,
                'command': command_data
            })
        else:
            conn.close()
            return jsonify({
                'success': True,
                'command': None,
                'message': 'Nenhum comando pendente'
            })

    except Exception as e:
        logger.error(f"Erro ao obter próximo comando: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raspberry_bp.route('/agv/sync_orders', methods=['GET'])
def sync_orders():
    """Sincroniza pedidos com o Raspberry Pi"""
    try:
        agv_ip = request.remote_addr
        logger.info(f"Sincronizando pedidos com AGV: {agv_ip}")

        conn = get_db_connection()

        # Buscar pedidos ativos
        active_orders = conn.execute('''
            SELECT p.id, p.status, p.created_at,
                   u.nome as usuario_nome, u.username,
                   GROUP_CONCAT(i.nome) as itens,
                   GROUP_CONCAT(i.corredor) as corredores,
                   GROUP_CONCAT(i.sub_corredor) as sub_corredores,
                   GROUP_CONCAT(i.posicao_x) as posicoes_x
            FROM pedidos p
            LEFT JOIN usuarios u ON p.usuario_id = u.id
            LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
            LEFT JOIN itens i ON pi.item_id = i.id
            WHERE p.status IN ('pendente', 'em_andamento', 'coletando')
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''').fetchall()

        conn.close()

        orders_data = []
        for order in active_orders:
            orders_data.append({
                'id': order['id'],
                'status': order['status'],
                'created_at': order['created_at'],
                'usuario_nome': order['usuario_nome'],
                'usuario_username': order['usuario_username'],
                'itens': order['itens'].split(',') if order['itens'] else [],
                'corredores': order['corredores'].split(',') if order['corredores'] else [],
                'sub_corredores': order['sub_corredores'].split(',') if order['sub_corredores'] else [],
                'posicoes_x': order['posicoes_x'].split(',') if order['posicoes_x'] else []
            })

        return jsonify({
            'success': True,
            'orders': orders_data,
            'total_orders': len(orders_data)
        })

    except Exception as e:
        logger.error(f"Erro na sincronização de pedidos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raspberry_bp.route('/agv/connected', methods=['GET'])
def get_connected_raspberries():
    """Retorna lista de Raspberry Pis conectados"""
    try:
        raspberries_list = []
        for raspberry_id, raspberry_data in connected_raspberries.items():
            raspberries_list.append({
                'id': raspberry_id,
                'ip': raspberry_data['ip'],
                'port': raspberry_data['port'],
                'status': raspberry_data['status'],
                'last_seen': raspberry_data['last_seen'],
                'connected': True
            })

        return jsonify({
            'success': True,
            'raspberries': raspberries_list,
            'total_connected': len(raspberries_list)
        })

    except Exception as e:
        logger.error(f"Erro ao obter Raspberry Pis conectados: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raspberry_bp.route('/agv/send_command', methods=['POST'])
def send_command_to_agv():
    """Envia comando para um AGV específico"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados do comando vazios'
            }), 400

        agv_ip = data.get('agv_ip')
        command = data.get('command')

        if not agv_ip or not command:
            return jsonify({
                'success': False,
                'error': 'IP do AGV e comando são obrigatórios'
            }), 400

        # TODO: Implementar envio de comando para AGV específico
        # Por enquanto, apenas log
        logger.info(f"Enviando comando para AGV {agv_ip}: {command}")

        return jsonify({
            'success': True,
            'message': f'Comando enviado para AGV {agv_ip}',
            'command': command
        })

    except Exception as e:
        logger.error(f"Erro ao enviar comando para AGV: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raspberry_bp.route('/test', methods=['GET'])
def test_endpoint():
    """Endpoint de teste para verificar conectividade"""
    return jsonify({
        'success': True,
        'message': 'AGV System API - Raspberry Pi Communication',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'connected_raspberries': len(connected_raspberries)
    })