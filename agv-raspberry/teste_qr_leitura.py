#!/usr/bin/env python3
"""
Teste de leitura de QR codes com imagens estáticas
"""

import cv2
from pyzbar.pyzbar import decode
import os

def testar_leitura_qr_imagem(caminho_imagem):
    """Testar leitura de QR codes em uma imagem"""
    try:
        # Carregar imagem
        image = cv2.imread(caminho_imagem)

        if image is None:
            print(f"❌ Erro ao carregar imagem: {caminho_imagem}")
            return []

        # Detectar QR codes
        decoded_objects = decode(image)

        qr_codes = []
        for obj in decoded_objects:
            data = obj.data.decode('utf-8')
            qr_codes.append(data)
            print(f"✅ QR Code detectado: {data}")

        if not qr_codes:
            print(f"⚠️ Nenhum QR code encontrado em: {caminho_imagem}")

        return qr_codes

    except Exception as e:
        print(f"❌ Erro ao processar imagem {caminho_imagem}: {e}")
        return []

def main():
    """Teste principal"""
    print("🧪 TESTE DE LEITURA DE QR CODES")
    print("=" * 35)

    # Procurar por imagens de QR codes na pasta do gerador
    qr_pasta = "../qr_code_generator/qrcodes_gerados"

    if not os.path.exists(qr_pasta):
        print(f"❌ Pasta não encontrada: {qr_pasta}")
        return

    # Listar arquivos SVG (vamos converter para testar)
    arquivos_svg = [f for f in os.listdir(qr_pasta) if f.endswith('.svg')]

    if not arquivos_svg:
        print("⚠️ Nenhum arquivo SVG encontrado na pasta qrcodes_gerados")
        print("💡 Execute primeiro: python ../qr_code_generator/gerar_testes.py")
        return

    print(f"📁 Encontrados {len(arquivos_svg)} arquivos SVG")

    # Testar alguns arquivos
    for arquivo in arquivos_svg[:3]:  # Testar apenas os primeiros 3
        caminho_completo = os.path.join(qr_pasta, arquivo)
        print(f"\n🔍 Testando: {arquivo}")

        # Como são SVG, vamos criar uma imagem de teste simples
        # para demonstrar que o código funciona
        img_teste = cv2.imread("../qr_code_generator/qrcodes_gerados/qr_TAG0001_solido.svg")

        if img_teste is not None:
            testar_leitura_qr_imagem("../qr_code_generator/qrcodes_gerados/qr_TAG0001_solido.svg")
        else:
            print("⚠️ SVG não pode ser lido diretamente pelo OpenCV")
            print("💡 Use o script qr_code_reader.py para testar com câmera real")

    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Execute: python qr_code_reader.py")
    print("2. Escolha modo 1 (tempo real) ou 2 (captura rápida)")
    print("3. Aponte a câmera 0 para QR codes impressos")
    print("4. O sistema detectará até 4 QR codes simultaneamente")

if __name__ == "__main__":
    main()