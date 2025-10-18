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

#define ENABLE_MIN_AND_MAX_CONSTRAINTS
#include "ServoEasing.hpp"
#include <Wire.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// Configurações de pinos
#define MOTOR_LEFT_PIN 1  // GPIO 1 - Servo Motor Esquerdo
#define MOTOR_RIGHT_PIN 3 // GPIO 3 - Servo Motor Direito
#define BUZZER_PIN 4      // GPIO 4 - Buzzer

#define PIN_SERVO_GIRO_GARRA 2
#define PIN_SERVO_SERVO_UM 6
#define PIN_SERVO_SERVO_DOIS 7
#define PIN_SERVO_TRES 8
#define PIN_SERVO_GARRA 5

// Controle de motores com Servo
Servo servoEsquerdo;
Servo servoDireito;

// Controle de motores com ServoEasing
ServoEasing motorGiroGarra;
ServoEasing motorUm;
ServoEasing motorDois;
ServoEasing motorGarra;
ServoEasing motorTres;

// Constantes de servo (contínuo): 90=parado, >90 um sentido, <90 outro
const int SERVO_NEUTRO = 90;
const int LEFT_FORWARD_VAL = 180;   // esquerda indo para frente
const int LEFT_BACKWARD_VAL = 0;    // esquerda indo para trás
const int RIGHT_FORWARD_VAL = 0;    // direita indo para frente (servos espelhados ao contrário)
const int RIGHT_BACKWARD_VAL = 180; // direita indo para trás (servos espelhados ao contrário)

int velocidade_esquerda = SERVO_NEUTRO; // 90 = parado
int velocidade_direita = SERVO_NEUTRO;  // 90 = parado

// Comunicação serial
String comando_recebido = "";
bool comando_completo = false;

// Forward declaration para comandos de texto (não-JSON)
void processarComandoTexto(String cmd);

// Estado de calibração (usado em enviarStatus)
bool calibrado = false;

