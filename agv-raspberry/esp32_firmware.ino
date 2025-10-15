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

// Pinos opcionais dos servos do braço (defina para -1 para desabilitar aquele eixo)
// Ajuste estes pinos conforme seu hardware. Foram escolhidos pinos genéricos que não conflitam com os já usados.
#ifndef ARM_GIRO_PIN
#define ARM_GIRO_PIN 2
#endif
#ifndef ARM_UM_PIN
#define ARM_UM_PIN 6
#endif
#ifndef ARM_DOIS_PIN
#define ARM_DOIS_PIN 7
#endif
#ifndef ARM_GARRA_PIN
#define ARM_GARRA_PIN 5
#endif
#ifndef ARM_TRES_PIN
#define ARM_TRES_PIN 8
#endif

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

// Servos do braço (opcionais)
Servo servoGiro;
Servo servoUm;
Servo servoDois;
Servo servoGarra;
Servo servoTres;

bool armGiroAtivo = false;
bool armUmAtivo = false;
bool armDoisAtivo = false;
bool armGarraAtivo = false;
bool armTresAtivo = false;

int velocidade_esquerda = 90; // 90 = parado
int velocidade_direita = 90;  // 90 = parado

// Posições atuais do braço (se não estiver conectado, valores são informativos)
int pos_giro = 30;
int pos_um = 65;
int pos_dois = 130;
int pos_garra = 73;
int pos_tres = 45;

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

  // Inicializar servos do braço, se pinos estiverem habilitados (>= 0)
  if (ARM_GIRO_PIN >= 0)
  {
    servoGiro.attach(ARM_GIRO_PIN);
    armGiroAtivo = true;
    servoGiro.write(pos_giro);
    servoGiro.setSpeed(60);
  }
  if (ARM_UM_PIN >= 0)
  {
    servoUm.attach(ARM_UM_PIN);
    armUmAtivo = true;
    servoUm.write(pos_um);
    servoUm.setSpeed(20);
    servoUm.setMinMaxConstraint(15, 165);
  }
  if (ARM_DOIS_PIN >= 0)
  {
    servoDois.attach(ARM_DOIS_PIN);
    armDoisAtivo = true;
    servoDois.write(pos_dois);
    servoDois.setSpeed(60);
    servoDois.setMinMaxConstraint(15, 165);
  }
  if (ARM_GARRA_PIN >= 0)
  {
    servoGarra.attach(ARM_GARRA_PIN);
    armGarraAtivo = true;
    servoGarra.write(pos_garra);
    servoGarra.setSpeed(80);
  }
  if (ARM_TRES_PIN >= 0)
  {
    servoTres.attach(ARM_TRES_PIN);
    armTresAtivo = true;
    servoTres.write(pos_tres);
    servoTres.setSpeed(60);
  }

  pararMotores();

  // Buzzer de inicialização
  beepBuzzer();

  // // Inicializar I2C com pinos customizados
  // Wire.begin(MPU6050_SDA, MPU6050_SCL);

  // // Inicializar MPU6050
  // inicializarMPU6050();

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
    // Se não for JSON válido, tentar interpretar como protocolo de texto simples
    if (!processarComandoTexto(comando))
    {
      Serial.println("{\"erro\": \"JSON inválido\"}");
    }
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

// ---- Protocolo de TEXTO para controle do braço e diagnósticos ----
// Formatos aceitos:
// - "MOVE giro um dois garra tres" -> define ângulos (0-180) dos 5 eixos (qualquer eixo desabilitado será ignorado)
// - "STATUS" -> imprime uma linha com: "giro:<v> um:<v> dois:<v> garra:<v> tres:<v>" e depois "OK"
// - "RUNSEQ" ou "X" -> executa uma sequência simples de teste (abre/fecha garra) e retorna "OK"
// - "BEEP" -> toque curto no buzzer e retorna "OK"
bool processarComandoTexto(String comando)
{
  comando.trim();
  if (comando.length() == 0)
    return false;

  // Extrair primeira palavra (comando)
  int sp = comando.indexOf(' ');
  String cmd = (sp >= 0) ? comando.substring(0, sp) : comando;
  String rest = (sp >= 0) ? comando.substring(sp + 1) : "";

  // Normalizar comando em maiúsculas para matching, sem afetar os valores
  cmd.toUpperCase();

  if (cmd == "STATUS")
  {
    imprimirStatusBraco();
    Serial.println("OK");
    return true;
  }
  else if (cmd == "BEEP")
  {
    beepBuzzer();
    return true;
  }
  else if (cmd == "RUNSEQ" || cmd == "X")
  {
    executarSequenciaTeste();
    Serial.println("OK");
    return true;
  }
  else if (cmd == "MOVE")
  {
    // Espera 5 inteiros no restante da linha
    int vals[5];
    int count = 0;

    // Tokenizar por espaços
    rest.trim();
    while (rest.length() > 0 && count < 5)
    {
      int p = rest.indexOf(' ');
      String tok = (p >= 0) ? rest.substring(0, p) : rest;
      if (p >= 0)
        rest = rest.substring(p + 1);
      else
        rest = "";
      tok.trim();
      if (tok.length() == 0)
        continue;
      vals[count] = tok.toInt();
      count++;
    }

    if (count != 5)
    {
      Serial.println("ERR BAD_MOVE");
      return true; // foi interpretado como texto, ainda que inválido
    }

    definirBraco(vals[0], vals[1], vals[2], vals[3], vals[4]);
    Serial.println("OK");
    return true;
  }

  return false; // não é um comando de texto reconhecido
}

