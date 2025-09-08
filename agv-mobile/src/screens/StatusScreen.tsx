import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, FlatList } from 'react-native';
import { Card, Title, Paragraph, Chip, ProgressBar } from 'react-native-paper';

interface StatusScreenProps {
  navigation: any;
}

interface Device {
  id: number;
  nome: string;
  codigo: string;
  status: string;
  bateria: number;
  localizacao: string;
}

interface Order {
  id: number;
  usuario_nome: string;
  status: string;
  created_at: string;
  itens: string;
  dispositivo_nome: string;
  dispositivo_id: number;
}

const StatusScreen: React.FC<StatusScreenProps> = ({ navigation }) => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load devices
      // const devicesResponse = await fetch('http://10.0.2.2:5000/dispositivos'); // For Android emulator
      // const devicesResponse = await fetch('http://localhost:5000/dispositivos'); // For iOS simulator
      const devicesResponse = await fetch('http://192.168.0.134:5000/dispositivos'); // For physical device (your PC IP)
      const devicesData = await devicesResponse.json();
      setDevices(devicesData);

      // Load orders
      // const ordersResponse = await fetch('http://10.0.2.2:5000/pedidos'); // For Android emulator
      // const ordersResponse = await fetch('http://localhost:5000/pedidos'); // For iOS simulator
      const ordersResponse = await fetch('http://192.168.0.134:5000/pedidos'); // For physical device (your PC IP)
      const ordersData = await ordersResponse.json();
      setOrders(ordersData);

      // Auto-select first device if available
      if (devicesData.length > 0 && !selectedDevice) {
        setSelectedDevice(devicesData[0].id);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDeviceStatusColor = (status: string) => {
    switch (status) {
      case 'disponivel': return '#16a34a';
      case 'ocupado': return '#2563eb';
      case 'manutencao': return '#dc2626';
      default: return '#64748b';
    }
  };

  const getDeviceStatusText = (status: string) => {
    switch (status) {
      case 'disponivel': return 'Disponível';
      case 'ocupado': return 'Em Operação';
      case 'manutencao': return 'Manutenção';
      default: return 'Offline';
    }
  };

  const getOrderStatusColor = (status: string) => {
    switch (status) {
      case 'pendente': return '#f59e0b';
      case 'em_andamento': return '#2563eb';
      case 'coletando': return '#7c3aed';
      case 'concluido': return '#16a34a';
      case 'cancelado': return '#dc2626';
      default: return '#64748b';
    }
  };

  const getOrderStatusText = (status: string) => {
    switch (status) {
      case 'pendente': return 'Pendente';
      case 'em_andamento': return 'Em Andamento';
      case 'coletando': return 'Coletando';
      case 'concluido': return 'Concluído';
      case 'cancelado': return 'Cancelado';
      default: return status;
    }
  };

  const getBatteryColor = (battery: number) => {
    if (battery > 50) return '#16a34a';
    if (battery > 20) return '#f59e0b';
    return '#dc2626';
  };

  const selectedDeviceData = devices.find(d => d.id === selectedDevice);
  const deviceOrders = orders.filter(order => order.dispositivo_id === selectedDevice);

  const renderDeviceCard = ({ item }: { item: Device }) => (
    <Card
      style={[
        styles.deviceCard,
        selectedDevice === item.id && styles.selectedDeviceCard
      ]}
      onPress={() => setSelectedDevice(item.id)}
    >
      <Card.Content>
        <View style={styles.deviceHeader}>
          <Title style={styles.deviceName}>{item.nome}</Title>
          <Chip
            style={[styles.statusChip, { backgroundColor: getDeviceStatusColor(item.status) }]}
            textStyle={styles.statusText}
          >
            {getDeviceStatusText(item.status)}
          </Chip>
        </View>

        <Paragraph style={styles.deviceCode}>Código: {item.codigo}</Paragraph>

        {/* Battery */}
        <View style={styles.batteryContainer}>
          <View style={styles.batteryLabel}>
            <Paragraph style={styles.batteryText}>🔋 Bateria</Paragraph>
            <Paragraph style={styles.batteryPercent}>{item.bateria}%</Paragraph>
          </View>
          <ProgressBar
            progress={item.bateria / 100}
            color={getBatteryColor(item.bateria)}
            style={styles.batteryBar}
          />
        </View>

        <Paragraph style={styles.deviceLocation}>
          📍 Localização: {item.localizacao || 'Base'}
        </Paragraph>
      </Card.Content>
    </Card>
  );

  const renderOrderCard = ({ item }: { item: Order }) => (
    <Card style={styles.orderCard}>
      <Card.Content>
        <View style={styles.orderHeader}>
          <Title style={styles.orderTitle}>Pedido #{item.id}</Title>
          <Chip
            style={[styles.orderStatusChip, { backgroundColor: getOrderStatusColor(item.status) }]}
            textStyle={styles.statusText}
          >
            {getOrderStatusText(item.status)}
          </Chip>
        </View>

        <Paragraph style={styles.orderUser}>👤 {item.usuario_nome}</Paragraph>
        <Paragraph style={styles.orderItems}>
          📦 Itens: {item.itens?.split(',').length || 0}
        </Paragraph>
        <Paragraph style={styles.orderDate}>
          📅 {new Date(item.created_at).toLocaleDateString('pt-BR')} às {new Date(item.created_at).toLocaleTimeString('pt-BR')}
        </Paragraph>
      </Card.Content>
    </Card>
  );

  return (
    <ScrollView style={styles.container}>
      {/* Device Selection */}
      <Card style={styles.sectionCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>Selecionar AGV</Title>
          <FlatList
            data={devices}
            renderItem={renderDeviceCard}
            keyExtractor={item => item.id.toString()}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.devicesList}
          />
        </Card.Content>
      </Card>

      {/* Selected Device Details */}
      {selectedDeviceData && (
        <Card style={styles.sectionCard}>
          <Card.Content>
            <Title style={styles.sectionTitle}>
              Status do {selectedDeviceData.nome}
            </Title>

            <View style={styles.deviceDetails}>
              <View style={styles.detailRow}>
                <Paragraph style={styles.detailLabel}>Status:</Paragraph>
                <Chip
                  style={[styles.detailChip, { backgroundColor: getDeviceStatusColor(selectedDeviceData.status) }]}
                  textStyle={styles.statusText}
                >
                  {getDeviceStatusText(selectedDeviceData.status)}
                </Chip>
              </View>

              <View style={styles.detailRow}>
                <Paragraph style={styles.detailLabel}>Bateria:</Paragraph>
                <View style={styles.batteryDetail}>
                  <ProgressBar
                    progress={selectedDeviceData.bateria / 100}
                    color={getBatteryColor(selectedDeviceData.bateria)}
                    style={styles.detailBatteryBar}
                  />
                  <Paragraph style={styles.batteryPercentText}>
                    {selectedDeviceData.bateria}%
                  </Paragraph>
                </View>
              </View>

              <View style={styles.detailRow}>
                <Paragraph style={styles.detailLabel}>Localização:</Paragraph>
                <Paragraph style={styles.detailValue}>
                  {selectedDeviceData.localizacao || 'Base'}
                </Paragraph>
              </View>
            </View>
          </Card.Content>
        </Card>
      )}

      {/* Orders for Selected Device */}
      <Card style={styles.sectionCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>
            Pedidos do {selectedDeviceData?.nome || 'AGV'}
          </Title>

          {deviceOrders.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Paragraph style={styles.emptyText}>
                Nenhum pedido ativo para este AGV
              </Paragraph>
            </View>
          ) : (
            <FlatList
              data={deviceOrders}
              renderItem={renderOrderCard}
              keyExtractor={item => item.id.toString()}
              scrollEnabled={false}
            />
          )}
        </Card.Content>
      </Card>

      {/* System Statistics */}
      <Card style={styles.sectionCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>Estatísticas do Sistema</Title>

          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Title style={styles.statValue}>{devices.length}</Title>
              <Paragraph style={styles.statLabel}>AGVs Totais</Paragraph>
            </View>

            <View style={styles.statItem}>
              <Title style={styles.statValue}>
                {devices.filter(d => d.status === 'disponivel').length}
              </Title>
              <Paragraph style={styles.statLabel}>Disponíveis</Paragraph>
            </View>

            <View style={styles.statItem}>
              <Title style={styles.statValue}>
                {orders.filter(o => o.status === 'em_andamento').length}
              </Title>
              <Paragraph style={styles.statLabel}>Em Andamento</Paragraph>
            </View>

            <View style={styles.statItem}>
              <Title style={styles.statValue}>
                {orders.filter(o => o.status === 'concluido').length}
              </Title>
              <Paragraph style={styles.statLabel}>Concluídos Hoje</Paragraph>
            </View>
          </View>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  sectionCard: {
    margin: 15,
    marginBottom: 0,
    elevation: 3,
  },
  sectionTitle: {
    marginBottom: 15,
  },
  devicesList: {
    paddingVertical: 10,
  },
  deviceCard: {
    width: 280,
    marginRight: 15,
    elevation: 3,
  },
  selectedDeviceCard: {
    borderColor: '#2563eb',
    borderWidth: 2,
  },
  deviceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  deviceName: {
    fontSize: 18,
  },
  statusChip: {
    height: 28,
  },
  statusText: {
    color: 'white',
    fontSize: 12,
  },
  deviceCode: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 15,
  },
  batteryContainer: {
    marginBottom: 15,
  },
  batteryLabel: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 5,
  },
  batteryText: {
    fontSize: 14,
  },
  batteryPercent: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  batteryBar: {
    height: 8,
    borderRadius: 4,
  },
  deviceLocation: {
    fontSize: 14,
    color: '#64748b',
  },
  deviceDetails: {
    marginTop: 10,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  detailLabel: {
    fontSize: 16,
    fontWeight: '500',
  },
  detailValue: {
    fontSize: 16,
    color: '#64748b',
  },
  detailChip: {
    height: 32,
  },
  batteryDetail: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginLeft: 10,
  },
  detailBatteryBar: {
    flex: 1,
    height: 10,
    borderRadius: 5,
    marginRight: 10,
  },
  batteryPercentText: {
    fontSize: 14,
    fontWeight: 'bold',
    minWidth: 35,
  },
  orderCard: {
    marginBottom: 10,
    elevation: 2,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  orderTitle: {
    fontSize: 16,
  },
  orderStatusChip: {
    height: 28,
  },
  orderUser: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 5,
  },
  orderItems: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 5,
  },
  orderDate: {
    fontSize: 12,
    color: '#94a3b8',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 30,
  },
  emptyText: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statItem: {
    alignItems: 'center',
    width: '48%',
    marginBottom: 20,
  },
  statValue: {
    fontSize: 32,
    color: '#2563eb',
    fontWeight: 'bold',
  },
  statLabel: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'center',
  },
});

export default StatusScreen;