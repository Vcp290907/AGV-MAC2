/*
 * Controle de Servo Motores AGV - ESP32
 * Recebe comandos via Serial do Raspberry Pi
 * Protocolo: JSON via Serial (115200 baud)
 *
 * Comandos suportados:
 * {"command": "ping"} - Teste de conectividade
 * {"command": "move", "direction": "forward", "duration": 1.0}
 * {"command": "move", "direction": "backward", "duration": 1.0}
 * {"command": "stop"}
 * {"command": "status"}
 *
 * Respostas:
 * {"status": "ok"} - Comando executado com sucesso
 * {"status": "error", "message": "descrição do erro"}
 *
 * Servo esquerdo (GPIO 1): 0°=frente, 180°=trás, 90°=parado
 * Servo direito (GPIO 3): 180°=frente, 0°=trás, 90°=parado
 */

#include <ArduinoJson.h>
#include <ESP32Servo.h>

// Definição dos servos
Servo motorEsq;  // Servo esquerdo
Servo motorDir;  // Servo direito

// Pinos dos servos
#define PIN_SERVO_ESQ  1   // Pino GPIO 1 para servo esquerdo
#define PIN_SERVO_DIR  3   // Pino GPIO 3 para servo direito

// LEDs indicadores
#define LED_STATUS     2   // LED onboard ESP32

// Configurações
#define SERIAL_BAUD    115200

// Posições dos servos (ângulos em graus)
#define SERVO_PARADO     90   // Posição neutra (parado)
#define SERVO_FRENTE     0    // Gira para frente (0 graus)
#define SERVO_TRAS       180  // Gira para trás (180 graus)

// Variáveis globais
bool motorsEnabled = true;

// Buffer para dados JSON
const size_t JSON_BUFFER_SIZE = 256;
char jsonBuffer[JSON_BUFFER_SIZE];
int bufferIndex = 0;

void setup() {
  // Inicializar Serial
  Serial.begin(SERIAL_BAUD);
  delay(1000);  // Aguardar estabilização

  // Anexar servos aos pinos
  motorEsq.attach(PIN_SERVO_ESQ);
  motorDir.attach(PIN_SERVO_DIR);

  // Configurar LED de status
  pinMode(LED_STATUS, OUTPUT);

  // Parar servos inicialmente (posição neutra)
  stopMotors();

  // Piscar LED para indicar inicialização
  blinkLED(3, 200);

  Serial.println("{\"status\": \"ready\", \"message\": \"ESP32 Servo Control Ready\"}");
}

void loop() {
  // Verificar se há dados na serial
  while (Serial.available() > 0) {
    char receivedChar = Serial.read();

    // Verificar fim da mensagem (newline)
    if (receivedChar == '\n') {
      jsonBuffer[bufferIndex] = '\0';  // Null terminate

      // Processar comando JSON
      processCommand(jsonBuffer);

      // Reset buffer
      bufferIndex = 0;
    } else if (bufferIndex < JSON_BUFFER_SIZE - 1) {
      jsonBuffer[bufferIndex++] = receivedChar;
    } else {
      // Buffer overflow - reset
      bufferIndex = 0;
      sendError("Buffer overflow");
    }
  }

  // Pequena pausa para não sobrecarregar CPU
  delay(10);
}

void processCommand(const char* jsonString) {
  // Parse JSON
  DynamicJsonDocument doc(256);

  DeserializationError error = deserializeJson(doc, jsonString);

  if (error) {
    String errorMsg = "JSON parse error: " + String(error.c_str());
    sendError(errorMsg.c_str());
    return;
  }

  // Verificar se tem campo "command"
  if (!doc.containsKey("command")) {
    sendError("Missing 'command' field");
    return;
  }

  String command = doc["command"];

  // Processar comando
  if (command == "ping") {
    // Comando de teste
    sendResponse("ok", "pong");

  } else if (command == "move") {
    // Comando de movimento
    handleMoveCommand(doc);

  } else if (command == "stop") {
    // Parar motores
    stopMotors();
    sendResponse("success", "Servos stopped");

  } else if (command == "set_speed") {
    // Servo motors don't have variable speed control
    // This command is kept for compatibility but has no effect
    sendResponse("success", "Speed control not available for servo motors");

  } else if (command == "status") {
    // Retornar status
    sendStatus();

  } else {
    String errorMsg = "Unknown command: " + command;
    sendError(errorMsg.c_str());
  }
}

void handleMoveCommand(DynamicJsonDocument& doc) {
  if (!doc.containsKey("direction")) {
    sendError("Missing 'direction' field");
    return;
  }

  String direction = doc["direction"];
  float duration = doc["duration"] | 1.0;  // Padrão 1 segundo

  if (direction == "forward") {
    moveForward(duration);
    String message = "Moved forward for " + String(duration) + "s";
    sendResponse("success", message.c_str());

  } else if (direction == "backward") {
    moveBackward(duration);
    String message = "Moved backward for " + String(duration) + "s";
    sendResponse("success", message.c_str());

  } else {
    String errorMsg = "Invalid direction: " + direction;
    sendError(errorMsg.c_str());
  }
}

void moveForward(float duration) {
  if (!motorsEnabled) return;

  // Configurar direção: frente
  // motorEsq.write(0) - Gira para frente
  // motorDir.write(180) - Gira para frente (invertido)
  motorEsq.write(SERVO_FRENTE);
  motorDir.write(SERVO_TRAS);

  // Aguardar duração
  delay(duration * 1000);

  // Parar servos
  stopMotors();
}

void moveBackward(float duration) {
  if (!motorsEnabled) return;

  // Configurar direção: trás
  // motorEsq.write(180) - Gira para trás
  // motorDir.write(0) - Gira para trás (invertido)
  motorEsq.write(SERVO_TRAS);
  motorDir.write(SERVO_FRENTE);

  // Aguardar duração
  delay(duration * 1000);

  // Parar servos
  stopMotors();
}

void stopMotors() {
  // Posição neutra para ambos os servos (parado)
  motorEsq.write(SERVO_PARADO);
  motorDir.write(SERVO_PARADO);
}

void sendResponse(const char* status, const char* message) {
  DynamicJsonDocument response(128);
  response["status"] = status;
  response["message"] = message;
  response["timestamp"] = millis();

  serializeJson(response, Serial);
  Serial.println();
}

void sendError(const String& message) {
  DynamicJsonDocument response(128);
  response["status"] = "error";
  response["message"] = message;
  response["timestamp"] = millis();

  serializeJson(response, Serial);
  Serial.println();
}

void sendStatus() {
  DynamicJsonDocument response(256);
  response["status"] = "ok";
  response["motor_type"] = "servo";
  response["motors_enabled"] = motorsEnabled;
  response["uptime_ms"] = millis();

  // Status dos servos
  response["servos"]["left_angle"] = motorEsq.read();
  response["servos"]["right_angle"] = motorDir.read();
  response["servos"]["left_attached"] = motorEsq.attached();
  response["servos"]["right_attached"] = motorDir.attached();

  serializeJson(response, Serial);
  Serial.println();
}

void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_STATUS, HIGH);
    delay(delayMs);
    digitalWrite(LED_STATUS, LOW);
    delay(delayMs);
  }
}