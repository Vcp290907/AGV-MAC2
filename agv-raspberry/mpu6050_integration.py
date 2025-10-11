#!/usr/bin/env python3
"""
Integração MPU6050 (Giroscópio + Acelerômetro) com ESP32
Para navegação avançada do AGV
"""

import serial
import time
import json
import math
from datetime import datetime

class MPU6050Integration:
    """Integração MPU6050 para navegação do AGV"""

    def __init__(self, esp32_port='/dev/ttyUSB0', baudrate=115200):
        self.esp32_port = esp32_port
        self.baudrate = baudrate
        self.serial_conn = None
        self.calibrado = False

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
        self.dt = 0.01     # Intervalo de tempo

    def conectar_esp32(self):
        """Conectar ao ESP32 via serial"""
        try:
            self.serial_conn = serial.Serial(
                self.esp32_port,
                self.baudrate,
                timeout=1
            )
            time.sleep(2)  # Aguardar inicialização

            print(f"✅ Conectado ao ESP32: {self.esp32_port}")
            return True

        except Exception as e:
            print(f"❌ Erro ao conectar ESP32: {e}")
            return False

    def enviar_comando(self, comando, dados=None):
        """Enviar comando para ESP32"""
        try:
            mensagem = {'comando': comando}
            if dados:
                mensagem.update(dados)

            json_str = json.dumps(mensagem) + '\n'
            self.serial_conn.write(json_str.encode())

            # Aguardar resposta
            resposta = self.serial_conn.readline().decode().strip()
            return resposta

        except Exception as e:
            print(f"❌ Erro ao enviar comando: {e}")
            return None

    def calibrar_sensor(self, amostras=100):
        """Calibrar MPU6050"""
        print(f"🔧 Calibrando MPU6050 ({amostras} amostras)...")

        soma_acel = {'x': 0, 'y': 0, 'z': 0}
        soma_giro = {'x': 0, 'y': 0, 'z': 0}

        for i in range(amostras):
            dados = self.ler_dados_brutos()
            if dados:
                for eixo in ['x', 'y', 'z']:
                    soma_acel[eixo] += dados['aceleracao'][eixo]
                    soma_giro[eixo] += dados['giroscopio'][eixo]

            time.sleep(0.01)
            if (i + 1) % 20 == 0:
                print(f"📊 Calibração: {i + 1}/{amostras}")

        # Calcular offsets
        for eixo in ['x', 'y', 'z']:
            self.offset_acel[eixo] = soma_acel[eixo] / amostras
            self.offset_giro[eixo] = soma_giro[eixo] / amostras

        # Ajustar offset Z da aceleração (gravidade)
        self.offset_acel['z'] -= 16384  # 1g em ±2g range

        self.calibrado = True
        print("✅ Calibração concluída!")
        return True

    def ler_dados_brutos(self):
        """Ler dados brutos do MPU6050 via ESP32"""
        resposta = self.enviar_comando('ler_mpu6050')

        if resposta:
            try:
                dados = json.loads(resposta)
                return dados
            except json.JSONDecodeError:
                pass

        return None

    def ler_dados_calibrados(self):
        """Ler dados calibrados do MPU6050"""
        dados_brutos = self.ler_dados_brutos()

        if not dados_brutos or not self.calibrado:
            return None

        # Aplicar calibração
        self.aceleracao = {
            'x': dados_brutos['aceleracao']['x'] - self.offset_acel['x'],
            'y': dados_brutos['aceleracao']['y'] - self.offset_acel['y'],
            'z': dados_brutos['aceleracao']['z'] - self.offset_acel['z']
        }

        self.giroscopio = {
            'x': dados_brutos['giroscopio']['x'] - self.offset_giro['x'],
            'y': dados_brutos['giroscopio']['y'] - self.offset_giro['y'],
            'z': dados_brutos['giroscopio']['z'] - self.offset_giro['z']
        }

        self.temperatura = dados_brutos.get('temperatura', 0)

        return {
            'aceleracao': self.aceleracao,
            'giroscopio': self.giroscopio,
            'temperatura': self.temperatura
        }

    def calcular_orientacao(self):
        """Calcular orientação usando filtro complementário"""
        if not self.calibrado:
            return None

        # Converter aceleração para ângulos (pitch e roll)
        accel_x = self.aceleracao['x'] / 16384.0  # ±2g range
        accel_y = self.aceleracao['y'] / 16384.0
        accel_z = self.aceleracao['z'] / 16384.0

        # Calcular ângulos da aceleração
        accel_pitch = math.atan2(accel_y, math.sqrt(accel_x**2 + accel_z**2)) * 180 / math.pi
        accel_roll = math.atan2(-accel_x, accel_z) * 180 / math.pi

        # Integrar giroscópio
        gyro_x = self.giroscopio['x'] / 131.0  # ±250°/s range
        gyro_y = self.giroscopio['y'] / 131.0
        gyro_z = self.giroscopio['z'] / 131.0

        # Filtro complementário
        self.angulo_x = self.alpha * (self.angulo_x + gyro_x * self.dt) + (1 - self.alpha) * accel_pitch
        self.angulo_y = self.alpha * (self.angulo_y + gyro_y * self.dt) + (1 - self.alpha) * accel_roll
        self.angulo_z += gyro_z * self.dt

        return {
            'pitch': self.angulo_x,
            'roll': self.angulo_y,
            'yaw': self.angulo_z,
            'temperatura': self.temperatura
        }

    def detectar_movimento(self, threshold=500):
        """Detectar movimento baseado na aceleração"""
        total_acel = math.sqrt(
            self.aceleracao['x']**2 +
            self.aceleracao['y']**2 +
            self.aceleracao['z']**2
        )

        return total_acel > threshold

    def detectar_queda(self, threshold=30000):
        """Detectar possível queda do robô"""
        # Se aceleração Z for muito baixa, pode ter caído
        return abs(self.aceleracao['z']) < threshold

    def obter_status_completo(self):
        """Obter status completo do sensor"""
        dados = self.ler_dados_calibrados()
        orientacao = self.calcular_orientacao()

        if not dados or not orientacao:
            return None

        return {
            'timestamp': datetime.now().isoformat(),
            'aceleracao': dados['aceleracao'],
            'giroscopio': dados['giroscopio'],
            'orientacao': orientacao,
            'movimento_detectado': self.detectar_movimento(),
            'queda_detectada': self.detectar_queda(),
            'calibrado': self.calibrado
        }

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
                    print(".2f"                    print(".2f"                    print(".2f"                    print(f"   🧭 Orientação: Pitch={status['orientacao']['pitch']:.1f}°, Roll={status['orientacao']['roll']:.1f}°, Yaw={status['orientacao']['yaw']:.1f}°")
                    print(f"   🔄 Movimento: {'Sim' if status['movimento_detectado'] else 'Não'}")
                    print(f"   📉 Queda: {'Sim' if status['queda_detectada'] else 'Não'}")
                    print()

                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Teste interrompido")

        print(f"✅ Teste concluído! {leituras} leituras realizadas")
        return True

def main():
    """Função principal"""
    print("🎯 INTEGRAÇÃO MPU6050 COM ESP32")
    print("=" * 40)

    # Configurações
    port = '/dev/ttyUSB0'  # Ajuste conforme necessário

    # Criar integração
    mpu = MPU6050Integration(esp32_port=port)

    # Executar teste
    mpu.teste_sensor(duracao=10)

if __name__ == "__main__":
    main()