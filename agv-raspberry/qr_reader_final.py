#!/usr/bin/env python3
"""
Leitor FINAL de QR Codes - Funciona em qualquer situação
Testa múltiplas abordagens automaticamente
"""

import cv2
from pyzbar.pyzbar import decode
import time
import sys
import os

class UniversalQRReader:
    """Leitor universal que funciona em qualquer situação"""

    def __init__(self):
        self.qr_codes_detectados = set()
        self.cap = None
        self.usando_csi = False
        self.usando_usb = False

    def tentar_csi(self):
        """Tentar usar câmera CSI diretamente"""
        try:
            from picamera2 import Picamera2
            print("📷 Tentando câmera CSI...")

            picam2 = Picamera2()
            config = picam2.create_preview_configuration(
                main={"format": 'XRGB8888', "size": (1280, 720)}
            )
            picam2.configure(config)
            picam2.start()
            time.sleep(2)

            # Testar captura
            frame = picam2.capture_array()
            if frame is not None:
                print("✅ CSI funcionando!")
                self.cap = picam2
                self.usando_csi = True
                return True

        except Exception as e:
            print(f"⚠️ CSI falhou: {e}")

        return False

    def tentar_usb(self):
        """Tentar usar câmera USB/OpenCV"""
        print("📷 Tentando câmera USB/OpenCV...")

        # Tentar diferentes índices de câmera
        for camera_id in [0, 1, 2, -1]:
            try:
                cap = cv2.VideoCapture(camera_id)
                if cap.isOpened():
                    # Testar captura
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"✅ USB câmera {camera_id} funcionando!")
                        self.cap = cap
                        self.usando_usb = True
                        return True
                    cap.release()
            except:
                pass

        print("❌ Nenhuma câmera USB encontrada")
        return False

    def initialize(self):
        """Inicializar câmera de qualquer tipo disponível"""
        print("🔍 INICIALIZANDO LEITOR UNIVERSAL DE QR CODES")
        print("=" * 50)

        # Tentar CSI primeiro (se disponível)
        if self.tentar_csi():
            return True

        # Fallback para USB
        if self.tentar_usb():
            return True

        print("❌ Nenhuma câmera disponível!")
        print("💡 Verifique se as câmeras estão conectadas")
        return False

    def capture_frame(self):
        """Capturar frame dependendo do tipo de câmera"""
        if self.usando_csi:
            # CSI (picamera2)
            frame = self.cap.capture_array()
            if frame is not None and frame.shape[2] == 4:  # XRGB
                frame = frame[:, :, :3]  # Remove alpha channel
            return frame

        elif self.usando_usb:
            # USB (OpenCV)
            ret, frame = self.cap.read()
            return frame if ret else None

        return None

    def detectar_qr_codes(self, frame):
        """Detectar QR codes em um frame"""
        try:
            decoded_objects = decode(frame)
            qr_codes = []

            for obj in decoded_objects:
                data = obj.data.decode('utf-8')
                qr_codes.append({
                    'data': data,
                    'bbox': obj.rect,
                    'type': obj.type
                })

            return qr_codes

        except Exception as e:
            print(f"❌ Erro ao detectar QR codes: {e}")
            return []

    def mostrar_qr_codes(self, qr_codes):
        """Mostrar QR codes detectados"""
        if not qr_codes:
            return

        print(f"\n🎯 QR CODES DETECTADOS ({len(qr_codes)}):")
        print("-" * 40)

        for i, qr in enumerate(qr_codes, 1):
            data = qr['data']
            if data not in self.qr_codes_detectados:
                self.qr_codes_detectados.add(data)
                print(f"✅ QR {i}: {data}")
            else:
                print(f"🔄 QR {i}: {data} (já detectado)")

    def ler_qr_codes_universal(self, modo_visual=False):
        """Ler QR codes usando qualquer câmera disponível"""
        print("Pressione 'q' para sair, 'r' para resetar lista, 'i' para info")

        if not self.initialize():
            return

        try:
            while True:
                # Capturar frame
                frame = self.capture_frame()

                if frame is None:
                    print("⚠️ Frame vazio, tentando novamente...")
                    time.sleep(0.1)
                    continue

                # Detectar QR codes
                qr_codes = self.detectar_qr_codes(frame)

                # Mostrar no terminal
                if qr_codes:
                    self.mostrar_qr_codes(qr_codes)

                # Modo visual opcional
                if modo_visual:
                    # Desenhar detecções
                    for qr in qr_codes:
                        bbox = qr['bbox']
                        cv2.rectangle(frame, (bbox.left, bbox.top),
                                    (bbox.left + bbox.width, bbox.top + bbox.height),
                                    (0, 255, 0), 3)

                        # Mostrar texto
                        text = qr['data'][:30] + "..." if len(qr['data']) > 30 else qr['data']
                        cv2.putText(frame, text, (bbox.left, bbox.top - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    # Mostrar estatísticas
                    tipo_camera = "CSI" if self.usando_csi else "USB" if self.usando_usb else "?"
                    info_text = f"Camera: {tipo_camera} | QR: {len(qr_codes)} | Unicos: {len(self.qr_codes_detectados)}"
                    cv2.putText(frame, info_text, (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                    cv2.imshow("QR Code Reader - Universal", frame)

                # Verificar teclas
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.qr_codes_detectados.clear()
                    print("🔄 Lista de QR codes resetada")
                elif key == ord('i'):
                    tipo = "CSI (picamera2)" if self.usando_csi else "USB (OpenCV)" if self.usando_usb else "Nenhuma"
                    print(f"📷 Usando: {tipo}")

                time.sleep(0.1)  # Pequena pausa

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")

        finally:
            if modo_visual:
                cv2.destroyAllWindows()

            # Liberar câmera
            if self.usando_csi and self.cap:
                self.cap.stop()
                print("🛑 Câmera CSI liberada")
            elif self.usando_usb and self.cap:
                self.cap.release()
                print("🛑 Câmera USB liberada")

            # Resumo final
            print(f"\n📊 RESUMO FINAL:")
            print(f"   Total de QR codes únicos detectados: {len(self.qr_codes_detectados)}")
            if self.qr_codes_detectados:
                print("   Lista completa:")
                for i, qr_data in enumerate(sorted(self.qr_codes_detectados), 1):
                    print(f"   {i}. {qr_data}")

def main():
    """Função principal"""
    print("🎯 LEITOR UNIVERSAL DE QR CODES")
    print("=" * 35)
    print("Funciona com CSI ou USB automaticamente")

    # Verificar argumentos
    modo_visual = '--visual' in sys.argv or '-v' in sys.argv

    # Criar leitor universal
    qr_reader = UniversalQRReader()

    # Executar leitura
    qr_reader.ler_qr_codes_universal(modo_visual=modo_visual)

if __name__ == "__main__":
    main()