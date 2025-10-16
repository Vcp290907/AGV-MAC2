/*
Firmware ESP32 com MPU6050_light e Servo para AGV
Inclui giroscópio, acelerômetro, controle de motores e buzzer

BIBLIOTECAS UTILIZADAS:
- MPU6050_light: Leitura simplificada do giroscópio/acelerômetro
- ESP32Servo: Controle dos motores para ESP32
- ArduinoJson: Comunicação JSON
- Wire: Comunicação I2C

Pinos configurados:
- Buzzer: GPIO 4
- MPU6050 SDA: GPIO 10
- MPU6050 SCL: GPIO 9
- Motor Esquerdo: GPIO 1 (Servo)
- Motor Direito: GPIO 3 (Servo)

IMPORTANTE:
- Motores usam Servo para controle direto
- MPU6050_light tem calibração automática
- Buzzer dá feedback sonoro para cada comando
- Comunicação JSON via serial
*/

#include <Wire.h>
#include <MPU6050_light.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// Configurações de pinos
#define MOTOR_LEFT_PIN 1  // GPIO 1 - Servo Motor Esquerdo
#define MOTOR_RIGHT_PIN 3 // GPIO 3 - Servo Motor Direito
#define BUZZER_PIN 4      // GPIO 4 - Buzzer
#define MPU6050_SDA 10    // GPIO 10 - SDA do MPU6050
#define MPU6050_SCL 9     // GPIO 9 - SCL do MPU6050

// Configurações MPU6050_light
MPU6050 mpu(Wire);
bool mpu6050_presente = false;

// Variáveis para MPU6050_light (dados em unidades SI)
float ax, ay, az, gx, gy, gz;
float temperature;

// Calibração MPU6050_light (automática pela biblioteca)
bool calibrado = false;

// Offsets para ângulos (para reset após calibração)
float angulo_offset_x = 0;
float angulo_offset_y = 0;
float angulo_offset_z = 0;

// Controle de motores com Servo
Servo servoEsquerdo;
Servo servoDireito;

// Constantes de servo (contínuo): 90=parado, >90 um sentido, <90 outro
const int SERVO_NEUTRO = 90;
// Valores de avanço/re quando mapeados a 100% (ajuste conforme seu hardware)
// Observação: muitos kits usam servos espelhados, então esquerda e direita podem ter "frente" opostos
// Defina aqui de forma explícita para evitar confusão:
const int LEFT_FORWARD_VAL = 180;   // esquerda indo para frente
const int LEFT_BACKWARD_VAL = 0;    // esquerda indo para trás
const int RIGHT_FORWARD_VAL = 0;    // direita indo para frente (servos espelhados ao contrário)
const int RIGHT_BACKWARD_VAL = 180; // direita indo para trás (servos espelhados ao contrário)

int velocidade_esquerda = SERVO_NEUTRO; // 90 = parado
int velocidade_direita = SERVO_NEUTRO;  // 90 = parado

// Comunicação serial
String comando_recebido = "";
bool comando_completo = false;

