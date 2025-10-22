#define ENABLE_MIN_AND_MAX_CONSTRAINTS
#include "ServoEasing.hpp"
#include <ArduinoJson.h>

//ESP32 02 - Coisas de cima

#define PIN_SERVO_GIRO_GARRA 9
#define PIN_SERVO_SERVO_UM 8
#define PIN_SERVO_SERVO_DOIS 7
#define PIN_SERVO_TRES 6
#define PIN_SERVO_GARRA 5

ServoEasing motorGiroGarra;
ServoEasing motorUm;
ServoEasing motorDois;
ServoEasing motorGarra;
ServoEasing motorTres;

String comando_recebido = "";
bool comando_completo = false;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  motorGarra.attach(PIN_SERVO_GARRA);
  motorDois.attach(PIN_SERVO_SERVO_DOIS);
  motorUm.attach(PIN_SERVO_SERVO_UM);
  motorGiroGarra.attach(PIN_SERVO_GIRO_GARRA);
  motorTres.attach(PIN_SERVO_TRES);

  motorGiroGarra.setMinMaxConstraint(0, 180);
  motorUm.setMinMaxConstraint(15, 165);
  motorDois.setMinMaxConstraint(15, 165);
  motorGarra.setMinMaxConstraint(0, 180);
  motorTres.setMinMaxConstraint(30, 110);

  motorGiroGarra.setEasingType(EASE_CUBIC_IN_OUT);
  motorUm.setEasingType(EASE_QUARTIC_IN_OUT);
  motorDois.setEasingType(EASE_CUBIC_IN_OUT);
  motorGarra.setEasingType(EASE_CUBIC_IN_OUT);
  motorTres.setEasingType(EASE_CUBIC_IN_OUT);

  motorGiroGarra.setSpeed(60);
  motorUm.setSpeed(10);
  motorDois.setSpeed(60);
  motorGarra.setSpeed(80);
  motorTres.setSpeed(60);

  Serial.println("{\"status\": \"ESP32 Garra inicializado\"}");
  ligarGarra();
}

void ligarGarra() {
  motorGarra.easeTo(35);
  delay(300);
  motorTres.easeTo(90);
  motorDois.easeTo(115);
  delay(300);
  motorUm.easeTo(60);
  delay(300);
  motorGiroGarra.easeTo(30);
  delay(300);
}

void loop() {
  processarComandosSeriais();
  motorGiroGarra.update();
  motorUm.update();
  motorDois.update();
  motorGarra.update();
  motorTres.update();
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

  if (tipo_comando == "move_servos") {
    int a = -1, b = -1, c = -1, d = -1, e = -1000;
    if (doc.containsKey("a") && doc.containsKey("b") && doc.containsKey("c") && doc.containsKey("d")) {
      a = doc["a"];
      b = doc["b"];
      c = doc["c"];
      d = doc["d"];
      if (doc.containsKey("e")) e = doc["e"];
    }
    if (a >= 0) motorGiroGarra.easeTo(a);
    if (b >= 0) motorUm.easeTo(b);
    if (c >= 0) motorDois.easeTo(c);
    if (d >= 0) motorGarra.easeTo(d);
    if (e != -1000) motorTres.easeTo(e);
    Serial.println("{\"status\": \"success\"}");
  } else if (tipo_comando == "beep") {
    Serial.println("{\"status\": \"beep not available\"}");
  } else if (tipo_comando == "status") {
    Serial.println("{\"status\": \"garra online\"}");
  } else {
    Serial.println("{\"erro\": \"Comando desconhecido\"}");
  }
}

void processarComandoTexto(String cmd) {
  cmd.trim();
  if (cmd.startsWith("MOVE ")) {
    int a, b, c, d, e = 0;
    int parsed = sscanf(cmd.c_str(), "MOVE %d %d %d %d %d", &a, &b, &c, &d, &e);
    if (parsed >= 4) {
      motorGiroGarra.easeTo(a);
      motorUm.easeTo(b);
      motorDois.easeTo(c);
      motorGarra.easeTo(d);
      if (parsed == 5) motorTres.easeTo(e);
      Serial.println("OK");
    } else {
      Serial.println("ERR: formato MOVE inválido");
    }
  } else {
    Serial.println("ERR: comando desconhecido");
  }
}