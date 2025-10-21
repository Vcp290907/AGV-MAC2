#define ENABLE_MIN_AND_MAX_CONSTRAINTS
#include "ServoEasing.hpp"
#include <ArduinoJson.h>

//ESP32 01 - Coisas de baixo

#define MOTOR_LEFT_PIN 14
#define MOTOR_RIGHT_PIN 15
#define BUZZER_PIN 27

ServoEasing servoEsquerdo;
ServoEasing servoDireito;

const int LEFT_DIR = +1;
const int RIGHT_DIR = -1;
int STOP_TRIM_LEFT = 0;
int STOP_TRIM_RIGHT = 0;
const int MIN_PULSE_US = 544;
const int MAX_PULSE_US = 2400;
int velocidade_esquerda = 0;
int velocidade_direita = 0;

String comando_recebido = "";
bool comando_completo = false;

void setup() {
  Serial.begin(115200);
  pinMode(BUZZER_PIN, OUTPUT);

  bool okL = servoEsquerdo.attach(MOTOR_LEFT_PIN, MIN_PULSE_US, MAX_PULSE_US, -100, 100);
  bool okR = servoDireito.attach(MOTOR_RIGHT_PIN, MIN_PULSE_US, MAX_PULSE_US, -100, 100);
  Serial.printf("Attach rodas: L=%d R=%d\n", okL, okR);
  servoEsquerdo.write(0);
  servoDireito.write(0);
  servoEsquerdo.setSpeed(300);
  servoDireito.setSpeed(300);
  pararMotores();

  beepBuzzer();
  Serial.println("{\"status\": \"ESP32 Rodas inicializado\"}");
}

void beepBuzzer() {
  const int freq = 4000;
  const int dur_ms = 200;
  int halfPeriodUs = 1000000 / (freq * 2);
  unsigned long end = millis() + dur_ms;
  while (millis() < end) {
    digitalWrite(BUZZER_PIN, HIGH);
    delayMicroseconds(halfPeriodUs);
    digitalWrite(BUZZER_PIN, LOW);
    delayMicroseconds(halfPeriodUs);
  }
  Serial.println("OK");
}

void loop() {
  processarComandosSeriais();
  servoEsquerdo.update();
  servoDireito.update();
  delay(10);
}

void processarComandosSeriais() {
  while (Serial.available()) {
    char ch = (char)Serial.read();
    if (ch == '\n' || ch == '\r' || ch == '}') {
      if (ch == '}') comando_recebido += '}';
      if (comando_recebido.length() > 0) comando_completo = true;
    } else {
      comando_recebido += ch;
      if (comando_recebido.length() > 512) {
        Serial.println("ERR: line too long");
        comando_recebido = "";
      }
    }
  }

  if (comando_completo) {
    String linha = comando_recebido; linha.trim();
    if (linha.startsWith("{")) processarComando(linha);
    else processarComandoTexto(linha);
    comando_recebido = "";
    comando_completo = false;
  }
}

void processarComando(String comando) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, comando);
  if (error) {
    Serial.println("{\"erro\": \"JSON inválido\"}");
    return;
  }

  String tipo_comando = doc["comando"];

  if (tipo_comando == "mover_frente" || tipo_comando == "mover_tras" || tipo_comando == "virar_esquerda" || tipo_comando == "virar_direita" || tipo_comando == "parar") {
    // Processa comandos de movimento localmente
    if (tipo_comando == "mover_frente") {
      int velocidade = doc["velocidade"] | 50;
      moverFrente(velocidade);
    } else if (tipo_comando == "mover_tras") {
      int velocidade = doc["velocidade"] | 50;
      moverTras(velocidade);
    } else if (tipo_comando == "virar_esquerda") {
      int velocidade = doc["velocidade"] | 25;
      virarEsquerda(velocidade);
    } else if (tipo_comando == "virar_direita") {
      int velocidade = doc["velocidade"] | 25;
      virarDireita(velocidade);
    } else if (tipo_comando == "parar") {
      pararMotores();
    }
  } else if (tipo_comando == "beep" || tipo_comando == "status") {
    if (tipo_comando == "beep") beepBuzzer();
    else if (tipo_comando == "status") Serial.println("{\"status\": \"rodas online\"}");
  } else {
    Serial.println("{\"erro\": \"Comando desconhecido para rodas\"}");
  }
}

void processarComandoTexto(String cmd) {
  // Apenas comandos de movimento, ignore outros
  Serial.println("ERR: comando texto não suportado para rodas");
}

// Funções de movimento (iguais ao original)
void moverFrente(int velocidade) {
  int s = constrain(velocidade, 0, 100);
  velocidade_esquerda = LEFT_DIR * s;
  velocidade_direita = RIGHT_DIR * s;
  aplicarVelocidadeMotores();
  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void moverTras(int velocidade) {
  int s = constrain(velocidade, 0, 100);
  velocidade_esquerda = LEFT_DIR * -s;
  velocidade_direita = RIGHT_DIR * -s;
  aplicarVelocidadeMotores();
  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void virarEsquerda(int velocidade) {
  int s = constrain(velocidade, 0, 100);
  velocidade_esquerda = LEFT_DIR * -s;
  velocidade_direita = RIGHT_DIR * +s;
  aplicarVelocidadeMotores();
  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void virarDireita(int velocidade) {
  int s = constrain(velocidade, 0, 100);
  velocidade_esquerda = LEFT_DIR * +s;
  velocidade_direita = RIGHT_DIR * -s;
  aplicarVelocidadeMotores();
  DynamicJsonDocument resposta(128);
  resposta["status"] = "success";
  resposta["velocidade"] = velocidade;
  serializeJson(resposta, Serial);
  Serial.println();
}

void pararMotores() {
  velocidade_esquerda = 0;
  velocidade_direita = 0;
  aplicarVelocidadeMotores();
  Serial.println("{\"status\": \"success\"}");
}

void aplicarVelocidadeMotores() {
  servoEsquerdo.startEaseTo(velocidade_esquerda + STOP_TRIM_LEFT);
  servoDireito.startEaseTo(velocidade_direita + STOP_TRIM_RIGHT);
  Serial.printf("{\"motores\": {\"esquerdo\": %d, \"direito\": %d}}\n", velocidade_esquerda, velocidade_direita);
}