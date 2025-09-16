import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import {
  TextInput,
  Button,
  Card,
  Title,
  Paragraph,
  ActivityIndicator,
} from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface LoginScreenProps {
  navigation: any;
}

const LoginScreen: React.FC<LoginScreenProps> = ({ navigation }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('Erro', 'Por favor, preencha todos os campos');
      return;
    }

    setLoading(true);

    try {
      // const response = await fetch('http://10.0.2.2:5000/login', { // For Android emulator
      // const response = await fetch('http://localhost:5000/login', { // For iOS simulator
      const response = await fetch('http://192.168.0.134:5000/login', { // For physical device (your PC IP)
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username.trim(),
          password: password.trim(),
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Save user data to AsyncStorage
        await AsyncStorage.setItem('user', JSON.stringify(data.usuario));

        // Navigate to Dashboard
        navigation.replace('Dashboard');
      } else {
        Alert.alert('Erro de Login', data.message || 'Credenciais inválidas');
      }
    } catch (error) {
      console.error('Login error:', error);
      Alert.alert(
        'Erro de Conexão',
        'Não foi possível conectar ao servidor. Verifique sua conexão com a internet.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        {/* Logo/Title Section */}
        <View style={styles.logoContainer}>
          <View style={styles.logoBox}>
            <Title style={styles.logoText}>MAC</Title>
          </View>
          <Title style={styles.appTitle}>AGV MOBILE</Title>
          <Paragraph style={styles.subtitle}>
            Sistema de Controle de Robô AGV
          </Paragraph>
        </View>

        {/* Login Form */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Login</Title>

            <TextInput
              label="Usuário"
              value={username}
              onChangeText={setUsername}
              mode="outlined"
              style={styles.input}
              autoCapitalize="none"
              autoCorrect={false}
            />

            <TextInput
              label="Senha"
              value={password}
              onChangeText={setPassword}
              mode="outlined"
              style={styles.input}
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
            />

            <Button
              mode="contained"
              onPress={handleLogin}
              style={styles.loginButton}
              loading={loading}
              disabled={loading}
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
          </Card.Content>
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoBox: {
    backgroundColor: '#dc2626',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    marginBottom: 20,
  },
  logoText: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
  },
  appTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
  },
  card: {
    marginBottom: 20,
    elevation: 4,
  },
  cardTitle: {
    textAlign: 'center',
    marginBottom: 20,
    color: '#1e293b',
  },
  input: {
    marginBottom: 16,
  },
  loginButton: {
    marginTop: 10,
    paddingVertical: 8,
  },
  demoCard: {
    backgroundColor: '#fef3c7',
    borderColor: '#f59e0b',
    borderWidth: 1,
  },
  demoTitle: {
    color: '#92400e',
    textAlign: 'center',
    marginBottom: 10,
  },
  demoText: {
    color: '#78350f',
    fontSize: 14,
    lineHeight: 20,
  },
});

export default LoginScreen;