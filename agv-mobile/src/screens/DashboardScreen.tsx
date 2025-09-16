import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Title, Paragraph, Button, Avatar } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface DashboardScreenProps {
  navigation: any;
}

const DashboardScreen: React.FC<DashboardScreenProps> = ({ navigation }) => {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const userData = await AsyncStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
      }
    } catch (error) {
      console.error('Error loading user:', error);
    }
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem('user');
    navigation.replace('Login');
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Avatar.Text
          size={60}
          label={user?.nome?.charAt(0)?.toUpperCase() || 'U'}
          style={styles.avatar}
        />
        <View style={styles.userInfo}>
          <Title style={styles.welcomeText}>Bem-vindo,</Title>
          <Title style={styles.userName}>{user?.nome || 'Usuário'}</Title>
          <Paragraph style={styles.userRole}>
            {user?.perfil === 'gerente' ? 'Gerente' : 'Funcionário'}
          </Paragraph>
        </View>
      </View>

      {/* Quick Actions */}
      <View style={styles.actionsContainer}>
        <Card style={styles.actionCard}>
          <Card.Content>
            <Title style={styles.cardTitle}>📦 Novo Pedido</Title>
            <Paragraph>Criar um novo pedido de coleta</Paragraph>
            <Button
              mode="contained"
              onPress={() => navigation.navigate('Orders')}
              style={styles.actionButton}
            >
              Criar Pedido
            </Button>
          </Card.Content>
        </Card>

        <Card style={styles.actionCard}>
          <Card.Content>
            <Title style={styles.cardTitle}>📊 Status AGV</Title>
            <Paragraph>Monitorar status dos robôs</Paragraph>
            <Button
              mode="contained"
              onPress={() => navigation.navigate('Status')}
              style={styles.actionButton}
            >
              Ver Status
            </Button>
          </Card.Content>
        </Card>

        <Card style={styles.actionCard}>
          <Card.Content>
            <Title style={styles.cardTitle}>📱 Scanner QR Code</Title>
            <Paragraph>Escanear códigos de itens</Paragraph>
            <Button
              mode="contained"
              onPress={() => navigation.navigate('QRScanner')}
              style={styles.actionButton}
            >
              Abrir Scanner
            </Button>
          </Card.Content>
        </Card>
      </View>

      {/* System Status */}
      <Card style={styles.statusCard}>
        <Card.Content>
          <Title style={styles.statusTitle}>🔋 Status do Sistema</Title>
          <View style={styles.statusGrid}>
            <View style={styles.statusItem}>
              <Paragraph style={styles.statusLabel}>AGVs Ativos</Paragraph>
              <Title style={styles.statusValue}>2</Title>
            </View>
            <View style={styles.statusItem}>
              <Paragraph style={styles.statusLabel}>Pedidos Hoje</Paragraph>
              <Title style={styles.statusValue}>15</Title>
            </View>
            <View style={styles.statusItem}>
              <Paragraph style={styles.statusLabel}>Itens Coletados</Paragraph>
              <Title style={styles.statusValue}>127</Title>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Logout Button */}
      <View style={styles.logoutContainer}>
        <Button
          mode="outlined"
          onPress={handleLogout}
          style={styles.logoutButton}
          textColor="#dc2626"
        >
          Sair
        </Button>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#2563eb',
  },
  avatar: {
    backgroundColor: '#ffffff',
  },
  userInfo: {
    marginLeft: 15,
    flex: 1,
  },
  welcomeText: {
    fontSize: 16,
    color: '#ffffff',
    opacity: 0.9,
  },
  userName: {
    fontSize: 24,
    color: '#ffffff',
    marginBottom: 4,
  },
  userRole: {
    fontSize: 14,
    color: '#ffffff',
    opacity: 0.8,
  },
  actionsContainer: {
    padding: 20,
  },
  actionCard: {
    marginBottom: 15,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    marginBottom: 8,
  },
  actionButton: {
    marginTop: 10,
  },
  statusCard: {
    margin: 20,
    marginTop: 0,
    elevation: 3,
  },
  statusTitle: {
    textAlign: 'center',
    marginBottom: 20,
  },
  statusGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statusItem: {
    alignItems: 'center',
  },
  statusLabel: {
    fontSize: 12,
    color: '#64748b',
    marginBottom: 5,
  },
  statusValue: {
    fontSize: 24,
    color: '#2563eb',
    fontWeight: 'bold',
  },
  logoutContainer: {
    padding: 20,
    paddingTop: 0,
  },
  logoutButton: {
    borderColor: '#dc2626',
  },
});

export default DashboardScreen;