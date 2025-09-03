from flask import Blueprint, jsonify, request
from database import get_db_connection

pedidos_bp = Blueprint('pedidos', __name__)

@pedidos_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    """Cria um novo pedido"""
    data = request.json
    usuario_id = data.get('usuario_id')  # Agora recebe ID do usuário
    itens_ids = data.get('itens', [])
    dispositivo_id = data.get('dispositivo_id')
    
    if not usuario_id or not itens_ids or not dispositivo_id:
        return jsonify({"error": "Usuario_id, itens e dispositivo são obrigatórios"}), 400
    
    if len(itens_ids) > 4:
        return jsonify({"error": "Máximo 4 itens por pedido"}), 400
    
    conn = get_db_connection()
    
    # Verificar se usuário existe
    usuario = conn.execute('SELECT id, nome FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    if not usuario:
        conn.close()
        return jsonify({"error": "Usuário não encontrado"}), 400
    
    # Verificar se dispositivo está disponível
    dispositivo = conn.execute('''
        SELECT status FROM dispositivos WHERE id = ?
    ''', (dispositivo_id,)).fetchone()
    
    if not dispositivo or dispositivo['status'] != 'disponivel':
        conn.close()
        return jsonify({"error": "Dispositivo não disponível"}), 400
    
    # Marcar dispositivo como ocupado
    conn.execute('''
        UPDATE dispositivos SET status = 'ocupado' WHERE id = ?
    ''', (dispositivo_id,))
    
    # Criar pedido
    cursor = conn.execute('''
        INSERT INTO pedidos (usuario_id, status, dispositivo_id) 
        VALUES (?, 'pendente', ?)
    ''', (usuario_id, dispositivo_id))
    
    pedido_id = cursor.lastrowid
    
    # Adicionar itens ao pedido
    for item_id in itens_ids:
        conn.execute('''
            INSERT INTO pedido_itens (pedido_id, item_id)
            VALUES (?, ?)
        ''', (pedido_id, item_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "pedido_id": pedido_id,
        "message": f"Pedido criado com sucesso para {usuario['nome']}!"
    })

@pedidos_bp.route("/pedidos", methods=["GET"])
def listar_pedidos():
    """Lista todos os pedidos com filtros opcionais"""
    dispositivo_id = request.args.get('dispositivo_id')
    status_filter = request.args.get('status')
    
    query = '''
        SELECT p.id, u.nome as usuario_nome, u.username, p.status, p.created_at,
               d.nome as dispositivo_nome, d.codigo as dispositivo_codigo,
               GROUP_CONCAT(i.nome) as itens,
               GROUP_CONCAT(i.corredor) as corredores,
               GROUP_CONCAT(i.sub_corredor) as sub_corredores,
               GROUP_CONCAT(i.posicao_x) as posicoes_x
        FROM pedidos p
        LEFT JOIN usuarios u ON p.usuario_id = u.id
        LEFT JOIN dispositivos d ON p.dispositivo_id = d.id
        LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
        LEFT JOIN itens i ON pi.item_id = i.id
    '''
    
    conditions = []
    params = []
    
    if dispositivo_id:
        conditions.append('p.dispositivo_id = ?')
        params.append(dispositivo_id)
    
    if status_filter:
        # Se múltiplos status (separados por vírgula)
        status_list = status_filter.split(',')
        placeholders = ','.join(['?' for _ in status_list])
        conditions.append(f'p.status IN ({placeholders})')
        params.extend(status_list)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' GROUP BY p.id ORDER BY p.created_at DESC'
    
    conn = get_db_connection()
    pedidos = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(pedido) for pedido in pedidos])