void setup()
{
  // Inicializar serial
  Serial.begin(115200);
  while (!Serial)
  {
    delay(10);
  }

  // Configurar pinos
  pinMode(BUZZER_PIN, OUTPUT);

  // Inicializar servos
  servoEsquerdo.attach(MOTOR_LEFT_PIN);
  servoDireito.attach(MOTOR_RIGHT_PIN);

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

void beepBuzzer()
{
  tone(BUZZER_PIN, 1000);
  delay(200); // Beep mais curto para feedback
  noTone(BUZZER_PIN);
  Serial.println("OK");
}

void loop()
{
  // Processar comandos seriais
  processarComandosSeriais();

  delay(10);
}

void inicializarMPU6050()
{
  Serial.println("{\"status\": \"Inicializando MPU6050_light...\"}");

  // Aguardar I2C estabilizar
  delay(500);

  // MPU6050_light: inicialização e teste de conexão simplificados
  byte status = mpu.begin();
  delay(100);

  if (status == 0)
  {
    mpu6050_presente = true;
    Serial.println("{\"status\": \"MPU6050_light conectado\"}");

    // Aguardar estabilização
    delay(500);

    // Auto-calibração da biblioteca
    calibrarMPU6050();
  }
  else
  {
    mpu6050_presente = false;
    Serial.printf("{\"status\": \"MPU6050_light erro: %d - verificar conexões I2C\"}\n", status);
    Serial.println("{\"status\": \"SDA=GPIO10, SCL=GPIO9\"}");
  }
}

void calibrarMPU6050()
{
  Serial.println("{\"status\": \"Calibrando MPU6050_light...\"}");

  // Calibração automática da MPU6050_light
  mpu.calcOffsets(true, true); // Calibra acel (true) e giro (true)

  // Aguardar calibração completar
  delay(1000);

  // Atualizar MPU e capturar ângulos atuais como offsets
  mpu.update();
  angulo_offset_x = mpu.getAngleX();
  angulo_offset_y = mpu.getAngleY();
  angulo_offset_z = mpu.getAngleZ();

  calibrado = true;
  Serial.println("{\"status\": \"MPU6050_light calibrado e offsets definidos\"}");
}

void processarComandosSeriais()
{
  while (Serial.available())
  {
    char caractere = Serial.read();

    if (caractere == '\n')
    {
      comando_completo = true;
    }
    else
    {
      comando_recebido += caractere;
    }
  }

  if (comando_completo)
  {
    processarComando(comando_recebido);
    comando_recebido = "";
    comando_completo = false;
  }
}

void processarComando(String comando)
{
  // Buzzer curto para indicar comando recebido
  // beepBuzzer();  // Desabilitado para evitar beeps constantes

  // Parse do JSON
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, comando);

  if (error)
  {
    Serial.println("{\"erro\": \"JSON inválido\"}");
    return;
  }

  String tipo_comando = doc["comando"];

  if (tipo_comando == "ler_mpu6050")
  {
    lerDadosMPU6050();
  }
  else if (tipo_comando == "mover_frente")
  {
    int velocidade = doc["velocidade"] | 50; // Velocidade padrão menor
    moverFrente(velocidade);
  }
  else if (tipo_comando == "mover_tras")
  {
    int velocidade = doc["velocidade"] | 50;
    moverTras(velocidade);
  }
  else if (tipo_comando == "virar_esquerda")
  {
    int velocidade = doc["velocidade"] | 25; // Velocidade padrão ainda mais reduzida para precisão
    virarEsquerda(velocidade);
  }
  else if (tipo_comando == "virar_direita")
  {
    int velocidade = doc["velocidade"] | 25; // Velocidade padrão ainda mais reduzida para precisão
    virarDireita(velocidade);
  }
  else if (tipo_comando == "parar")
  {
    pararMotores();
  }
  else if (tipo_comando == "calibrar_mpu6050")
  {
    calibrarMPU6050();
  }
  else if (tipo_comando == "status")
  {
    enviarStatus();
  }
  else if (tipo_comando == "beep")
  {
    beepBuzzer();
  }
  else if (tipo_comando == "move")
  {
    String direction = doc["direction"];
    int velocidade = doc["velocidade"] | 50;
    if (direction == "forward")
    {
      moverFrente(velocidade);
    }
    else if (direction == "backward")
    {
      moverTras(velocidade);
    }
  }
  else if (tipo_comando == "stop")
  {
    pararMotores();
    Serial.println("{\"status\": \"success\"}");
  }
  else if (tipo_comando == "ping")
  {
    Serial.println("{\"status\": \"ok\"}");
  }
  else
  {
    Serial.println("{\"erro\": \"Comando desconhecido\"}");
  }
}

