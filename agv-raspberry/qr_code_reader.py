#!/usr/bin/env python3
"""
Leitor de QR Codes para AGV usando câmera CSI
Detecta e lê aproximadamente 4 QR codes por vez
"""

import cv2
from pyzbar.pyzbar import decode
from agv_camera import AGVCamera
import time
import numpy as np

class QRCodeReader:
    def __init__(self, camera_id=0, width=1280, height=720):
        """Inicializar leitor de QR codes"""
        self.camera = AGVCamera(camera_id=camera_id, width=width, height=height)
        self.qr_codes_detectados = []
        self.max_qr_codes = 4  # Limite aproximado de 4 QR codes

    def initialize(self):
        """Inicializar câmera"""
        return self.camera.initialize()

    def detectar_qr_codes(self, frame):
        """Detectar QR codes em um frame"""
        try:
            # Decodificar QR codes
            decoded_objects = decode(frame)

            qr_codes = []
            for obj in decoded_objects:
                # Obter dados do QR code
                data = obj.data.decode('utf-8')

                # Obter pontos do polígono
                points = obj.polygon
                if len(points) == 4:
                    pts = [(point.x, point.y) for point in points]

                    qr_codes.append({
                        'data': data,
                        'bbox': obj.rect,
                        'polygon': pts
                    })

            return qr_codes

        except Exception as e:
            print(f"❌ Erro ao detectar QR codes: {e}")
            return []

    def desenhar_qr_codes(self, frame, qr_codes):
        """Desenhar detecções de QR codes no frame"""
        for i, qr in enumerate(qr_codes):
            # Desenhar retângulo ao redor do QR code
            bbox = qr['bbox']
            cv2.rectangle(frame, (bbox.left, bbox.top),
                         (bbox.left + bbox.width, bbox.top + bbox.height),
                         (0, 255, 0), 3)

            # Desenhar pontos do polígono
            pts = np.array(qr['polygon'], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, (255, 0, 0), 2)

            # Adicionar texto com dados do QR code
            text = f"QR{i+1}: {qr['data'][:20]}{'...' if len(qr['data']) > 20 else ''}"
            cv2.putText(frame, text, (bbox.left, bbox.top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return frame

    def ler_qr_codes_tempo_real(self):
        """Ler QR codes em tempo real"""
        print("🔍 LEITOR DE QR CODES - TEMPO REAL")
        print("=" * 40)
        print(f"📷 Usando câmera {self.camera.camera_id}")
        print("🎯 Detectando até 4 QR codes simultaneamente")
        print("Pressione 'q' para sair, 'c' para capturar, 'r' para resetar")

        if not self.initialize():
            print("❌ Falha ao inicializar câmera")
            return

        qr_codes_unicos = set()  # Para evitar duplicatas

        try:
            while True:
                # Capturar frame
                frame = self.camera.capture_frame()

                if frame is None:
                    print("⚠️ Frame vazio, tentando novamente...")
                    time.sleep(0.1)
                    continue

                # Detectar QR codes
                qr_codes = self.detectar_qr_codes(frame)

                # Filtrar apenas os primeiros 4 QR codes
                qr_codes = qr_codes[:self.max_qr_codes]

                # Desenhar detecções
                frame_com_deteccoes = self.desenhar_qr_codes(frame.copy(), qr_codes)

                # Adicionar informações na tela
                info_text = f"QR Codes detectados: {len(qr_codes)}/{self.max_qr_codes}"
                cv2.putText(frame_com_deteccoes, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Mostrar códigos únicos detectados
                y_offset = 70
                for i, qr in enumerate(qr_codes):
                    if qr['data'] not in qr_codes_unicos:
                        qr_codes_unicos.add(qr['data'])
                        print(f"✅ QR Code {i+1} detectado: {qr['data']}")

                    text = f"QR{i+1}: {qr['data']}"
                    cv2.putText(frame_com_deteccoes, text, (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    y_offset += 30

                # Mostrar frame
                cv2.imshow("QR Code Reader - Camera 0", frame_com_deteccoes)

                # Verificar teclas
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    break
                elif key == ord('c'):
                    # Capturar screenshot
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"qr_capture_{timestamp}.jpg"
                    cv2.imwrite(filename, frame_com_deteccoes)
                    print(f"📸 Screenshot salvo: {filename}")
                elif key == ord('r'):
                    # Resetar detecções
                    qr_codes_unicos.clear()
                    print("🔄 Detecções resetadas")

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")

        finally:
            cv2.destroyAllWindows()
            self.camera.release()

            # Resumo final
            print(f"\n📊 RESUMO DA SESSÃO:")
            print(f"   QR codes únicos detectados: {len(qr_codes_unicos)}")
            for i, qr_data in enumerate(qr_codes_unicos, 1):
                print(f"   {i}. {qr_data}")

    def capturar_e_ler_qr_codes(self, num_frames=10):
        """Capturar múltiplos frames e ler QR codes"""
        print(f"📸 Capturando {num_frames} frames para detectar QR codes...")

        if not self.initialize():
            return []

        qr_codes_unicos = set()

        try:
            for i in range(num_frames):
                frame = self.camera.capture_frame()
                if frame is not None:
                    qr_codes = self.detectar_qr_codes(frame)

                    # Adicionar códigos únicos
                    for qr in qr_codes:
                        qr_codes_unicos.add(qr['data'])

                    print(f"Frame {i+1}/{num_frames}: {len(qr_codes)} QR codes detectados")

                time.sleep(0.2)  # Pequena pausa entre frames

        finally:
            self.camera.release()

        qr_list = list(qr_codes_unicos)
        print(f"\n✅ Detecção concluída! {len(qr_list)} QR codes únicos encontrados:")
        for i, qr_data in enumerate(qr_list, 1):
            print(f"   {i}. {qr_data}")

        return qr_list

def main():
    """Função principal"""
    print("🎯 LEITOR DE QR CODES PARA AGV")
    print("=" * 35)

    # Criar leitor para câmera 0
    qr_reader = QRCodeReader(camera_id=0, width=1280, height=720)

    print("\nEscolha o modo:")
    print("1. Leitura em tempo real (visualização)")
    print("2. Captura rápida (detecção automática)")

    try:
        modo = input("Modo (1 ou 2) [1]: ").strip()

        if modo == "2":
            # Modo de captura rápida
            num_frames = input("Número de frames para capturar [10]: ").strip()
            num_frames = int(num_frames) if num_frames.isdigit() else 10

            qr_codes = qr_reader.capturar_e_ler_qr_codes(num_frames)
            print(f"\n🎉 Total de QR codes detectados: {len(qr_codes)}")

        else:
            # Modo tempo real (padrão)
            qr_reader.ler_qr_codes_tempo_real()

    except KeyboardInterrupt:
        print("\n👋 Programa encerrado")

if __name__ == "__main__":
    main()