import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, FlatList, Alert } from 'react-native';
import { Card, Title, Paragraph, Button, Chip, FAB } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface OrderScreenProps {
  navigation: any;
  route: any;
}

interface Item {
  id: number;
  nome: string;
  tag: string;
  categoria: string;
}

interface Order {
  id: number;
  usuario_nome: string;
  status: string;
  created_at: string;
  itens: string;
  dispositivo_nome: string;
}

const OrderScreen: React.FC<OrderScreenProps> = ({ navigation, route }) => {
  const [items, setItems] = useState<Item[]>([]);
  const [selectedItems, setSelectedItems] = useState<Item[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();

    // Verificar se há um item para adicionar (vindo do QR Scanner)
    const itemParaAdicionar = route.params?.itemParaAdicionar;
    if (itemParaAdicionar) {
      adicionarItemDoQR(itemParaAdicionar);
    }
  }, [route.params]);

  const loadData = async () => {
    try {
      // Load items
      // const itemsResponse = await fetch('http://10.0.2.2:5000/itens'); // For Android emulator
      // const itemsResponse = await fetch('http://localhost:5000/itens'); // For iOS simulator
      const itemsResponse = await fetch('http://192.168.0.134:5000/itens'); // For physical device (your PC IP)
      const itemsData = await itemsResponse.json();
      setItems(itemsData);

      // Load available devices
      // const devicesResponse = await fetch('http://10.0.2.2:5000/dispositivos/disponiveis'); // For Android emulator
      // const devicesResponse = await fetch('http://localhost:5000/dispositivos/disponiveis'); // For iOS simulator
      const devicesResponse = await fetch('http://192.168.0.134:5000/dispositivos/disponiveis'); // For physical device (your PC IP)
      const devicesData = await devicesResponse.json();
      setDevices(devicesData);

      // Load orders
      // const ordersResponse = await fetch('http://10.0.2.2:5000/pedidos'); // For Android emulator
      // const ordersResponse = await fetch('http://localhost:5000/pedidos'); // For iOS simulator
      const ordersResponse = await fetch('http://192.168.0.134:5000/pedidos'); // For physical device (your PC IP)
      const ordersData = await ordersResponse.json();
      setOrders(ordersData);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const adicionarItemDoQR = (item: Item) => {
    // Verificar se o item já foi selecionado
    const jaSelecionado = selectedItems.find(i => i.id === item.id);
    if (jaSelecionado) {
      Alert.alert('Atenção', 'Este item já foi adicionado ao pedido!');
      return;
    }

    // Verificar limite de itens
    if (selectedItems.length >= 4) {
      Alert.alert('Limite Atingido', 'Máximo de 4 itens por pedido!');
      return;
    }

    // Adicionar item à lista selecionada
    setSelectedItems([...selectedItems, item]);

    // Mostrar confirmação
    Alert.alert('Item Adicionado!', `${item.nome} foi adicionado ao seu pedido.`);
  };

  const toggleItemSelection = (item: Item) => {
    setSelectedItems(prev => {
      const isSelected = prev.find(i => i.id === item.id);
      if (isSelected) {
        return prev.filter(i => i.id !== item.id);
      } else if (prev.length < 4) {
        return [...prev, item];
      }
      return prev;
    });
  };

  const createOrder = async () => {
    if (selectedItems.length === 0) {
      alert('Selecione pelo menos um item');
      return;
    }

    if (!selectedDevice) {
      alert('Selecione um dispositivo');
      return;
    }

    setLoading(true);

    try {
      const userData = await AsyncStorage.getItem('user');
      const user = JSON.parse(userData || '{}');

      // const response = await fetch('http://10.0.2.2:5000/pedidos', { // For Android emulator
      // const response = await fetch('http://localhost:5000/pedidos', { // For iOS simulator
      const response = await fetch('http://192.168.0.134:5000/pedidos', { // For physical device (your PC IP)
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          usuario_id: user.id,
          itens: selectedItems.map(item => item.id),
          dispositivo_id: selectedDevice,
        }),
      });

      const data = await response.json();

      if (data.success) {
        alert('Pedido criado com sucesso!');
        setSelectedItems([]);
        setSelectedDevice(null);
        loadData(); // Refresh data
      } else {
        alert('Erro ao criar pedido: ' + data.error);
      }
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Erro ao criar pedido');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pendente': return '#f59e0b';
      case 'em_andamento': return '#2563eb';
      case 'coletando': return '#7c3aed';
      case 'concluido': return '#16a34a';
      case 'cancelado': return '#dc2626';
      default: return '#64748b';
    }
  };

  const renderItem = ({ item }: { item: Item }) => {
    const isSelected = selectedItems.find(i => i.id === item.id);

    return (
      <Card
        style={[styles.itemCard, isSelected && styles.selectedItemCard]}
        onPress={() => toggleItemSelection(item)}
      >
        <Card.Content style={styles.itemContent}>
          <View style={styles.itemInfo}>
            <Title style={styles.itemName}>{item.nome}</Title>
            <Paragraph style={styles.itemTag}>Tag: {item.tag}</Paragraph>
            <Paragraph style={styles.itemCategory}>{item.categoria}</Paragraph>
          </View>
          {isSelected && (
            <View style={styles.checkmark}>
              <Title style={styles.checkmarkText}>✓</Title>
            </View>
          )}
        </Card.Content>
      </Card>
    );
  };

  const renderOrder = ({ item }: { item: Order }) => (
    <Card style={styles.orderCard}>
      <Card.Content>
        <View style={styles.orderHeader}>
          <Title style={styles.orderTitle}>Pedido #{item.id}</Title>
          <Chip
            style={[styles.statusChip, { backgroundColor: getStatusColor(item.status) }]}
            textStyle={styles.statusText}
          >
            {item.status}
          </Chip>
        </View>
        <Paragraph style={styles.orderUser}>{item.usuario_nome}</Paragraph>
        <Paragraph style={styles.orderDevice}>{item.dispositivo_nome}</Paragraph>
        <Paragraph style={styles.orderItems}>
          Itens: {item.itens?.split(',').length || 0}
        </Paragraph>
        <Paragraph style={styles.orderDate}>
          {new Date(item.created_at).toLocaleDateString('pt-BR')}
        </Paragraph>
      </Card.Content>
    </Card>
  );

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollContainer}>
        {/* Device Selection */}
        <Card style={styles.sectionCard}>
          <Card.Content>
            <Title style={styles.sectionTitle}>Selecionar Dispositivo</Title>
            <View style={styles.devicesContainer}>
              {devices.map(device => (
                <Button
                  key={device.id}
                  mode={selectedDevice === device.id ? 'contained' : 'outlined'}
                  onPress={() => setSelectedDevice(device.id)}
                  style={styles.deviceButton}
                >
                  {device.nome} (🔋{device.bateria}%)
                </Button>
              ))}
            </View>
          </Card.Content>
        </Card>

        {/* Selected Items */}
        {selectedItems.length > 0 && (
          <Card style={styles.sectionCard}>
            <Card.Content>
              <Title style={styles.sectionTitle}>
                Itens Selecionados ({selectedItems.length}/4)
              </Title>
              <View style={styles.selectedItemsContainer}>
                {selectedItems.map(item => (
                  <Chip
                    key={item.id}
                    style={styles.selectedItemChip}
                    onClose={() => toggleItemSelection(item)}
                  >
                    {item.nome}
                  </Chip>
                ))}
              </View>
            </Card.Content>
          </Card>
        )}

        {/* Create Order Button */}
        <View style={styles.actionContainer}>
          <Button
            mode="contained"
            onPress={createOrder}
            loading={loading}
            disabled={loading || selectedItems.length === 0 || !selectedDevice}
            style={styles.createOrderButton}
          >
            {loading ? 'Criando...' : 'Criar Pedido'}
          </Button>
        </View>

        {/* Recent Orders */}
        <Card style={styles.sectionCard}>
          <Card.Content>
            <Title style={styles.sectionTitle}>Pedidos Recentes</Title>
            <FlatList
              data={orders.slice(0, 5)}
              renderItem={renderOrder}
              keyExtractor={item => item.id.toString()}
              scrollEnabled={false}
            />
          </Card.Content>
        </Card>
      </ScrollView>

      {/* Items Selection FAB */}
      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => {/* Navigate to item selection */}}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollContainer: {
    flex: 1,
    padding: 15,
  },
  sectionCard: {
    marginBottom: 15,
    elevation: 3,
  },
  sectionTitle: {
    marginBottom: 15,
  },
  devicesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  deviceButton: {
    marginRight: 10,
    marginBottom: 10,
  },
  selectedItemsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  selectedItemChip: {
    backgroundColor: '#dbeafe',
  },
  actionContainer: {
    marginBottom: 15,
  },
  createOrderButton: {
    paddingVertical: 8,
  },
  itemCard: {
    marginBottom: 10,
    elevation: 2,
  },
  selectedItemCard: {
    backgroundColor: '#dbeafe',
    borderColor: '#2563eb',
    borderWidth: 2,
  },
  itemContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
  },
  itemTag: {
    fontSize: 12,
    color: '#64748b',
  },
  itemCategory: {
    fontSize: 12,
    color: '#64748b',
  },
  checkmark: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#16a34a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkmarkText: {
    color: 'white',
    fontSize: 16,
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
  statusChip: {
    height: 28,
  },
  statusText: {
    color: 'white',
    fontSize: 12,
  },
  orderUser: {
    fontSize: 14,
    color: '#64748b',
  },
  orderDevice: {
    fontSize: 14,
    color: '#64748b',
  },
  orderItems: {
    fontSize: 14,
    color: '#64748b',
  },
  orderDate: {
    fontSize: 12,
    color: '#94a3b8',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#2563eb',
  },
});

export default OrderScreen;