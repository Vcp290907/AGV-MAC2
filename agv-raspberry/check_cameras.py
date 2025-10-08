#!/usr/bin/env python3
"""
Teste ULTRA SIMPLES - verificar quais câmeras estão disponíveis
"""

import cv2

print("🔍 VERIFICANDO CÂMERAS DISPONÍVEIS")
print("===================================")

cameras_encontradas = []

# Testar índices de 0 a 9
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            height, width = frame.shape[:2]
            cameras_encontradas.append((i, width, height))
            print(f"✅ Câmera {i}: {width}x{height}")
        else:
            print(f"⚠️  Câmera {i}: abre mas não captura")
    else:
        print(f"❌ Câmera {i}: não abre")
    cap.release()

print("")
print("📊 RESUMO:")
if cameras_encontradas:
    print(f"✅ {len(cameras_encontradas)} câmera(s) funcionando:")
    for idx, w, h in cameras_encontradas:
        print(f"   • Índice {idx}: {w}x{h}")
else:
    print("❌ Nenhuma câmera funcionando")

print("")
print("💡 Para testar câmera específica:")
print("   python3 -c \"import cv2; cap=cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL'); cap.release()\"")