void setup()
{

  Serial.begin(115200);
  while (!Serial)
  {
    delay(10);
  }

  pinMode(BUZZER_PIN, OUTPUT);

  // Inicializar servos
  servoEsquerdo.attach(MOTOR_LEFT_PIN);
  servoDireito.attach(MOTOR_RIGHT_PIN);

  pararMotores();

  motorGarra.attach(PIN_SERVO_GARRA);
  motorTres.attach(PIN_SERVO_TRES);
  motorDois.attach(PIN_SERVO_SERVO_DOIS);
  motorUm.attach(PIN_SERVO_SERVO_UM);
  motorGiroGarra.attach(PIN_SERVO_GIRO_GARRA);

  motorUm.setMinMaxConstraint(15, 165);
  motorDois.setMinMaxConstraint(15, 165);
  motorGarra.setMinMaxConstraint(30, 73);

  motorGiroGarra.setEasingType(EASE_CUBIC_IN_OUT);
  motorUm.setEasingType(EASE_QUARTIC_IN_OUT);
  motorDois.setEasingType(EASE_CUBIC_IN_OUT);
  motorGarra.setEasingType(EASE_CUBIC_IN_OUT);
  motorTres.setEasingType(EASE_CUBIC_IN_OUT);

  motorGiroGarra.setSpeed(60);
  motorUm.setSpeed(10);
  motorDois.setSpeed(60);
  motorTres.setSpeed(60);
  motorGarra.setSpeed(80);

  motorGarra.easeTo(73);
  motorTres.easeTo(90);
  motorDois.easeTo(90);
  motorUm.easeTo(50);
  motorGiroGarra.easeTo(30);
  delay(3000);

  beepBuzzer();

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

void processarComandosSeriais()
{
  while (Serial.available())
  {
    char caractere = Serial.read();

    if (caractere == '\n' || caractere == '\r')
    {
      if (comando_recebido.length() > 0)
      {
        comando_completo = true;
      }
    }
    else
    {
      comando_recebido += caractere;
      // proteção contra linhas muito longas
      if (comando_recebido.length() > 200)
      {
        Serial.println("ERR: line too long");
        comando_recebido = "";
      }
    }
  }

  if (comando_completo)
  {
    String linha = comando_recebido;
    linha.trim();

    // Se começar com '{', tratar como JSON; senão, tratar como comando de texto
    if (linha.startsWith("{"))
    {
      processarComando(linha);
    }
    else if (linha.length() > 0)
    {
      processarComandoTexto(linha);
    }

    comando_recebido = "";
    comando_completo = false;
  }
}

void processarComando(String comando)
{
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, comando);

  if (error)
  {
    Serial.println("{\"erro\": \"JSON inválido\"}");
    return;
  }

  String tipo_comando = doc["comando"];

  if (tipo_comando == "mover_frente")
  {
    int velocidade = doc["velocidade"] | 50; // Velocidade padrão menor
    moverFrente(velocidade)
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
  else if (tipo_comando == "move_text")
  {
    // Encaminha uma linha de texto (ex: "MOVE a b c d [e]") para o parser textual
    String linha = doc["linha"] | "";
    if (linha.length() == 0)
    {
      Serial.println("{\"erro\": \"linha vazia em move_text\"}");
    }
    else
    {
      processarComandoTexto(linha);
    }
  }
  else if (tipo_comando == "move_servos")
  {
    // Move os 4 ou 5 servos (giro, um, dois, garra [, tres]) via JSON
    // Formatos aceitos:
    // 1) {"comando":"move_servos", "angles":[a,b,c,d]}  // [e] opcional
    // 2) {"comando":"move_servos", "a":..., "b":..., "c":..., "d":..., "e":...}

    int a = -1, b = -1, c = -1, d = -1, e = -1000;

    if (doc.containsKey("angles"))
    {
      JsonArray arr = doc["angles"].as<JsonArray>();
      if (arr.size() < 4)
      {
        Serial.println("{\"erro\": \"angles requer ao menos 4 valores\"}");
        return;
      }
      a = arr[0];
      b = arr[1];
      c = arr[2];
      d = arr[3];
      if (arr.size() >= 5)
        e = arr[4];
    }
    else if (doc.containsKey("a") && doc.containsKey("b") && doc.containsKey("c") && doc.containsKey("d"))
    {
      a = doc["a"].as<int>();
      b = doc["b"].as<int>();
      c = doc["c"].as<int>();
      d = doc["d"].as<int>();
      if (doc.containsKey("e"))
        e = doc["e"].as<int>();
    }
    else
    {
      Serial.println("{\"erro\": \"parametros ausentes: use angles[4-5] ou campos a,b,c,d[,e]\"}");
      return;
    }

    // Executa movimentos
    motorGiroGarra.easeTo(a);
    motorUm.easeTo(b);
    motorDois.easeTo(c);
    motorGarra.easeTo(d);
    if (e != -1000)
    {
      motorTres.easeTo(e);
    }

    DynamicJsonDocument resposta(128);
    resposta["status"] = "success";
    serializeJson(resposta, Serial);
    Serial.println();
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

// Processamento de comandos de texto (apenas MOVE)
void processarComandoTexto(String cmd)
{
  cmd.trim();
  if (cmd.length() == 0)
    return;

  String up = cmd;
  up.toUpperCase();

  if (up.startsWith("MOVE "))
  {
    // Formato: MOVE a b c d [e]  -> (giro, um, dois, garra [, tres])
    int a = 0, b = 0, c = 0, d = 0, e = 0;
    int parsed = sscanf(cmd.c_str(), "MOVE %d %d %d %d %d", &a, &b, &c, &d, &e);
    if (parsed == 5 || parsed == 4)
    {
      motorGiroGarra.easeTo(a);
      motorUm.easeTo(b);
      motorDois.easeTo(c);
      motorGarra.easeTo(d);
      if (parsed == 5)
      {
        motorTres.easeTo(e);
      }
      Serial.println("OK");
    }
    else
    {
      Serial.println("ERR: expected 'MOVE a b c d [e]'");
    }
    return;
  }

  Serial.println("ERR: unknown command");
}

void enviarStatus()
{
  DynamicJsonDocument resposta(256);
  resposta["status"] = "online";
  resposta["calibrado"] = calibrado;
  resposta["buzzer_pin"] = BUZZER_PIN;
  resposta["motores"]["esquerdo"] = velocidade_esquerda;
  resposta["motores"]["direito"] = velocidade_direita;

  serializeJson(resposta, Serial);
  Serial.println();
}