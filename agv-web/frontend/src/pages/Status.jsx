import React, { useState, useEffect } from 'react';
import socketService from '../services/socketService';

export default function Status({ usuario }) {
  const [pedidoAtual, setPedidoAtual] = useState(null);
  const [rotaAtual, setRotaAtual] = useState([]);
  const [statusSistema, setStatusSistema] = useState({ bateria: 0, conexao: 'offline' });
  const [loading, setLoading] = useState(false);
  const [agvs, setAgvs] = useState([]);
  const [agvSelecionado, setAgvSelecionado] = useState('');
  const [statusAgv, setStatusAgv] = useState(null);

  useEffect(() => {
    carregarAgvs();

    // Set up WebSocket event listeners for real-time updates
    const handleSystemStatus = (data) => {
      console.log('Received real-time status update:', data);

      // Update devices
      setAgvs(data.devices || []);

      // Update status system
      setStatusSistema(prev => ({
        ...prev,
        bateria: data.devices?.find(d => d.id == agvSelecionado)?.bateria || prev.bateria,
        conexao: data.devices?.length > 0 ? 'ok' : 'offline'
      }));

      // Update AGV status
      if (agvSelecionado) {
        const selectedDevice = data.devices?.find(d => d.id == agvSelecionado);
        if (selectedDevice) {
          setStatusAgv(selectedDevice);
        }
      }

      // Update active orders for the selected AGV
      const activeOrders = data.active_orders || [];
      const ordersForSelectedAgv = activeOrders.filter(order =>
        agvSelecionado && order.dispositivo_id == agvSelecionado
      );

      if (ordersForSelectedAgv.length > 0) {
        const pedidoAtivo = ordersForSelectedAgv[0]; // Get the most recent active order for this AGV
        console.log('Setting active order:', pedidoAtivo);
        setPedidoAtual(pedidoAtivo);

        // Generate route if there's an active order
        if (pedidoAtivo && pedidoAtivo.itens) {
          gerarRotaAtual(pedidoAtivo);
        }
      } else {
        console.log('No active orders for selected AGV, clearing data');
        setPedidoAtual(null);
        setRotaAtual([]);
      }
    };

    // Add event listener
    socketService.addEventListener('system_status', handleSystemStatus);

    // Initial data load
    carregarDados();

    // Cleanup
    return () => {
      socketService.removeEventListener('system_status', handleSystemStatus);
    };
  }, [agvSelecionado]);

  useEffect(() => {
    if (agvSelecionado) {
      carregarDados();
    }
  }, [agvSelecionado]);

  const carregarAgvs = async () => {
    try {
      const response = await fetch('http://localhost:5000/dispositivos');
      const data = await response.json();
      setAgvs(data);
      
      // Selecionar o primeiro AGV por padrão se não há nenhum selecionado
      if (data.length > 0 && !agvSelecionado) {
        setAgvSelecionado(data[0].id.toString());
      }
    } catch (error) {
      console.error('Erro ao carregar AGVs:', error);
    }
  };

  const carregarDados = async () => {
    try {
      // Carregar status do sistema
      const statusResponse = await fetch('http://localhost:5000/status');
      const statusData = await statusResponse.json();
      setStatusSistema(statusData);

      // Se há AGV selecionado, carregar dados específicos dele
      if (agvSelecionado) {
        // Carregar status específico do AGV
        const agvResponse = await fetch(`http://localhost:5000/dispositivos/${agvSelecionado}`);
        const agvData = await agvResponse.json();
        setStatusAgv(agvData);

        // Carregar pedidos ativos para este AGV específico
        const pedidosResponse = await fetch(`http://localhost:5000/pedidos?dispositivo_id=${agvSelecionado}&status=pendente,em_andamento,coletando`);
        const pedidosData = await pedidosResponse.json();
        
        console.log('Pedidos carregados:', pedidosData); // Debug
        
        let pedidoAtivo = pedidosData.length > 0 ? pedidosData[0] : null;
        
        // Se encontrou um pedido pendente, automaticamente iniciar ele
        if (pedidoAtivo && pedidoAtivo.status === 'pendente') {
          try {
            console.log('Iniciando pedido pendente automaticamente:', pedidoAtivo.id);
            await fetch(`http://localhost:5000/pedidos/${pedidoAtivo.id}/iniciar`, {
              method: 'PUT'
            });
            // Atualizar o status local
            pedidoAtivo.status = 'em_andamento';
          } catch (error) {
            console.error('Erro ao iniciar pedido automaticamente:', error);
          }
        }
        
        // Se não há pedido real, não criar dados de demonstração
        // O usuário verá "Nenhum pedido em andamento" em vez de dados falsos
        
        setPedidoAtual(pedidoAtivo);

        // Se há pedido ativo, gerar rota
        if (pedidoAtivo) {
          console.log('Pedido ativo encontrado:', pedidoAtivo); // Debug
          gerarRotaAtual(pedidoAtivo);
        } else {
          console.log('Nenhum pedido ativo encontrado'); // Debug
          setRotaAtual([]);
        }
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    }
  };

  const gerarRotaAtual = (pedido) => {
    console.log('Gerando rota para pedido:', pedido); // Debug

    // Gerar rota baseada nos dados reais do pedido
    if (!pedido.itens) {
      console.log('Pedido sem itens'); // Debug
      setRotaAtual([]);
      return;
    }

    const itens = pedido.itens.split(',');
    const corredores = pedido.corredores ? pedido.corredores.split(',') : [];
    const subCorredores = pedido.sub_corredores ? pedido.sub_corredores.split(',') : [];
    const posicoesX = pedido.posicoes_x ? pedido.posicoes_x.split(',') : [];

    console.log('Dados do pedido:', { itens, corredores, subCorredores, posicoesX }); // Debug

    const rota = itens.map((item, index) => {
      // Para pedidos reais, todos os itens começam com status 'N' (não pego ainda)
      // O status será atualizado quando o AGV realmente coletar/processar os itens
      const status = 'N'; // Não pego ainda

      return {
        id: index + 1,
        nome: item.trim(),
        corredor: corredores[index] || '1',
        subCorredor: subCorredores[index] || '1',
        posicao: posicoesX[index] || '1',
        status: status,
        coletado: false
      };
    });

    console.log('Rota gerada:', rota); // Debug
    setRotaAtual(rota);
  };

  const cancelarPedido = async () => {
    if (!pedidoAtual) return;

    if (!window.confirm('Tem certeza que deseja cancelar este pedido?')) return;

    setLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/pedidos/${pedidoAtual.id}/cancelar`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await response.json();
      if (data.success) {
        alert('Pedido cancelado com sucesso!');
        carregarDados();
      } else {
        alert('Erro ao cancelar pedido: ' + data.error);
      }
    } catch (error) {
      alert('Erro ao cancelar pedido');
    } finally {
      setLoading(false);
    }
  };

  const simularPedidoTeste = () => {
    // Função para simular um pedido de teste
    const pedidoTeste = {
      id: 999,
      usuario_nome: 'Usuário Teste',
      status: 'em_andamento',
      dispositivo_nome: statusAgv?.nome || 'AGV Teste',
      dispositivo_codigo: statusAgv?.codigo || 'AGV001',
      itens: 'Prego,Pilha,Resistor,Filamento',
      corredores: '1,1,1,1',
      sub_corredores: '1,1,2,3',
      posicoes_x: '1,2,1,1'
    };
    
    setPedidoAtual(pedidoTeste);
    gerarRotaAtual(pedidoTeste);
  };

  const removerItemDaRota = async (itemIndex) => {
    if (!pedidoAtual || !rotaAtual[itemIndex]) return;

    if (!window.confirm(`Tem certeza que deseja remover "${rotaAtual[itemIndex].nome}" da rota?`)) return;

    setLoading(true);
    try {
      // Se é um pedido real, atualizar no backend
      if (!pedidoAtual.id.toString().startsWith('demo_')) {
        const response = await fetch(`http://localhost:5000/pedidos/${pedidoAtual.id}/remover-item`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            item_index: itemIndex,
            item_nome: rotaAtual[itemIndex].nome 
          })
        });

        const data = await response.json();
        if (!data.success) {
          alert('Erro ao remover item: ' + data.error);
          return;
        }
      }

      // Atualizar localmente
      const novaRota = rotaAtual.filter((_, index) => index !== itemIndex);
      setRotaAtual(novaRota);

      // Se não há mais itens, cancelar o pedido
      if (novaRota.length === 0) {
        await cancelarRotaCompleta();
      }

      alert('Item removido da rota com sucesso!');
    } catch (error) {
      alert('Erro ao remover item da rota');
    } finally {
      setLoading(false);
    }
  };

  const cancelarRotaCompleta = async () => {
    if (!pedidoAtual) return;

    if (!window.confirm('Tem certeza que deseja cancelar toda a rota? Itens já coletados serão removidos do armazém.')) return;

    setLoading(true);
    try {
      // Se é um pedido real, processar no backend
      if (!pedidoAtual.id.toString().startsWith('demo_')) {
        const response = await fetch(`http://localhost:5000/pedidos/${pedidoAtual.id}/cancelar-completo`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            itens_rota: rotaAtual.map(item => ({
              nome: item.nome,
              status: item.status,
              coletado: item.status === 'P'
            }))
          })
        });

        const data = await response.json();
        if (!data.success) {
          alert('Erro ao cancelar rota: ' + data.error);
          return;
        }
      }

      // Limpar estado local
      setPedidoAtual(null);
      setRotaAtual([]);

      alert('Rota cancelada com sucesso! Itens coletados foram removidos do armazém.');
      
      // Recarregar dados após um pequeno delay
      setTimeout(() => {
        carregarDados();
      }, 1000);
    } catch (error) {
      alert('Erro ao cancelar rota completa');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'P': return 'text-green-600 dark:text-green-400';
      case 'F': return 'text-red-600 dark:text-red-400';
      case 'N': return 'text-gray-600 dark:text-gray-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'P': return 'Pego';
      case 'F': return 'Não encontrado';
      case 'N': return 'Não pego ainda';
      default: return 'Desconhecido';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Cabeçalho */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Status do Sistema
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Acompanhe o status do AGV e pedidos em andamento
        </p>
      </div>

      {/* Seletor de AGV */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-4">
        <div className="flex items-center justify-center space-x-4">
          <label className="text-gray-700 dark:text-gray-300 font-medium">
            Selecionar AGV:
          </label>
          <select
            value={agvSelecionado}
            onChange={(e) => setAgvSelecionado(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white min-w-48 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Selecione um AGV</option>
            {agvs.map(agv => (
              <option key={agv.id} value={agv.id}>
                {agv.nome} ({agv.codigo}) - {agv.status}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Status do Sistema */}
      {agvSelecionado && statusAgv && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Status do AGV: {statusAgv.nome}
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Bateria */}
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Bateria</p>
                <div className="flex items-center space-x-2">
                  <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
                    <div 
                      className={`h-2 rounded-full ${
                        statusSistema.bateria > 50 ? 'bg-green-500' : 
                        statusSistema.bateria > 20 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${statusSistema.bateria}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {statusSistema.bateria}%
                  </span>
                </div>
              </div>
            </div>

            {/* Status do AGV */}
            <div className="flex items-center space-x-3">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                statusAgv.status === 'disponivel' ? 'bg-green-100 dark:bg-green-900/20' :
                statusAgv.status === 'ocupado' ? 'bg-yellow-100 dark:bg-yellow-900/20' :
                'bg-red-100 dark:bg-red-900/20'
              }`}>
                <svg className={`w-6 h-6 ${
                  statusAgv.status === 'disponivel' ? 'text-green-600 dark:text-green-400' :
                  statusAgv.status === 'ocupado' ? 'text-yellow-600 dark:text-yellow-400' :
                  'text-red-600 dark:text-red-400'
                }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
                <p className={`text-sm font-medium ${
                  statusAgv.status === 'disponivel' ? 'text-green-600 dark:text-green-400' :
                  statusAgv.status === 'ocupado' ? 'text-yellow-600 dark:text-yellow-400' :
                  'text-red-600 dark:text-red-400'
                }`}>
                  {statusAgv.status === 'disponivel' ? 'Disponível' :
                   statusAgv.status === 'ocupado' ? 'Em Operação' :
                   statusAgv.status === 'manutencao' ? 'Manutenção' : 'Offline'}
                </p>
              </div>
            </div>

            {/* Conexão */}
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Conexão</p>
                <p className={`text-sm font-medium ${
                  statusSistema.conexao === 'ok' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                }`}>
                  {statusSistema.conexao === 'ok' ? 'Online' : 'Offline'}
                </p>
              </div>
            </div>
          </div>

          {/* Informações adicionais do AGV */}
          <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
              <p className="text-gray-600 dark:text-gray-400">
                <span className="font-medium">Código:</span> {statusAgv.codigo}
              </p>
              <p className="text-gray-600 dark:text-gray-400">
                <span className="font-medium">Localização:</span> {statusAgv.localizacao || 'Base'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Rota Atual */}
      {!agvSelecionado ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">🤖</div>
            <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">
              Selecione um AGV para monitorar
            </p>
            <p className="text-gray-400 dark:text-gray-500 text-sm">
              Escolha um AGV na lista acima para ver seu status e pedidos
            </p>
          </div>
        </div>
      ) : pedidoAtual ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Rota Atual
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Pedido #{pedidoAtual.id} - {pedidoAtual.usuario_nome}
                {pedidoAtual.id.toString().startsWith('demo_') && (
                  <span className="ml-2 px-2 py-1 bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300 rounded text-xs">
                    DEMONSTRAÇÃO
                  </span>
                )}
              </p>
            </div>
            
            {usuario.perfil === 'gerente' && (
              <div className="flex gap-2">
                <button
                  onClick={cancelarRotaCompleta}
                  disabled={loading}
                  className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {loading ? 'Cancelando...' : 'Cancelar Rota Completa'}
                </button>
                
                {pedidoAtual && !pedidoAtual.id.toString().startsWith('demo_') && (
                  <button
                    onClick={cancelarPedido}
                    disabled={loading}
                    className="px-4 py-2 bg-orange-500 text-white text-sm rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    {loading ? 'Cancelando...' : 'Cancelar Pedido'}
                  </button>
                )}
              </div>
            )}
          </div>

          {rotaAtual.length > 0 ? (
            <div className="space-y-6">
              {/* Estatísticas da Rota */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {rotaAtual.length}
                  </div>
                  <div className="text-sm text-blue-600 dark:text-blue-400">Total de Itens</div>
                </div>
                
                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {rotaAtual.filter(item => item.status === 'P').length}
                  </div>
                  <div className="text-sm text-green-600 dark:text-green-400">Coletados</div>
                </div>
                
                <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                    {rotaAtual.filter(item => item.status === 'F').length}
                  </div>
                  <div className="text-sm text-red-600 dark:text-red-400">Não Encontrados</div>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                    {rotaAtual.filter(item => item.status === 'N').length}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Pendentes</div>
                </div>
              </div>

              {/* Tabela de Itens */}
              <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b-2 border-gray-200 dark:border-gray-600">
                    <th className="text-left py-4 px-4 font-semibold text-gray-900 dark:text-white">Item</th>
                    <th className="text-center py-4 px-4 font-semibold text-gray-900 dark:text-white">Corredor</th>
                    <th className="text-center py-4 px-4 font-semibold text-gray-900 dark:text-white">SubCorredor</th>
                    <th className="text-center py-4 px-4 font-semibold text-gray-900 dark:text-white">Status</th>
                    <th className="text-center py-4 px-4 font-semibold text-gray-900 dark:text-white"></th>
                  </tr>
                </thead>
                <tbody>
                  {rotaAtual.map((item, index) => (
                    <tr key={item.id} className={`border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 ${
                      item.status === 'P' ? 'bg-green-50 dark:bg-green-900/10' :
                      item.status === 'F' ? 'bg-red-50 dark:bg-red-900/10' :
                      'bg-white dark:bg-gray-800'
                    }`}>
                      <td className="py-4 px-4">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            item.status === 'P' ? 'bg-green-500' :
                            item.status === 'F' ? 'bg-red-500' :
                            'bg-gray-400'
                          }`}></div>
                          <span className={`font-medium ${
                            item.status === 'P' ? 'text-green-900 dark:text-green-100' :
                            item.status === 'F' ? 'text-red-900 dark:text-red-100' :
                            'text-gray-900 dark:text-white'
                          }`}>{item.nome}</span>
                          {item.status === 'P' && (
                            <span className="px-2 py-1 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded text-xs font-medium">
                              Coletado
                            </span>
                          )}
                          {item.status === 'F' && (
                            <span className="px-2 py-1 bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded text-xs font-medium">
                              Não encontrado
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="text-center py-4 px-4 text-gray-700 dark:text-gray-300 font-medium">{item.corredor}</td>
                      <td className="text-center py-4 px-4 text-gray-700 dark:text-gray-300 font-medium">{item.subCorredor}</td>
                      <td className="text-center py-4 px-4">
                        <span className={`font-bold text-lg ${getStatusColor(item.status)}`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="text-center py-4 px-4">
                        {usuario.perfil === 'gerente' ? (
                          <button 
                            onClick={() => removerItemDaRota(index)}
                            disabled={loading}
                            className="w-8 h-8 mx-auto rounded bg-red-500 hover:bg-red-600 disabled:opacity-50 flex items-center justify-center transition-colors"
                            title="Remover item da rota"
                          >
                            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        ) : (
                          <div className="w-8 h-8 mx-auto rounded bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                            <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-2">🚚</div>
              <p className="text-gray-500 dark:text-gray-400">Aguardando rota...</p>
            </div>
          )}

          {/* Legenda */}
          <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Legenda:</p>
            <div className="flex flex-wrap gap-4 text-xs">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                <span className="text-gray-700 dark:text-gray-300">P - Pego</span>
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                <span className="text-gray-700 dark:text-gray-300">F - Não encontrado</span>
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full"></span>
                <span className="text-gray-700 dark:text-gray-300">N - Não pego ainda</span>
              </span>
            </div>
          </div>

          {/* Informação do dispositivo */}
          {pedidoAtual.dispositivo_nome && (
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                <span className="font-medium">Dispositivo:</span> {pedidoAtual.dispositivo_nome} ({pedidoAtual.dispositivo_codigo})
              </p>
            </div>
          )}
        </div>
      ) : (
        /* Nenhuma rota ativa para o AGV selecionado */
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Rota Atual - {statusAgv?.nome}
          </h3>
          
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">🚛</div>
            <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">
              Nenhum pedido em andamento
            </p>
            <p className="text-gray-400 dark:text-gray-500 text-sm mb-4">
              Este AGV está aguardando novos pedidos
            </p>
            
            {/* Botão para simular pedido de teste */}
            <button
              onClick={simularPedidoTeste}
              className="px-4 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
            >
              Simular Pedido de Teste
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
