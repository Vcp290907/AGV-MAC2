/*
Firmware ESP32 com MPU6050 e Buzzer para AGV
Inclui giroscópio, acelerômetro, controle de motores e buzzer

Pinos configurados:
- Buzzer: GPIO 4
- MPU6050 SDA: GPIO 10
- MPU6050 SCL: GPIO 9
- Motor Esquerdo: GPIO 1 (PWM LEDC canal 0)
- Motor Direito: GPIO 3 (PWM LEDC canal 1)

IMPORTANTE:
- Verificar conexões I2C se MPU6050 não for detectado
- Motores agora usam PWM real (LEDC) ao invés de simulação
- Buzzer dá feedback sonoro para cada comando
*/

#include <Wire.h>
#include <MPU6050.h>
#include <ArduinoJson.h>

// Configurações de pinos
#define MOTOR_LEFT_PIN 1    // GPIO 1 - Servo Motor Esquerdo
#define MOTOR_RIGHT_PIN 3   // GPIO 3 - Servo Motor Direito
#define BUZZER_PIN 4        // GPIO 4 - Buzzer
#define MPU6050_SDA 10      // GPIO 10 - SDA do MPU6050
#define MPU6050_SCL 9       // GPIO 9 - SCL do MPU6050

// Configurações MPU6050
MPU6050 mpu;
bool mpu6050_presente = false;

// Variáveis para MPU6050
int16_t ax, ay, az, gx, gy, gz;
float temperature;

// Calibração MPU6050
int16_t offset_ax = 0, offset_ay = 0, offset_az = 0;
int16_t offset_gx = 0, offset_gy = 0, offset_gz = 0;
bool calibrado = false;

// Controle de motores
int velocidade_esquerda = 90;  // 90 = parado
int velocidade_direita = 90;   // 90 = parado

// Comunicação serial
String comando_recebido = "";
bool comando_completo = false;

void setup() {
  // Inicializar serial
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  // Configurar pinos
  pinMode(MOTOR_LEFT_PIN, OUTPUT);
  pinMode(MOTOR_RIGHT_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Configurar PWM para motores (canais 0 e 1)
  ledcSetup(0, 50, 8);  // Canal 0, 50Hz, 8-bit resolution
  ledcSetup(1, 50, 8);  // Canal 1, 50Hz, 8-bit resolution
  ledcAttachPin(MOTOR_LEFT_PIN, 0);
  ledcAttachPin(MOTOR_RIGHT_PIN, 1);

  // Inicializar motores no estado parado
  pararMotores();

  // Buzzer de inicialização
  beepBuzzer();

  // Inicializar I2C com pinos customizados
  Wire.begin(MPU6050_SDA, MPU6050_SCL);

  // Inicializar MPU6050
  inicializarMPU6050();

  Serial.println("{\"status\": \"ESP32 inicializado\"}");
}

void beepBuzzer() {
  tone(BUZZER_PIN, 1000);
  delay(200);  // Beep mais curto para feedback
  noTone(BUZZER_PIN);
  Serial.println("OK");
}

void loop() {
  // Processar comandos seriais
  processarComandosSeriais();

  delay(10);
}

void inicializarMPU6050() {
  Serial.println("{\"status\": \"Inicializando MPU6050...\"}");

  // Aguardar I2C estabilizar
  delay(500);

  mpu.initialize();
  delay(100);

  if (mpu.testConnection()) {
    mpu6050_presente = true;

    // Configurar MPU6050
    mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);  // ±2g
    mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_250);  // ±250°/s

    Serial.println("{\"status\": \"MPU6050 conectado e configurado\"}");

    // Aguardar estabilização
    delay(500);

    // Auto-calibração
    calibrarMPU6050();

  } else {
    mpu6050_presente = false;
    Serial.println("{\"status\": \"MPU6050 não encontrado - verificar conexões I2C\"}");
    Serial.println("{\"status\": \"SDA=GPIO10, SCL=GPIO9\"}");
  }
}

void calibrarMPU6050() {
  Serial.println("{\"status\": \"Calibrando MPU6050...\"}");

  const int amostras = 100;
  long soma_ax = 0, soma_ay = 0, soma_az = 0;
  long soma_gx = 0, soma_gy = 0, soma_gz = 0;

  for (int i = 0; i < amostras; i++) {
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    soma_ax += ax;
    soma_ay += ay;
    soma_az += az;
    soma_gx += gx;
    soma_gy += gy;
    soma_gz += gz;

    delay(10);

    if ((i + 1) % 20 == 0) {
      Serial.printf("{\"calibracao\": {\"progresso\": %d, \"total\": %d}}\n", i + 1, amostras);
    }
  }

  // Calcular offsets
  offset_ax = soma_ax / amostras;
  offset_ay = soma_ay / amostras;
  offset_az = soma_az / amostras - 16384;  // Remover 1g da gravidade
  offset_gx = soma_gx / amostras;
  offset_gy = soma_gy / amostras;
  offset_gz = soma_gz / amostras;

  calibrado = true;
  Serial.println("{\"status\": \"MPU6050 calibrado\"}");
}

void processarComandosSeriais() {
  while (Serial.available()) {
    char caractere = Serial.read();

    if (caractere == '\n') {
      comando_completo = true;
    } else {
      comando_recebido += caractere;
    }
  }

  if (comando_completo) {
    processarComando(comando_recebido);
    comando_recebido = "";
    comando_completo = false;
  }
}

