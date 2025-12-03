#!/usr/bin/env python3
"""
Integração MPU6050 (Giroscópio + Acelerômetro) com ESP32
Para navegação avançada do AGV
"""

try:
    import serial
    HAVE_PYSERIAL = True
except Exception:
    serial = None
    HAVE_PYSERIAL = False
    print("pyserial nao disponivel - usando simulacao")
import time
import json
import math
from datetime import datetime
from config import get_esp32_motor_port as get_esp32_port, get_esp32_motor_baudrate as get_esp32_baudrate

# 🔧 NOVO: Usar controlador centralizado do esp32_control.py
try:
    from esp32_control import get_esp32_motor_controller
    HAVE_ESP32_CONTROL = True
except ImportError:
    HAVE_ESP32_CONTROL = False
    print("⚠️ esp32_control não disponível - usando conexão legada")

class MPU6050Integration:
    """Integração MPU6050 para navegação do AGV"""

    def __init__(self, esp32_port=None, baudrate=None):
        self.esp32_port = esp32_port or get_esp32_port()
        self.baudrate = baudrate or get_esp32_baudrate()
        self.serial_conn = None
        self.calibrado = False
        
        # 🔧 NOVO: Referência ao controlador centralizado
        self.esp32_controller = None

        # Dados do sensor
        self.aceleracao = {'x': 0, 'y': 0, 'z': 0}
        self.giroscopio = {'x': 0, 'y': 0, 'z': 0}
        self.temperatura = 0

        # Orientação calculada
        self.angulo_x = 0
        self.angulo_y = 0
        self.angulo_z = 0

        # Calibração
        self.offset_acel = {'x': 0, 'y': 0, 'z': 0}
        self.offset_giro = {'x': 0, 'y': 0, 'z': 0}

        # Filtros
        self.alpha = 0.98  # Filtro complementário
        self.dt = 0.1     # Intervalo de tempo (0.1s entre leituras)

    def conectar_esp32(self):
        """Conectar ao ESP32 via serial - usando controlador centralizado"""
        try:
            # 🔧 PRIORIDADE: Usar controlador centralizado com descoberta automática
            if HAVE_ESP32_CONTROL:
                print("🔌 Usando controlador ESP32 centralizado com descoberta automática...")
                self.esp32_controller = get_esp32_motor_controller()
                
                # Se já estiver conectado, usar a conexão existente
                if self.esp32_controller.connected and self.esp32_controller.serial_connection:
                    self.serial_conn = self.esp32_controller.serial_connection
                    print(f"✅ Usando conexão ESP32 existente: {self.esp32_controller.port}")
                    return True
                
                # Caso contrário, conectar
                if self.esp32_controller.connect():
                    self.serial_conn = self.esp32_controller.serial_connection
                    print(f"✅ ESP32 Motor conectado via controlador: {self.esp32_controller.port}")
                    return True
                else:
                    print("❌ Falha ao conectar via controlador centralizado, tentando método legado...")
            
            # Fallback: método legado
            if not HAVE_PYSERIAL:
                print("pyserial nao disponivel - simulando conexao ESP32")
                self.serial_conn = None  # Simulação
                return True
                
            self.serial_conn = serial.Serial(
                self.esp32_port,
                self.baudrate,
                timeout=2
            )
            time.sleep(2)  # Aguardar inicialização

            print(f"Conectado ao ESP32: {self.esp32_port}")
            return True

        except Exception as e:
            print(f"Erro ao conectar ESP32: {e}")
            return False

    def enviar_comando(self, comando, dados=None):
        """Enviar comando para ESP32"""
        try:
            if not HAVE_PYSERIAL or self.serial_conn is None:
                print(f"(simulacao) comando enviado: {comando}")
                return '{"status": "ok"}'

            # 🔧 Verificar se a porta está aberta
            if hasattr(self.serial_conn, 'is_open') and not self.serial_conn.is_open:
                print(f"⚠️ Porta serial fechada, tentando reconectar...")
                if self.esp32_controller:
                    # Reconectar via controlador
                    if self.esp32_controller.connect():
                        self.serial_conn = self.esp32_controller.serial_connection
                        print(f"✅ Reconectado com sucesso")
                    else:
                        print(f"❌ Falha ao reconectar")
                        return None
                else:
                    # Tentar reabrir porta legada
                    try:
                        self.serial_conn.open()
                        print(f"✅ Porta reaberta com sucesso")
                    except Exception as e:
                        print(f"❌ Erro ao reabrir porta: {e}")
                        return None

            # Limpar buffer de entrada
            if self.serial_conn:
                self.serial_conn.reset_input_buffer()

            mensagem = {'comando': comando}
            if dados:
                mensagem.update(dados)

            json_str = json.dumps(mensagem) + '\n'
            self.serial_conn.write(json_str.encode())

            # Aguardar resposta
            resposta = self.serial_conn.readline().decode().strip()
            return resposta

        except Exception as e:
            print(f"Erro ao enviar comando: {e}")
            return None

    def calibrar_sensor(self, amostras=10):
        """Calibrar MPU6050 - calibração feita no ESP32"""
        # Calibração é feita no ESP32 com mpu.calcOffsets()
        self.calibrado = True
        return True

    def ler_dados_brutos(self):
        """Ler dados brutos do MPU6050 via ESP32 - ângulos"""
        if not HAVE_PYSERIAL or self.serial_conn is None:
            # Simulação
            return {
                'angulos': {'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0},
                'calibrado': True
            }

        resposta = self.enviar_comando('ler_mpu6050')

        if resposta:
            try:
                dados = json.loads(resposta)
                if 'angulos' in dados:
                    return dados
            except json.JSONDecodeError:
                pass

        # Se não conseguiu na primeira resposta, tentar ler mais linhas
        for _ in range(5):  # Tentar até 5 linhas adicionais
            try:
                linha = self.serial_conn.readline().decode().strip()
                if linha:
                    dados = json.loads(linha)
                    if 'angulos' in dados:
                        return dados
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

        return None

    def obter_status_completo(self):
        """Obter status completo do sensor - ângulos diretos"""
        dados = self.ler_dados_brutos()

        if not dados:
            return None

        return {
            'timestamp': datetime.now().isoformat(),
            'orientacao': dados['angulos'],
            'calibrado': dados.get('calibrado', False)
        }

    def teste_buzzer(self):
        """Teste do buzzer"""
        print("🔊 TESTANDO BUZZER")
        print("=" * 20)

        if not self.conectar_esp32():
            return False

        print("📡 Enviando comando beep...")
        resposta = self.enviar_comando('beep')

        if resposta:
            print("✅ Comando enviado com sucesso!")
            print(f"📄 Resposta: {resposta}")
            return True
        else:
            print("❌ Falha ao enviar comando")
            return False

    def teste_sensor(self, duracao=10):
        """Teste básico do sensor"""
        print("🧪 TESTANDO MPU6050")
        print("=" * 30)

        if not self.conectar_esp32():
            return False

        if not self.calibrar_sensor():
            return False

        print(f"📊 Lendo dados por {duracao} segundos...")

        inicio = time.time()
        leituras = 0

        try:
            while time.time() - inicio < duracao:
                status = self.obter_status_completo()

                if status:
                    leituras += 1
                    print(f"📈 Leitura {leituras}:")
                    print(".2f")
                    print(".2f")
                    print(".2f")
                    print(f"   🧭 Orientação: Pitch={status['orientacao']['pitch']:.1f}°, Roll={status['orientacao']['roll']:.1f}°, Yaw={status['orientacao']['yaw']:.1f}°")
                    print()

                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Teste interrompido")

        print(f"✅ Teste concluído! {leituras} leituras realizadas")
        return True

def detectar_porta_esp32():
    """Detectar automaticamente a porta do ESP32"""
    import glob
    import platform
    if not HAVE_PYSERIAL:
        print("⚠️ pyserial não disponível - detecção automática desativada")
        return None
    import serial

    system = platform.system().lower()

    if system == 'linux':
        # Procurar por portas ACM (ESP32) ou USB (Arduino)
        portas = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    elif system == 'darwin':  # macOS
        portas = glob.glob('/dev/tty.usb*') + glob.glob('/dev/tty.wchusb*')
    elif system == 'windows':
        import serial.tools.list_ports
        portas = [p.device for p in serial.tools.list_ports.comports()]
    else:
        portas = []

    print("🔍 Procurando portas seriais disponíveis...")
    for porta in portas:
        print(f"   📡 Porta encontrada: {porta}")

    # Tentar conectar a cada porta para ver se é ESP32
    for porta in portas:
        try:
            print(f"🧪 Testando porta: {porta}")
            ser = serial.Serial(porta, 115200, timeout=2)
            time.sleep(2)  # Aguardar inicialização

            # Enviar comando de status
            ser.write(b'{"comando": "status"}\n')
            resposta = ser.readline().decode().strip()

            if resposta and ('status' in resposta or 'online' in resposta):
                print(f"✅ ESP32 encontrado na porta: {porta}")
                ser.close()
                return porta
            else:
                print(f"❌ Porta {porta} não é ESP32")
                ser.close()

        except Exception as e:
            print(f"❌ Erro ao testar porta {porta}: {e}")
            continue

    print("❌ Nenhum ESP32 encontrado automaticamente")
    return None

def menu_interativo():
    """Menu interativo para testes"""
    print("🎯 CONTROLE ESP32 - MPU6050 + BUZZER")
    print("=" * 45)

    # Detectar porta automaticamente
    print("🔍 Detectando porta do ESP32...")
    porta_detectada = detectar_porta_esp32()

    if porta_detectada:
        port = porta_detectada
        print(f"✅ Usando porta detectada: {port}")
    else:
        # Fallback para configuração do config.py
        port = get_esp32_port()
        print(f"⚠️  Usando porta do config: {port}")
        print("💡 Para alterar, edite config.py ou passe --port")

    # Criar integração
    esp32 = MPU6050Integration(esp32_port=port)

    while True:
        print("\n" + "="*50)
        print("🎮 MENU DE TESTES ESP32")
        print("="*50)
        print(f"📡 Porta atual: {esp32.esp32_port}")
        print("1. Teste básico de comunicação")
        print("2. Teste buzzer")
        print("3. Ler dados do MPU6050")
        print("4. Calibrar MPU6050")
        print("5. Teste de movimento (frente)")
        print("6. Teste de movimento (trás)")
        print("7. Teste de curva (esquerda)")
        print("8. Teste de curva (direita)")
        print("9. Parar motores")
        print("10. Status completo")
        print("11. Teste completo do sensor (10s)")
        print("12. Alterar porta manualmente")
        print("0. Sair")
        print("="*50)

        try:
            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                # Teste básico de comunicação
                if esp32.conectar_esp32():
                    resposta = esp32.enviar_comando('status')
                    if resposta:
                        print("✅ Comunicação OK!")
                        print(f"📄 Status: {resposta}")
                    else:
                        print("❌ Sem resposta")
                else:
                    print("❌ Falha na conexão")

            elif opcao == '2':
                # Teste buzzer
                esp32.teste_buzzer()

            elif opcao == '3':
                # Ler dados MPU6050
                if esp32.conectar_esp32():
                    dados = esp32.ler_dados_brutos()
                    if dados:
                        print("📊 Dados MPU6050:")
                        angulos = dados['angulos']
                        print(f"   Ângulos: Pitch={angulos['pitch']:.1f}°, Roll={angulos['roll']:.1f}°, Yaw={angulos['yaw']:.1f}°")
                    else:
                        print("❌ Falha ao ler dados")
                else:
                    print("❌ ESP32 não conectado")

            elif opcao == '4':
                # Calibrar MPU6050
                if esp32.conectar_esp32():
                    esp32.calibrar_sensor()
                else:
                    print("❌ ESP32 não conectado")

            elif opcao == '5':
                # Movimento frente
                if esp32.conectar_esp32():
                    resposta = esp32.enviar_comando('mover_frente', {'velocidade': 50})
                    print(f"📡 Comando enviado: {resposta}")

            elif opcao == '6':
                # Movimento trás
                if esp32.conectar_esp32():
                    resposta = esp32.enviar_comando('mover_tras', {'velocidade': 50})
                    print(f"📡 Comando enviado: {resposta}")

            elif opcao == '7':
                # Curva esquerda
                if esp32.conectar_esp32():
                    resposta = esp32.enviar_comando('virar_esquerda', {'velocidade': 50})
                    print(f"📡 Comando enviado: {resposta}")

            elif opcao == '8':
                # Curva direita
                if esp32.conectar_esp32():
                    resposta = esp32.enviar_comando('virar_direita', {'velocidade': 50})
                    print(f"📡 Comando enviado: {resposta}")

            elif opcao == '9':
                # Parar motores
                if esp32.conectar_esp32():
                    resposta = esp32.enviar_comando('parar')
                    print(f"📡 Comando enviado: {resposta}")

            elif opcao == '10':
                # Status completo
                if esp32.conectar_esp32():
                    resposta = esp32.enviar_comando('status')
                    if resposta:
                        try:
                            status = json.loads(resposta)
                            print("📊 STATUS ESP32:")
                            print(f"   Online: {status.get('status', 'unknown')}")
                            print(f"   MPU6050: {'Sim' if status.get('mpu6050') else 'Não'}")
                            print(f"   Calibrado: {'Sim' if status.get('calibrado') else 'Não'}")
                            print(f"   Buzzer PIN: {status.get('buzzer_pin', 'N/A')}")
                            print(f"   MPU SDA/SCL: {status.get('mpu6050_sda', 'N/A')}/{status.get('mpu6050_scl', 'N/A')}")
                            motores = status.get('motores', {})
                            print(f"   Motores: Esq={motores.get('esquerdo', 'N/A')}, Dir={motores.get('direito', 'N/A')}")
                        except:
                            print(f"📄 Resposta: {resposta}")
                    else:
                        print("❌ Sem resposta")

            elif opcao == '11':
                # Teste completo
                esp32.teste_sensor(duracao=10)

            elif opcao == '12':
                # Alterar porta manualmente
                print("🔧 ALTERAR PORTA MANUALMENTE")
                print("Portas disponíveis:")
                import glob
                import platform
                system = platform.system().lower()

                if system == 'linux':
                    portas = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
                elif system == 'darwin':
                    portas = glob.glob('/dev/tty.usb*') + glob.glob('/dev/tty.wchusb*')
                elif system == 'windows':
                    import serial.tools.list_ports
                    portas = [p.device for p in serial.tools.list_ports.comports()]
                else:
                    portas = []

                for i, p in enumerate(portas, 1):
                    print(f"   {i}. {p}")

                try:
                    escolha = input("Escolha o número da porta (ou digite a porta completa): ").strip()
                    if escolha.isdigit() and 1 <= int(escolha) <= len(portas):
                        nova_porta = portas[int(escolha) - 1]
                    else:
                        nova_porta = escolha

                    # Recriar objeto com nova porta
                    esp32 = MPU6050Integration(esp32_port=nova_porta)
                    print(f"✅ Porta alterada para: {nova_porta}")

                except Exception as e:
                    print(f"❌ Erro ao alterar porta: {e}")

            elif opcao == '0':
                print("👋 Saindo...")
                break

            else:
                print("❌ Opção inválida")

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

def main():
    """Função principal"""
    menu_interativo()

if __name__ == "__main__":
    main()