#!/usr/bin/env python3
"""
Visualização em tempo real das câmeras chinesas CSI
Mostra ambas as câmeras lado a lado
"""

import cv2
import numpy as np
from agv_camera import AGVDualCamera
import time

def main():
    """Visualização em tempo real das câmeras"""
    print("📺 VISUALIZAÇÃO TEMPO REAL - CÂMERAS AGV")
    print("=========================================")

    # Inicializar sistema dual com resoluções diferentes
    # Câmera 1: 640x480 (mais rápida), Câmera 2: 1280x720 (mais detalhada)
    dual_camera = AGVDualCamera(width1=640, height1=480, width2=1280, height2=720)

    try:
        dual_camera.initialize()

        print("\n🎥 Iniciando visualização em tempo real...")
        print("Pressione 'q' para sair, 's' para salvar screenshot")

        # Loop de visualização
        while True:
            # Capturar frames
            frame1, frame2 = dual_camera.capture_frames()

            # Preparar display
            if frame1 is not None and frame2 is not None:
                # Redimensionar câmera 2 para combinar com câmera 1 (mesma altura)
                height1 = frame1.shape[0]
                frame2_resized = cv2.resize(frame2, (int(frame2.shape[1] * height1 / frame2.shape[0]), height1))

                # Combinar imagens lado a lado
                combined = np.hstack((frame1, frame2_resized))

                # Adicionar labels
                cv2.putText(combined, "Camera 1 (640x480)", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(combined, f"Camera 2 ({frame2.shape[1]}x{frame2.shape[0]})", (frame1.shape[1] + 10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Mostrar imagem combinada
                cv2.imshow("AGV Dual Camera - Tempo Real", combined)

            elif frame1 is not None:
                # Só câmera 1
                cv2.putText(frame1, "Camera 1 (Camera 2 offline)", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow("AGV Dual Camera - Tempo Real", frame1)

            elif frame2 is not None:
                # Só câmera 2
                cv2.putText(frame2, "Camera 2 (Camera 1 offline)", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow("AGV Dual Camera - Tempo Real", frame2)

            else:
                # Nenhuma câmera
                blank = np.zeros((480, 1280, 3), dtype=np.uint8)
                cv2.putText(blank, "Nenhuma camera detectada", (400, 240),
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                cv2.imshow("AGV Dual Camera - Tempo Real", blank)

            # Verificar teclas
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("\n🛑 Saindo da visualização...")
                break

            elif key == ord('s'):
                # Salvar screenshot
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"agv_dual_screenshot_{timestamp}.jpg"

                if frame1 is not None and frame2 is not None:
                    # Redimensionar câmera 2 para combinar com câmera 1
                    height1 = frame1.shape[0]
                    frame2_resized = cv2.resize(frame2, (int(frame2.shape[1] * height1 / frame2.shape[0]), height1))
                    combined = np.hstack((frame1, frame2_resized))
                    cv2.imwrite(filename, combined)
                    print(f"📷 Screenshot salvo: {filename} (Camera 1: 640x480, Camera 2: {frame2.shape[1]}x{frame2.shape[0]})")
                elif frame1 is not None:
                    cv2.imwrite(filename, frame1)
                    print(f"📷 Screenshot salvo: {filename} (Camera 1: 640x480)")
                elif frame2 is not None:
                    cv2.imwrite(filename, frame2)
                    print(f"📷 Screenshot salvo: {filename} (Camera 2: {frame2.shape[1]}x{frame2.shape[0]})")

            # Pequena pausa para não sobrecarregar CPU
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")

    except Exception as e:
        print(f"❌ Erro na visualização: {e}")

    finally:
        cv2.destroyAllWindows()
        dual_camera.release()
        print("✅ Visualização finalizada")

if __name__ == "__main__":
    main()