void processarComando(String comando) {
  // Buzzer curto para indicar comando recebido
  beepBuzzer();

  // Parse do JSON
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, comando);

  if (error) {
    Serial.println("{\"erro\": \"JSON inválido\"}");
    return;
  }

  String tipo_comando = doc["comando"];

  if (tipo_comando == "ler_mpu6050") {
    lerDadosMPU6050();

  } else if (tipo_comando == "mover_frente") {
    int velocidade = doc["velocidade"] | 50;  // Velocidade padrão menor
    moverFrente(velocidade);

  } else if (tipo_comando == "mover_tras") {
    int velocidade = doc["velocidade"] | 50;
    moverTras(velocidade);

  } else if (tipo_comando == "virar_esquerda") {
    int velocidade = doc["velocidade"] | 50;
    virarEsquerda(velocidade);

  } else if (tipo_comando == "virar_direita") {
    int velocidade = doc["velocidade"] | 50;
    virarDireita(velocidade);

  } else if (tipo_comando == "parar") {
    pararMotores();

  } else if (tipo_comando == "calibrar_mpu6050") {
    calibrarMPU6050();

  } else if (tipo_comando == "status") {
    enviarStatus();

  } else if (tipo_comando == "beep") {
    beepBuzzer();

  } else {
    Serial.println("{\"erro\": \"Comando desconhecido\"}");
  }
}

void lerDadosMPU6050() {
  if (!mpu6050_presente) {
    Serial.println("{\"erro\": \"MPU6050 não disponível\"}");
    return;
  }

  // Ler dados
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  temperature = mpu.getTemperature() / 340.0 + 36.53;

  // Aplicar calibração se disponível
  if (calibrado) {
    ax -= offset_ax;
    ay -= offset_ay;
    az -= offset_az;
    gx -= offset_gx;
    gy -= offset_gy;
    gz -= offset_gz;
  }

  // Criar resposta JSON
  DynamicJsonDocument resposta(512);
  resposta["aceleracao"]["x"] = ax;
  resposta["aceleracao"]["y"] = ay;
  resposta["aceleracao"]["z"] = az;
  resposta["giroscopio"]["x"] = gx;
  resposta["giroscopio"]["y"] = gy;
  resposta["giroscopio"]["z"] = gz;
  resposta["temperatura"] = temperature;
  resposta["calibrado"] = calibrado;

  serializeJson(resposta, Serial);
  Serial.println();
}

void moverFrente(int velocidade) {
  // Converter velocidade 0-100 para ângulo do servo
  // 90 = parado, 0 = velocidade máxima para frente
  velocidade_esquerda = map(velocidade, 0, 100, 90, 0);
  velocidade_direita = map(velocidade, 0, 100, 90, 180);

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "movendo_frente";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void moverTras(int velocidade) {
  // 90 = parado, 180 = velocidade máxima para trás
  velocidade_esquerda = map(velocidade, 0, 100, 90, 180);
  velocidade_direita = map(velocidade, 0, 100, 90, 0);

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "movendo_tras";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void virarEsquerda(int velocidade) {
  velocidade_esquerda = map(velocidade, 0, 100, 90, 180);  // Trás
  velocidade_direita = map(velocidade, 0, 100, 90, 180);   // Frente

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "virando_esquerda";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void virarDireita(int velocidade) {
  velocidade_esquerda = map(velocidade, 0, 100, 90, 0);    // Frente
  velocidade_direita = map(velocidade, 0, 100, 90, 0);     // Trás

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "virando_direita";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void pararMotores() {
  velocidade_esquerda = 90;
  velocidade_direita = 90;
  aplicarVelocidadeMotores();

  Serial.println("{\"status\": \"parado\"}");
}

void aplicarVelocidadeMotores() {
  // Aplicar PWM nos servos usando LEDC (ESP32 PWM)
  // Converter ângulo do servo (0-180) para duty cycle (0-255)

  int pwm_esquerdo = map(velocidade_esquerda, 0, 180, 0, 255);
  int pwm_direito = map(velocidade_direita, 0, 180, 0, 255);

  // Aplicar PWM usando LEDC
  ledcWrite(0, pwm_esquerdo);  // Canal 0 - Motor esquerdo
  ledcWrite(1, pwm_direito);   // Canal 1 - Motor direito

  // Debug: mostrar valores aplicados
  Serial.printf("{\"motores\": {\"esquerdo\": %d, \"direito\": %d, \"pwm_esq\": %d, \"pwm_dir\": %d}}\n",
                velocidade_esquerda, velocidade_direita, pwm_esquerdo, pwm_direito);
}

void enviarStatus() {
  DynamicJsonDocument resposta(256);
  resposta["status"] = "online";
  resposta["mpu6050"] = mpu6050_presente;
  resposta["calibrado"] = calibrado;
  resposta["buzzer_pin"] = BUZZER_PIN;
  resposta["mpu6050_sda"] = MPU6050_SDA;
  resposta["mpu6050_scl"] = MPU6050_SCL;
  resposta["motores"]["esquerdo"] = velocidade_esquerda;
  resposta["motores"]["direito"] = velocidade_direita;

  if (mpu6050_presente) {
    resposta["sensores"]["temperatura"] = temperature;
  }

  serializeJson(resposta, Serial);
  Serial.println();
}