import React, { useState, useEffect } from 'react';
import socketService from '../services/socketService';

export default function Analise({ usuario }) {
  const [analyticsData, setAnalyticsData] = useState({
    totalOrders: 0,
    completedOrders: 0,
    activeOrders: 0,
    avgOrderTime: 0,
    agvPerformance: [],
    warehouseUtilization: 0,
    systemEfficiency: 0,
    recentActivity: []
  });
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24h'); // 24h, 7d, 30d

  useEffect(() => {
    loadAnalyticsData();

    // Set up real-time updates
    const handleSystemStatus = (data) => {
      updateAnalyticsFromRealtime(data);
    };

    socketService.addEventListener('system_status', handleSystemStatus);

    return () => {
      socketService.removeEventListener('system_status', handleSystemStatus);
    };
  }, [timeRange]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);

      // Load orders data
      const ordersResponse = await fetch('http://localhost:5000/pedidos');
      const ordersData = await ordersResponse.json();

      // Load devices data
      const devicesResponse = await fetch('http://localhost:5000/dispositivos');
      const devicesData = await devicesResponse.json();

      // Load warehouse data
      const warehouseResponse = await fetch('http://localhost:5000/armazem/itens');
      const warehouseData = await warehouseResponse.json();

      // Process analytics
      const processedData = processAnalyticsData(ordersData, devicesData, warehouseData);
      setAnalyticsData(processedData);

    } catch (error) {
      console.error('Erro ao carregar dados analíticos:', error);
    } finally {
      setLoading(false);
    }
  };

  const processAnalyticsData = (orders, devices, warehouse) => {
    const now = new Date();
    const timeRangeMs = getTimeRangeMs(timeRange);

    // Filter orders by time range
    const filteredOrders = orders.filter(order => {
      const orderDate = new Date(order.created_at);
      return (now - orderDate) <= timeRangeMs;
    });

    // Calculate order statistics
    const totalOrders = filteredOrders.length;
    const completedOrders = filteredOrders.filter(o => o.status === 'concluido').length;
    const activeOrders = filteredOrders.filter(o =>
      ['pendente', 'em_andamento', 'coletando'].includes(o.status)
    ).length;

    // Calculate average order completion time
    const completedOrderTimes = filteredOrders
      .filter(o => o.status === 'concluido')
      .map(o => {
        const created = new Date(o.created_at);
        const nowDate = new Date();
        return (nowDate - created) / (1000 * 60); // minutes
      });

    const avgOrderTime = completedOrderTimes.length > 0
      ? completedOrderTimes.reduce((a, b) => a + b, 0) / completedOrderTimes.length
      : 0;

    // Calculate AGV performance
    const agvPerformance = devices.map(device => {
      const deviceOrders = filteredOrders.filter(o => o.dispositivo_id == device.id);
      const completedDeviceOrders = deviceOrders.filter(o => o.status === 'concluido').length;
      const efficiency = deviceOrders.length > 0 ? (completedDeviceOrders / deviceOrders.length) * 100 : 0;

      return {
        id: device.id,
        name: device.nome,
        totalOrders: deviceOrders.length,
        completedOrders: completedDeviceOrders,
        efficiency: efficiency,
        batteryLevel: device.bateria,
        status: device.status
      };
    });

    // Calculate warehouse utilization
    // Fixed warehouse layout: 1 corredor × 3 sub-corredores × 4 posições = 12 posições totais
    const TOTAL_WAREHOUSE_POSITIONS = 12;
    const occupiedPositions = warehouse.length; // Number of items that exist in warehouse
    const warehouseUtilization = (occupiedPositions / TOTAL_WAREHOUSE_POSITIONS) * 100;
    const vacantPositions = TOTAL_WAREHOUSE_POSITIONS - occupiedPositions;

    // Calculate system efficiency
    const systemEfficiency = totalOrders > 0 ? (completedOrders / totalOrders) * 100 : 0;

    // Get recent activity
    const recentActivity = filteredOrders
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 10)
      .map(order => ({
        id: order.id,
        type: 'order',
        description: `Pedido ${order.id} - ${order.usuario_nome}`,
        status: order.status,
        timestamp: order.created_at
      }));

    return {
      totalOrders,
      completedOrders,
      activeOrders,
      avgOrderTime: Math.round(avgOrderTime),
      agvPerformance,
      warehouseUtilization: Math.round(warehouseUtilization),
      warehouseOccupied: occupiedPositions,
      warehouseVacant: vacantPositions,
      systemEfficiency: Math.round(systemEfficiency),
      recentActivity
    };
  };

  const updateAnalyticsFromRealtime = (data) => {
    // Update real-time metrics from WebSocket data
    if (data.devices && data.active_orders) {
      const activeOrders = data.active_orders.length;
      const totalDevices = data.devices.length;
      const operationalDevices = data.devices.filter(d => d.status === 'disponivel' || d.status === 'ocupado').length;

      setAnalyticsData(prev => ({
        ...prev,
        activeOrders,
        systemEfficiency: totalDevices > 0 ? (operationalDevices / totalDevices) * 100 : prev.systemEfficiency
      }));
    }
  };

  const getTimeRangeMs = (range) => {
    const hour = 60 * 60 * 1000;
    const day = 24 * hour;

    switch (range) {
      case '24h': return day;
      case '7d': return 7 * day;
      case '30d': return 30 * day;
      default: return day;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'concluido': return 'text-green-600';
      case 'em_andamento': return 'text-blue-600';
      case 'coletando': return 'text-yellow-600';
      case 'pendente': return 'text-gray-600';
      case 'cancelado': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = (status) => {
    const statusMap = {
      'concluido': 'Concluído',
      'em_andamento': 'Em Andamento',
      'coletando': 'Coletando',
      'pendente': 'Pendente',
      'cancelado': 'Cancelado'
    };
    return statusMap[status] || status;
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Carregando dados analíticos...</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Análise e Relatórios
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Métricas de performance e eficiência do sistema AGV
          </p>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center space-x-2">
          <label className="text-gray-700 dark:text-gray-300 font-medium">
            Período:
          </label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="24h">Últimas 24 horas</option>
            <option value="7d">Últimos 7 dias</option>
            <option value="30d">Últimos 30 dias</option>
          </select>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Orders */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total de Pedidos</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {analyticsData.totalOrders}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Completed Orders */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Pedidos Concluídos</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {analyticsData.completedOrders}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Active Orders */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Pedidos Ativos</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {analyticsData.activeOrders}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </div>

        {/* System Efficiency */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Eficiência do Sistema</p>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {analyticsData.systemEfficiency}%
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AGV Performance */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Performance dos AGVs
          </h3>

          <div className="space-y-4">
            {analyticsData.agvPerformance.map(agv => (
              <div key={agv.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {agv.name}
                    </h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      agv.status === 'disponivel' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' :
                      agv.status === 'ocupado' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400' :
                      'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                    }`}>
                      {agv.status === 'disponivel' ? 'Disponível' :
                       agv.status === 'ocupado' ? 'Em Operação' : 'Manutenção'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600 dark:text-gray-400">Pedidos Totais</p>
                      <p className="font-medium text-gray-900 dark:text-white">{agv.totalOrders}</p>
                    </div>
                    <div>
                      <p className="text-gray-600 dark:text-gray-400">Eficiência</p>
                      <p className="font-medium text-gray-900 dark:text-white">{Math.round(agv.efficiency)}%</p>
                    </div>
                  </div>

                  <div className="mt-2">
                    <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                      <span>Bateria</span>
                      <span>{agv.batteryLevel}%</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          agv.batteryLevel > 50 ? 'bg-green-500' :
                          agv.batteryLevel > 20 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${agv.batteryLevel}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {analyticsData.agvPerformance.length === 0 && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                Nenhum AGV cadastrado
              </div>
            )}
          </div>
        </div>

        {/* Warehouse Utilization */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Utilização do Armazém
          </h3>

          <div className="space-y-6">
            <div className="text-center">
              <div className="relative w-32 h-32 mx-auto mb-4">
                <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeDasharray={`${analyticsData.warehouseUtilization}, 100`}
                    className="text-gray-200 dark:text-gray-600"
                  />
                  <path
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeDasharray={`${analyticsData.warehouseUtilization}, 100`}
                    className="text-blue-500"
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold text-gray-900 dark:text-white">
                    {analyticsData.warehouseUtilization}%
                  </span>
                </div>
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                Posições ocupadas
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 text-center">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {analyticsData.warehouseOccupied}
                </p>
                <p className="text-sm text-green-600 dark:text-green-400">
                  Itens Cadastrados
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                  {analyticsData.warehouseVacant}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Posições Vazias
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Atividade Recente
        </h3>

        <div className="space-y-3">
          {analyticsData.recentActivity.map(activity => (
            <div key={activity.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`w-2 h-2 rounded-full ${
                  activity.status === 'concluido' ? 'bg-green-500' :
                  activity.status === 'em_andamento' ? 'bg-blue-500' :
                  activity.status === 'coletando' ? 'bg-yellow-500' :
                  'bg-gray-500'
                }`}></div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {activity.description}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {new Date(activity.timestamp).toLocaleString('pt-BR')}
                  </p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(activity.status)}`}>
                {getStatusText(activity.status)}
              </span>
            </div>
          ))}

          {analyticsData.recentActivity.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              Nenhuma atividade recente no período selecionado
            </div>
          )}
        </div>
      </div>
    </div>
  );
}