@pedidos_bp.route("/pedidos/<int:pedido_id>/cancelar", methods=["PUT"])
def cancelar_pedido(pedido_id):
    """Cancela um pedido específico"""
    conn = get_db_connection()
    
    # Verificar se o pedido existe
    pedido = conn.execute('SELECT id, status, dispositivo_id FROM pedidos WHERE id = ?', (pedido_id,)).fetchone()
    
    if not pedido:
        conn.close()
        return jsonify({"error": "Pedido não encontrado"}), 404
    
    if pedido['status'] in ['concluido', 'cancelado']:
        conn.close()
        return jsonify({"error": "Pedido já foi finalizado"}), 400
    
    # Atualizar status do pedido para cancelado
    conn.execute('UPDATE pedidos SET status = ? WHERE id = ?', ('cancelado', pedido_id))
    
    # Liberar dispositivo se estava ocupado
    if pedido['dispositivo_id']:
        conn.execute('UPDATE dispositivos SET status = ? WHERE id = ?', ('disponivel', pedido['dispositivo_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Pedido cancelado com sucesso"})

@pedidos_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    """Atualiza o status de um pedido"""
    data = request.json
    novo_status = data.get('status')
    
    if not novo_status:
        return jsonify({"error": "Status é obrigatório"}), 400
    
    status_validos = ['pendente', 'em_andamento', 'coletando', 'concluido', 'cancelado']
    if novo_status not in status_validos:
        return jsonify({"error": "Status inválido"}), 400
    
    conn = get_db_connection()
    
    # Verificar se o pedido existe
    pedido = conn.execute('SELECT id, dispositivo_id FROM pedidos WHERE id = ?', (pedido_id,)).fetchone()
    
    if not pedido:
        conn.close()
        return jsonify({"error": "Pedido não encontrado"}), 404
    
    # Atualizar status
    conn.execute('UPDATE pedidos SET status = ? WHERE id = ?', (novo_status, pedido_id))
    
    # Se concluído ou cancelado, liberar dispositivo
    if novo_status in ['concluido', 'cancelado'] and pedido['dispositivo_id']:
        conn.execute('UPDATE dispositivos SET status = ? WHERE id = ?', ('disponivel', pedido['dispositivo_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Status atualizado para {novo_status}"})

@pedidos_bp.route("/pedidos/ativo", methods=["GET"])
def pedido_ativo():
    """Retorna o pedido atualmente ativo (em andamento)"""
    conn = get_db_connection()
    pedido = conn.execute('''
        SELECT p.id, u.nome as usuario_nome, u.username, p.status, p.created_at,
               d.nome as dispositivo_nome, d.codigo as dispositivo_codigo,
               GROUP_CONCAT(i.nome) as itens,
               GROUP_CONCAT(i.corredor) as corredores,
               GROUP_CONCAT(i.sub_corredor) as sub_corredores,
               GROUP_CONCAT(i.posicao_x) as posicoes_x
        FROM pedidos p
        LEFT JOIN usuarios u ON p.usuario_id = u.id
        LEFT JOIN dispositivos d ON p.dispositivo_id = d.id
        LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
        LEFT JOIN itens i ON pi.item_id = i.id
        WHERE p.status IN ('em_andamento', 'coletando')
        GROUP BY p.id
        ORDER BY p.created_at DESC
        LIMIT 1
    ''').fetchone()
    conn.close()
    
    if pedido:
        return jsonify(dict(pedido))
    else:
        return jsonify(None)

@pedidos_bp.route("/pedidos/<int:pedido_id>/remover-item", methods=["PUT"])
def remover_item_pedido(pedido_id):
    """Remove um item específico de um pedido"""
    data = request.json
    item_index = data.get('item_index')
    item_nome = data.get('item_nome')
    
    if item_index is None:
        return jsonify({"error": "Índice do item é obrigatório"}), 400
    
    conn = get_db_connection()
    
    # Verificar se o pedido existe
    pedido = conn.execute('SELECT id, status FROM pedidos WHERE id = ?', (pedido_id,)).fetchone()
    
    if not pedido:
        conn.close()
        return jsonify({"error": "Pedido não encontrado"}), 404
    
    if pedido['status'] in ['concluido', 'cancelado']:
        conn.close()
        return jsonify({"error": "Pedido já foi finalizado"}), 400
    
    # Obter itens do pedido
    itens_pedido = conn.execute('''
        SELECT pi.id, i.nome, i.id as item_id
        FROM pedido_itens pi
        JOIN itens i ON pi.item_id = i.id
        WHERE pi.pedido_id = ?
        ORDER BY pi.id
    ''', (pedido_id,)).fetchall()
    
    if item_index >= len(itens_pedido):
        conn.close()
        return jsonify({"error": "Índice de item inválido"}), 400
    
    # Remover o item específico
    item_a_remover = itens_pedido[item_index]
    conn.execute('DELETE FROM pedido_itens WHERE id = ?', (item_a_remover['id'],))
    
    # Verificar se ainda há itens no pedido
    itens_restantes = conn.execute('SELECT COUNT(*) as count FROM pedido_itens WHERE pedido_id = ?', (pedido_id,)).fetchone()
    
    # Se não há mais itens, cancelar o pedido
    if itens_restantes['count'] == 0:
        conn.execute('UPDATE pedidos SET status = ? WHERE id = ?', ('cancelado', pedido_id))
        
        # Liberar dispositivo
        conn.execute('''
            UPDATE dispositivos SET status = 'disponivel' 
            WHERE id = (SELECT dispositivo_id FROM pedidos WHERE id = ?)
        ''', (pedido_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Item {item_nome} removido do pedido"})

@pedidos_bp.route("/pedidos/<int:pedido_id>/cancelar-completo", methods=["PUT"])
def cancelar_pedido_completo(pedido_id):
    """Cancela um pedido completo, removendo itens coletados do armazém"""
    data = request.json
    itens_rota = data.get('itens_rota', [])
    
    conn = get_db_connection()
    
    # Verificar se o pedido existe
    pedido = conn.execute('SELECT id, status, dispositivo_id FROM pedidos WHERE id = ?', (pedido_id,)).fetchone()
    
    if not pedido:
        conn.close()
        return jsonify({"error": "Pedido não encontrado"}), 404
    
    if pedido['status'] in ['concluido', 'cancelado']:
        conn.close()
        return jsonify({"error": "Pedido já foi finalizado"}), 400
    
    # Processar itens coletados - remover do armazém
    for item_info in itens_rota:
        if item_info.get('coletado', False):  # Se foi coletado (status 'P')
            # Marcar como indisponível no armazém
            conn.execute('''
                UPDATE itens SET disponivel = 0 
                WHERE nome = ? AND disponivel = 1
                LIMIT 1
            ''', (item_info['nome'],))
    
    # Cancelar o pedido
    conn.execute('UPDATE pedidos SET status = ? WHERE id = ?', ('cancelado', pedido_id))
    
    # Liberar dispositivo
    if pedido['dispositivo_id']:
        conn.execute('UPDATE dispositivos SET status = ? WHERE id = ?', ('disponivel', pedido['dispositivo_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Pedido cancelado e itens coletados removidos do armazém"})

@pedidos_bp.route("/pedidos/<int:pedido_id>/iniciar", methods=["PUT"])
def iniciar_pedido(pedido_id):
    """Inicia um pedido pendente"""
    conn = get_db_connection()
    
    # Verificar se o pedido existe e está pendente
    pedido = conn.execute('SELECT id, status FROM pedidos WHERE id = ?', (pedido_id,)).fetchone()
    
    if not pedido:
        conn.close()
        return jsonify({"error": "Pedido não encontrado"}), 404
    
    if pedido['status'] != 'pendente':
        conn.close()
        return jsonify({"error": "Apenas pedidos pendentes podem ser iniciados"}), 400
    
    # Atualizar status para em_andamento
    conn.execute('UPDATE pedidos SET status = ? WHERE id = ?', ('em_andamento', pedido_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Pedido iniciado com sucesso"})