void lerDadosMPU6050()
{
  if (!mpu6050_presente)
  {
    Serial.println("{\"erro\": \"MPU6050 não disponível\"}");
    return;
  }

  // Aguardar estabilização
  delay(10);

  // MPU6050_light: update e leitura dos ângulos
  mpu.update();

  float angX = mpu.getAngleX() - angulo_offset_x; // Pitch
  float angY = mpu.getAngleY() - angulo_offset_y; // Roll
  float angZ = mpu.getAngleZ() - angulo_offset_z; // Yaw

  // Normalizar ângulos para 0-360°
  angX = fmod(angX, 360.0);
  if (angX < 0)
    angX += 360.0;

  angY = fmod(angY, 360.0);
  if (angY < 0)
    angY += 360.0;

  angZ = fmod(angZ, 360.0);
  if (angZ < 0)
    angZ += 360.0;

  // JSON resposta com ângulos
  DynamicJsonDocument resposta(256);
  resposta["angulos"]["pitch"] = angX;
  resposta["angulos"]["roll"] = angY;
  resposta["angulos"]["yaw"] = angZ;
  resposta["calibrado"] = calibrado;
  resposta["biblioteca"] = "MPU6050_light";

  serializeJson(resposta, Serial);
  Serial.println();
}

void moverFrente(int velocidade)
{
  // Para frente: usar constantes explícitas por lado
  velocidade_esquerda = map(velocidade, 0, 100, SERVO_NEUTRO, LEFT_FORWARD_VAL);
  velocidade_direita = map(velocidade, 0, 100, SERVO_NEUTRO, RIGHT_FORWARD_VAL);

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void moverTras(int velocidade)
{
  // Para trás: usar constantes explícitas por lado
  velocidade_esquerda = map(velocidade, 0, 100, SERVO_NEUTRO, LEFT_BACKWARD_VAL);
  velocidade_direita = map(velocidade, 0, 100, SERVO_NEUTRO, RIGHT_BACKWARD_VAL);

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void virarEsquerda(int velocidade)
{
  // Virar esquerda: esquerda para trás, direita para frente
  velocidade_esquerda = map(velocidade, 0, 100, SERVO_NEUTRO, LEFT_BACKWARD_VAL);
  velocidade_direita = map(velocidade, 0, 100, SERVO_NEUTRO, RIGHT_FORWARD_VAL);

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void virarDireita(int velocidade)
{
  // Virar direita: esquerda para frente, direita para trás
  velocidade_esquerda = map(velocidade, 0, 100, SERVO_NEUTRO, LEFT_FORWARD_VAL);
  velocidade_direita = map(velocidade, 0, 100, SERVO_NEUTRO, RIGHT_BACKWARD_VAL);

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void pararMotores()
{
  velocidade_esquerda = SERVO_NEUTRO;
  velocidade_direita = SERVO_NEUTRO;
  aplicarVelocidadeMotores();

  Serial.println("{\"status\": \"success\"}");
}

void aplicarVelocidadeMotores()
{
  // Aplicar velocidade diretamente
  servoEsquerdo.write(velocidade_esquerda);
  servoDireito.write(velocidade_direita);

  // Debug: mostrar valores aplicados
  Serial.printf("{\"motores\": {\"esquerdo\": %d, \"direito\": %d, \"L_FWD\": %d, \"L_BCK\": %d, \"R_FWD\": %d, \"R_BCK\": %d}}\n",
                velocidade_esquerda, velocidade_direita,
                LEFT_FORWARD_VAL, LEFT_BACKWARD_VAL, RIGHT_FORWARD_VAL, RIGHT_BACKWARD_VAL);
}

void enviarStatus()
{
  DynamicJsonDocument resposta(256);
  resposta["status"] = "online";
  resposta["mpu6050"] = mpu6050_presente;
  resposta["calibrado"] = calibrado;
  resposta["buzzer_pin"] = BUZZER_PIN;
  resposta["mpu6050_sda"] = MPU6050_SDA;
  resposta["mpu6050_scl"] = MPU6050_SCL;
  resposta["motores"]["esquerdo"] = velocidade_esquerda;
  resposta["motores"]["direito"] = velocidade_direita;

  if (mpu6050_presente)
  {
    resposta["sensores"]["temperatura"] = temperature;
  }

  serializeJson(resposta, Serial);
  Serial.println();
}