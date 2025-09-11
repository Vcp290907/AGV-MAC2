import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, Alert, Text } from 'react-native';
import { Camera, CameraView } from 'expo-camera';
import { Button, Card, Title, Paragraph, ActivityIndicator } from 'react-native-paper';

interface QRScannerScreenProps {
  navigation: any;
  route: any;
}

const QRScannerScreen: React.FC<QRScannerScreenProps> = ({ navigation, route }) => {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanned, setScanned] = useState(false);
  const [loading, setLoading] = useState(false);
  const [serverUrl, setServerUrl] = useState('http://192.168.0.134:5000');

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');

      // Testar conectividade com o servidor
      await testarConectividade();
    })();
  }, []);

  const testarConectividade = async () => {
    try {
      console.log('🌐 Testando conectividade com servidor...');
      Alert.alert('Testando Conectividade', 'Verificando conexão com o servidor...');

      const response = await fetch(`${serverUrl}/status`);
      if (response.ok) {
        console.log('✅ Servidor acessível via:', serverUrl);
        Alert.alert('✅ Sucesso', `Servidor acessível via ${serverUrl}`);
      } else {
        console.log('⚠️ Servidor respondeu mas com erro:', response.status);
        Alert.alert('⚠️ Aviso', `Servidor respondeu com erro: ${response.status}`);
      }
    } catch (error) {
      console.log('❌ Erro de conectividade:', error);
      Alert.alert('❌ Erro de Rede', `Não foi possível conectar ao servidor: ${error instanceof Error ? error.message : 'Erro desconhecido'}`);

      console.log('💡 Tentando localhost...');

      // Tentar localhost como alternativa
      try {
        const response = await fetch('http://10.0.2.2:5000/status'); // Para Android emulator
        if (response.ok) {
          console.log('✅ Servidor acessível via localhost (Android emulator)');
          setServerUrl('http://10.0.2.2:5000');
          Alert.alert('✅ Alternativa Encontrada', 'Servidor acessível via localhost (emulador)');
        }
      } catch (error2) {
        console.log('❌ Localhost também falhou');
        Alert.alert('❌ Problema de Rede', 'Verifique se o servidor está rodando e se há conectividade WiFi');
      }
    }
  };

  const handleBarCodeScanned = async ({ type, data }: { type: string; data: string }) => {
    console.log('🎯 handleBarCodeScanned CHAMADA!');
    console.log('📊 Tipo:', type);
    console.log('📝 Dados:', data);

    setScanned(true);
    setLoading(true);

    try {
      // Processar o QR code lido
      console.log('🚀 Iniciando processamento do QR Code:', data);
      Alert.alert('📱 QR Code Detectado', `Código lido: ${data}\nIniciando busca...`);

      // Verificar se é um QR code válido do sistema AGV
      console.log('🔍 Verificando formato do QR code...');
      console.log('📋 Data recebida:', data);
      console.log('📋 startsWith AGV-:', data.startsWith('AGV-'));
      console.log('📋 includes Corredor_:', data.includes('Corredor_'));
      console.log('📋 regex ^\\d{4,}$:', /^\d{4,}$/.test(data));
      console.log('📋 startsWith TAG:', data.startsWith('TAG'));

      if (data.startsWith('AGV-') || data.includes('Corredor_') || /^\d{4,}$/.test(data) || data.startsWith('TAG')) {
        console.log('✅ QR code válido detectado, iniciando busca...');
        // QR code válido - buscar informações do item
        const itemInfo = await buscarItemPorQR(data);

        if (itemInfo) {
          Alert.alert(
            'Item Encontrado!',
            `Nome: ${itemInfo.nome}\nTag: ${itemInfo.tag}\nCategoria: ${itemInfo.categoria}`,
            [
              {
                text: 'Adicionar ao Pedido',
                onPress: () => {
                  // Passar o item para a tela de pedidos
                  navigation.navigate('Orders', { itemParaAdicionar: itemInfo });
                }
              },
              {
                text: 'Ver Detalhes',
                onPress: () => {
                  // Mostrar detalhes do item
                  Alert.alert(
                    'Detalhes do Item',
                    `Nome: ${itemInfo.nome}\nTag: ${itemInfo.tag}\nCategoria: ${itemInfo.categoria}\nLocalização: Corredor ${itemInfo.corredor}, Sub ${itemInfo.sub_corredor}, Pos ${itemInfo.posicao_x}`,
                    [{ text: 'OK' }]
                  );
                }
              },
              {
                text: 'Escanear Outro',
                onPress: () => setScanned(false)
              }
            ]
          );
        } else {
          Alert.alert(
            'Item Não Encontrado',
            'Este QR code não corresponde a nenhum item cadastrado no sistema.',
            [
              { text: 'Tentar Novamente', onPress: () => setScanned(false) },
              { text: 'Voltar', onPress: () => navigation.goBack() }
            ]
          );
        }
      } else {
        Alert.alert(
          'QR Code Inválido',
          'Este QR code não é válido para o sistema AGV.',
          [
            { text: 'Tentar Novamente', onPress: () => setScanned(false) },
            { text: 'Voltar', onPress: () => navigation.goBack() }
          ]
        );
      }
    } catch (error) {
      console.error('Erro ao processar QR code:', error);
      Alert.alert(
        'Erro',
        'Erro ao processar o QR code. Tente novamente.',
        [{ text: 'OK', onPress: () => setScanned(false) }]
      );
    } finally {
      setLoading(false);
    }
  };

  const buscarItemPorQR = async (qrData: string) => {
    try {
      console.log('🔍 Iniciando busca para QR:', qrData);
      Alert.alert('🔍 Buscando Item', `Procurando item para: ${qrData}`);

      // Tentar diferentes formatos de QR code
      let response;
      let urlTentada = '';

      // Se for formato TAGXXXX (como TAG0001)
      if (qrData.startsWith('TAG') && /^\d{4,}$/.test(qrData.substring(3))) {
        console.log('📋 Detectado formato TAGXXXX');

        // Primeiro tenta buscar com o formato completo TAGXXXX
        urlTentada = `${serverUrl}/itens/tag/${qrData}`;
        console.log('🔗 Tentando URL:', urlTentada);
        response = await fetch(urlTentada);

        if (response.ok) {
          console.log('✅ Sucesso na primeira tentativa');
          Alert.alert('✅ Item Encontrado!', 'Busca realizada com sucesso.');
          const data = await response.json();
          return data;
        } else {
          console.log('❌ Primeira tentativa falhou, tentando sem prefixo TAG');
          Alert.alert('🔄 Tentando Alternativa', 'Primeira busca falhou, tentando formato alternativo...');

          // Se não encontrou, tenta buscar apenas com os números
          const tagNumerica = qrData.substring(3);
          urlTentada = `${serverUrl}/itens/tag/${tagNumerica}`;
          console.log('🔗 Tentando URL alternativa:', urlTentada);
          response = await fetch(urlTentada);

          if (response.ok) {
            console.log('✅ Sucesso na segunda tentativa');
            const data = await response.json();
            return data;
          }
        }
      }
      // Se for uma tag numérica (4+ dígitos) - pode ser apenas números
      else if (/^\d{4,}$/.test(qrData)) {
        console.log('📋 Detectado formato numérico');

        // Primeiro tenta buscar com o formato exato
        urlTentada = `${serverUrl}/itens/tag/${qrData}`;
        console.log('🔗 Tentando URL:', urlTentada);
        response = await fetch(urlTentada);

        if (response.ok) {
          console.log('✅ Sucesso na busca numérica');
          const data = await response.json();
          return data;
        }
      }
      // Se for formato Corredor_SubCorredor
      else if (qrData.includes('Corredor_') && qrData.includes('SubCorredor_')) {
        console.log('📋 Detectado formato localização');

        const partes = qrData.split('/');
        if (partes.length >= 2) {
          const corredor = partes[0].split('_')[1];
          const subCorredor = partes[1].split('_')[1];
          urlTentada = `${serverUrl}/itens/localizacao/${corredor}/${subCorredor}`;
          console.log('🔗 Tentando URL localização:', urlTentada);
          response = await fetch(urlTentada);
        }
      }
      // Busca geral por nome/tag
      else {
        console.log('📋 Usando busca geral');

        urlTentada = `${serverUrl}/itens/buscar?q=${encodeURIComponent(qrData)}`;
        console.log('🔗 Tentando URL geral:', urlTentada);
        response = await fetch(urlTentada);
      }

      if (response && response.ok) {
        console.log('✅ Resposta OK recebida');
        const data = await response.json();
        console.log('📦 Dados recebidos:', data);

        // Para busca geral, retorna o primeiro item se existir
        if (Array.isArray(data)) {
          return data.length > 0 ? data[0] : null;
        }
        // Para busca específica, retorna o item diretamente
        return data;
      } else {
        console.log('❌ Resposta não OK:', response ? response.status : 'Sem resposta');
      }

      console.log('🔍 Busca concluída sem sucesso');
      return null;
    } catch (error) {
      console.error('💥 Erro ao buscar item:', error);
      return null;
    }
  };

  if (hasPermission === null) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Solicitando permissão da câmera...</Text>
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={styles.container}>
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.title}>Permissão Negada</Title>
            <Paragraph style={styles.paragraph}>
              Para usar o scanner de QR code, você precisa permitir o acesso à câmera.
            </Paragraph>
            <Button
              mode="contained"
              onPress={() => navigation.goBack()}
              style={styles.button}
            >
              Voltar
            </Button>
          </Card.Content>
        </Card>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        style={StyleSheet.absoluteFillObject}
        facing="back"
        onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
      />

      {/* Overlay com instruções */}
      <View style={styles.overlay}>
        <View style={styles.scanArea}>
          <View style={styles.cornerTopLeft} />
          <View style={styles.cornerTopRight} />
          <View style={styles.cornerBottomLeft} />
          <View style={styles.cornerBottomRight} />
        </View>

        <Card style={styles.instructionsCard}>
          <Card.Content>
            <Title style={styles.instructionsTitle}>Scanner de QR Code</Title>
            <Paragraph style={styles.instructionsText}>
              Posicione o QR code dentro da área marcada para escanear automaticamente.
            </Paragraph>
          </Card.Content>
        </Card>

        {scanned && (
          <Card style={styles.resultCard}>
            <Card.Content>
              <Title style={styles.resultTitle}>Processando...</Title>
              {loading && <ActivityIndicator size="small" />}
            </Card.Content>
          </Card>
        )}

        <View style={styles.buttonContainer}>
          <Button
            mode="contained"
            onPress={() => setScanned(false)}
            style={styles.scanButton}
            disabled={loading}
          >
            {scanned ? 'Escanear Novamente' : 'Pausar Scanner'}
          </Button>

          <Button
            mode="outlined"
            onPress={testarConectividade}
            style={styles.testButton}
          >
            🧪 Testar Conexão
          </Button>

          <Button
            mode="outlined"
            onPress={() => navigation.goBack()}
            style={styles.backButton}
          >
            Voltar
          </Button>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  loadingText: {
    color: '#fff',
    fontSize: 16,
    marginTop: 20,
  },
  card: {
    margin: 20,
    elevation: 4,
  },
  title: {
    textAlign: 'center',
    color: '#1e293b',
  },
  paragraph: {
    textAlign: 'center',
    marginVertical: 10,
  },
  button: {
    marginTop: 20,
  },
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanArea: {
    width: 250,
    height: 250,
    borderWidth: 2,
    borderColor: '#00ff00',
    backgroundColor: 'transparent',
    position: 'relative',
  },
  cornerTopLeft: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: 20,
    height: 20,
    borderTopWidth: 4,
    borderLeftWidth: 4,
    borderColor: '#00ff00',
    borderTopLeftRadius: 10,
  },
  cornerTopRight: {
    position: 'absolute',
    top: 0,
    right: 0,
    width: 20,
    height: 20,
    borderTopWidth: 4,
    borderRightWidth: 4,
    borderColor: '#00ff00',
    borderTopRightRadius: 10,
  },
  cornerBottomLeft: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    width: 20,
    height: 20,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
    borderColor: '#00ff00',
    borderBottomLeftRadius: 10,
  },
  cornerBottomRight: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 20,
    height: 20,
    borderBottomWidth: 4,
    borderRightWidth: 4,
    borderColor: '#00ff00',
    borderBottomRightRadius: 10,
  },
  instructionsCard: {
    marginTop: 30,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    marginHorizontal: 20,
  },
  instructionsTitle: {
    color: '#fff',
    textAlign: 'center',
  },
  instructionsText: {
    color: '#fff',
    textAlign: 'center',
    opacity: 0.9,
  },
  resultCard: {
    marginTop: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  resultTitle: {
    color: '#fff',
    textAlign: 'center',
  },
  buttonContainer: {
    position: 'absolute',
    bottom: 50,
    left: 20,
    right: 20,
    gap: 10,
  },
  scanButton: {
    backgroundColor: '#00ff00',
  },
  backButton: {
    borderColor: '#fff',
  },
  testButton: {
    borderColor: '#ffa500',
  },
});

export default QRScannerScreen;