void definirBraco(int giro, int um, int dois, int garra, int tres)
{
  // Limitar aos intervalos 0..180
  giro = constrain(giro, 0, 180);
  um = constrain(um, 0, 180);
  dois = constrain(dois, 0, 180);
  garra = constrain(garra, 0, 180);
  tres = constrain(tres, 0, 180);

  pos_giro = giro;
  pos_um = um;
  pos_dois = dois;
  pos_garra = garra;
  pos_tres = tres;

  if (armGiroAtivo)
    servoGiro.write(pos_giro);
  if (armUmAtivo)
    servoUm.write(pos_um);
  if (armDoisAtivo)
    servoDois.write(pos_dois);
  if (armGarraAtivo)
    servoGarra.write(pos_garra);
  if (armTresAtivo)
    servoTres.write(pos_tres);
}

void imprimirStatusBraco()
{
  Serial.print("giro:");
  Serial.print(pos_giro);
  Serial.print(" um:");
  Serial.print(pos_um);
  Serial.print(" dois:");
  Serial.print(pos_dois);
  Serial.print(" garra:");
  Serial.print(pos_garra);
  Serial.print(" tres:");
  Serial.println(pos_tres);
}

void executarSequenciaTeste()
{
  // Pequena sequência: abrir/fechar garra com movimentos suaves dos eixos principais se disponíveis
  int save_giro = pos_giro, save_um = pos_um, save_dois = pos_dois, save_garra = pos_garra, save_tres = pos_tres;

  // Abrir garra
  definirBraco(pos_giro, pos_um, pos_dois, 180, pos_tres);
  delay(300);
  // Leve ajuste
  definirBraco(90, 90, 90, 180, 90);
  delay(300);
  // Fechar garra
  definirBraco(90, 90, 90, 20, 90);
  delay(300);
  // Voltar ao estado salvo
  definirBraco(save_giro, save_um, save_dois, save_garra, save_tres);
  delay(200);
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
  // Para frente: Esquerda 180, Direita 0 (invertido novamente)
  velocidade_esquerda = map(velocidade, 0, 100, 90, 180);
  velocidade_direita = map(velocidade, 0, 100, 90, 0);

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void moverTras(int velocidade)
{
  // Para trás: Esquerda 0, Direita 180 (invertido novamente)
  velocidade_esquerda = map(velocidade, 0, 100, 90, 0);
  velocidade_direita = map(velocidade, 0, 100, 90, 180);

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void virarEsquerda(int velocidade)
{
  // Virar esquerda: Esquerda para trás (0), Direita para frente (0) para rotação anti-horária
  velocidade_esquerda = map(velocidade, 0, 100, 90, 0); // Esquerda: trás
  velocidade_direita = map(velocidade, 0, 100, 90, 0);  // Direita: frente

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void virarDireita(int velocidade)
{
  // Virar direita: Esquerda para frente (180), Direita para trás (180) para rotação horária
  velocidade_esquerda = map(velocidade, 0, 100, 90, 180); // Esquerda: frente
  velocidade_direita = map(velocidade, 0, 100, 90, 180);  // Direita: trás

  aplicarVelocidadeMotores();

  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void pararMotores()
{
  velocidade_esquerda = 90;
  velocidade_direita = 90;
  aplicarVelocidadeMotores();

  Serial.println("{\"status\": \"success\"}");
}

void aplicarVelocidadeMotores()
{
  // Aplicar velocidade diretamente
  servoEsquerdo.write(velocidade_esquerda);
  servoDireito.write(velocidade_direita);

  // Debug: mostrar valores aplicados
  Serial.printf("{\"motores\": {\"esquerdo\": %d, \"direito\": %d}}\n",
                velocidade_esquerda, velocidade_direita);
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