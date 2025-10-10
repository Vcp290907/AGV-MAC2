#!/usr/bin/env python3
"""
Gerador avançado de QR Codes com personalização
Versão estendida com mais opções
Salva automaticamente na pasta qrcodes_gerados/
"""

import os
import qrcode
from qrcode.image.svg import SvgImage, SvgPathImage, SvgFragmentImage

# Pasta para salvar os QR codes
PASTA_QR = "qrcodes_gerados"

def criar_pasta_se_nao_existir():
    """Cria a pasta de QR codes se não existir"""
    if not os.path.exists(PASTA_QR):
        os.makedirs(PASTA_QR)
        print(f"📁 Pasta criada: {PASTA_QR}/")

def gerar_qr_solido(texto, nome_arquivo="qr_code_solido.svg",
                    versao=1, correcao="L", tamanho_modulo=10, borda=4):
    """
    Gera QR code sólido (otimizado para CAD/CAM) mantendo a funcionalidade de leitura

    Args:
        texto (str): Texto para codificar
        nome_arquivo (str): Nome do arquivo de saída
        versao (int): Versão do QR (1-40, None para automático)
        correcao (str): Nível de correção ('L', 'M', 'Q', 'H')
        tamanho_modulo (int): Tamanho de cada módulo em pixels
        borda (int): Tamanho da borda em módulos
    """
    try:
        # Mapear correção
        correcao_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }

        # Criar QR Code
        qr = qrcode.QRCode(
            version=versao,
            error_correction=correcao_map.get(correcao.upper(), qrcode.constants.ERROR_CORRECT_L),
            box_size=tamanho_modulo,
            border=borda,
        )

        qr.add_data(texto)
        qr.make(fit=True)

        # Obter matriz do QR code
        matrix = qr.get_matrix()

        # Calcular dimensões totais
        tamanho_total = len(matrix) * tamanho_modulo
        view_box_size = len(matrix)

        # Criar SVG otimizado para CAD/CAM (mantém funcionalidade de leitura)
        svg_content = f'''<?xml version='1.0' encoding='UTF-8'?>
<svg width="{tamanho_total}mm" height="{tamanho_total}mm" version="1.1" viewBox="0 0 {view_box_size} {view_box_size}" xmlns="http://www.w3.org/2000/svg">
<rect width="{view_box_size}" height="{view_box_size}" fill="white"/>
<path d="'''

        # Gerar path otimizado mantendo cada módulo individual (preserva funcionalidade)
        path_commands = []

        for y, row in enumerate(matrix):
            for x, module in enumerate(row):
                if module:  # Módulo preto
                    path_commands.append(f"M{x},{y}h1v1h-1z")

        svg_content += "".join(path_commands) + '" fill="#000000" fill-rule="evenodd"/>\n</svg>'

        # Salvar arquivo
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        print(f"✅ QR Code sólido gerado!")
        print(f"📁 Arquivo: {nome_arquivo}")
        print(f"🔧 Configurações: Versão {qr.version}, Correção {correcao}, {tamanho_modulo}px/modulo")
        print(f"🎯 Tipo: Sólido (otimizado para CAD/CAM, mantém leitura)")

        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def gerar_qr_personalizado(texto, nome_arquivo="qr_code.svg",
                          versao=1, correcao="L", tamanho_modulo=10, borda=4,
                          formato_svg="path"):
    """
    Gera QR code personalizado com várias opções

    Args:
        texto (str): Texto para codificar
        nome_arquivo (str): Nome do arquivo de saída
        versao (int): Versão do QR (1-40, None para automático)
        correcao (str): Nível de correção ('L', 'M', 'Q', 'H')
        tamanho_modulo (int): Tamanho de cada módulo em pixels
        borda (int): Tamanho da borda em módulos
        formato_svg (str): Tipo de SVG ('path', 'fragment', 'image')
    """
    try:
        # Mapear correção
        correcao_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }

        # Escolher factory baseado no formato
        if formato_svg == "path":
            factory = SvgPathImage
        elif formato_svg == "fragment":
            factory = SvgFragmentImage
        else:
            factory = SvgImage

        # Criar QR Code
        qr = qrcode.QRCode(
            version=versao,
            error_correction=correcao_map.get(correcao.upper(), qrcode.constants.ERROR_CORRECT_L),
            box_size=tamanho_modulo,
            border=borda,
        )

        qr.add_data(texto)
        qr.make(fit=True)

        # Gerar imagem
        img = qr.make_image(image_factory=factory)
        img.save(nome_arquivo)

        print(f"✅ QR Code personalizado gerado!")
        print(f"📁 Arquivo: {nome_arquivo}")
        print(f"🔧 Configurações: Versão {qr.version}, Correção {correcao}, {tamanho_modulo}px/modulo")

        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def gerar_qr_visual_solido(texto, nome_arquivo="qr_code_visual_solido.svg",
                           versao=1, correcao="L", tamanho_modulo=10, borda=4):
    """
    Gera QR code com blocos VISUALMENTE conectados (prioriza aparência CAD/CAM sobre leitura perfeita)

    ⚠️ AVISO: Esta versão agrupa módulos adjacentes visualmente, o que pode afetar
    a robustez da leitura do QR code. Use apenas se a aparência visual for mais
    importante que a funcionalidade de leitura perfeita.

    Args:
        texto (str): Texto para codificar
        nome_arquivo (str): Nome do arquivo de saída
        versao (int): Versão do QR (1-40, None para automático)
        correcao (str): Nível de correção ('L', 'M', 'Q', 'H')
        tamanho_modulo (int): Tamanho de cada módulo em pixels
        borda (int): Tamanho da borda em módulos
    """
    try:
        # Mapear correção
        correcao_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }

        # Criar QR Code
        qr = qrcode.QRCode(
            version=versao,
            error_correction=correcao_map.get(correcao.upper(), qrcode.constants.ERROR_CORRECT_L),
            box_size=tamanho_modulo,
            border=borda,
        )

        qr.add_data(texto)
        qr.make(fit=True)

        # Obter matriz do QR code
        matrix = qr.get_matrix()

        # Calcular dimensões totais
        tamanho_total = len(matrix) * tamanho_modulo
        view_box_size = len(matrix)

        # Criar SVG com blocos conectados VISUALMENTE
        svg_content = f'''<?xml version='1.0' encoding='UTF-8'?>
<svg width="{tamanho_total}mm" height="{tamanho_total}mm" version="1.1" viewBox="0 0 {view_box_size} {view_box_size}" xmlns="http://www.w3.org/2000/svg">
<rect width="{view_box_size}" height="{view_box_size}" fill="white"/>
<path d="'''

        # Algoritmo para conectar módulos adjacentes VISUALMENTE
        visited = [[False for _ in row] for row in matrix]
        path_parts = []

        def flood_fill(x, y):
            """Flood fill para encontrar regiões conectadas de módulos pretos"""
            if x < 0 or y < 0 or x >= len(matrix[0]) or y >= len(matrix):
                return None
            if not matrix[y][x] or visited[y][x]:
                return None

            # Encontrar os limites da região conectada
            min_x, max_x = x, x
            min_y, max_y = y, y

            # Usar uma pilha para flood fill
            stack = [(x, y)]
            visited[y][x] = True

            while stack:
                cx, cy = stack.pop()

                # Expandir horizontalmente
                for nx in range(max(0, cx-1), min(len(matrix[0]), cx+2)):
                    if matrix[cy][nx] and not visited[cy][nx]:
                        visited[cy][nx] = True
                        stack.append((nx, cy))
                        min_x = min(min_x, nx)
                        max_x = max(max_x, nx)

                # Expandir verticalmente
                for ny in range(max(0, cy-1), min(len(matrix), cy+2)):
                    if matrix[ny][cx] and not visited[ny][cx]:
                        visited[ny][cx] = True
                        stack.append((cx, ny))
                        min_y = min(min_y, ny)
                        max_y = max(max_y, ny)

            # Verificar se todos os módulos na região estão pretos
            all_black = True
            for yy in range(min_y, max_y + 1):
                for xx in range(min_x, max_x + 1):
                    if not matrix[yy][xx]:
                        all_black = False
                        break
                if not all_black:
                    break

            # Mesmo que não seja retangular perfeito, criar um retângulo
            # Isso conecta visualmente os módulos, mesmo que altere o padrão
            width = max_x - min_x + 1
            height = max_y - min_y + 1
            return f"M{min_x},{min_y}h{width}v{height}h{-width}z"

        # Processar toda a matriz
        for y in range(len(matrix)):
            for x in range(len(matrix[0])):
                if matrix[y][x] and not visited[y][x]:
                    part = flood_fill(x, y)
                    if part:
                        path_parts.append(part)

        svg_content += "".join(path_parts) + '" fill="#000000" fill-rule="evenodd"/>\n</svg>'

        # Salvar arquivo
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        print(f"✅ QR Code visual sólido gerado!")
        print(f"📁 Arquivo: {nome_arquivo}")
        print(f"🔧 Configurações: Versão {qr.version}, Correção {correcao}, {tamanho_modulo}px/modulo")
        print(f"🎯 Tipo: Visual sólido (blocos conectados - pode afetar leitura)")
        print(f"⚠️  AVISO: Esta versão prioriza aparência visual sobre robustez de leitura!")

        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def menu_principal():
    """Menu interativo para configurações avançadas"""
    print("🎯 GERADOR AVANÇADO DE QR CODES")
    print("=" * 50)

    # Criar pasta na inicialização
    criar_pasta_se_nao_existir()

    while True:
        print("\n📝 Digite o texto para o QR Code:")
        print("(ou 'sair' para encerrar, 'menu' para opções)")

        texto = input("> ").strip()

        if texto.lower() in ['sair', 'exit', 'quit', 'q']:
            print("👋 Até logo!")
            break

        if texto.lower() == 'menu':
            mostrar_menu_opcoes()
            continue

        if not texto:
            print("⚠️  Texto vazio!")
            continue

        # Opções padrão
        versao = None  # Automático
        correcao = "L"
        tamanho_modulo = 10
        borda = 4
        tipo_qr = "padrao"  # "padrao" ou "solido"

        # Perguntar tipo de QR code
        print("\n🎨 Tipo de QR Code:")
        print("1. Padrão (módulos separados - compatível com leitores)")
        print("2. Otimizado (módulos individuais - melhor para CAD/CAM)")
        print("3. Visual Sólido (blocos conectados - aparência sólida ⚠️)")
        tipo_input = input("Escolha (1, 2 ou 3) [2]: ").strip()

        if tipo_input == "3":
            tipo_qr = "visual_solido"
        elif tipo_input == "1":
            tipo_qr = "padrao"
        else:
            tipo_qr = "solido"

        # Perguntar se quer personalizar
        print("\n🔧 Usar configurações padrão? (s/n)")
        if input("> ").lower().startswith('n'):
            print("\n🎨 CONFIGURAÇÕES PERSONALIZADAS:")
            print("Versão (1-40, Enter=automático):")
            try:
                v = input("> ").strip()
                versao = int(v) if v else None
            except:
                versao = None

            print("Correção de erro (L=7%, M=15%, Q=25%, H=30%) [L]:")
            corr = input("> ").strip().upper()
            if corr in ['L', 'M', 'Q', 'H']:
                correcao = corr

            print("Tamanho do módulo (pixels) [10]:")
            try:
                tm = input("> ").strip()
                tamanho_modulo = int(tm) if tm else 10
            except:
                tamanho_modulo = 10

            print("Tamanho da borda (módulos) [4]:")
            try:
                b = input("> ").strip()
                borda = int(b) if b else 4
            except:
                borda = 4

        # Gerar nome do arquivo na pasta específica
        sufixo = "_solido" if tipo_qr == "solido" else ""
        nome_base = texto[:25].replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace(".", "_")
        nome_arquivo = os.path.join(PASTA_QR, f"qr_{nome_base}{sufixo}.svg")

        contador = 1
        while os.path.exists(nome_arquivo):
            nome_arquivo = os.path.join(PASTA_QR, f"qr_{nome_base}{sufixo}_{contador}.svg")
            contador += 1

        # Gerar QR Code baseado no tipo
        if tipo_qr == "visual_solido":
            print("⚠️  ATENÇÃO: O tipo 'Visual Sólido' pode comprometer a leitura do QR code!")
            confirmar = input("Continuar mesmo assim? (s/n) [n]: ").lower().startswith('s')
            if confirmar:
                sucesso = gerar_qr_visual_solido(
                    texto, nome_arquivo, versao, correcao,
                    tamanho_modulo, borda
                )
            else:
                print("Cancelado. Usando tipo otimizado...")
                sucesso = gerar_qr_solido(
                    texto, nome_arquivo, versao, correcao,
                    tamanho_modulo, borda
                )
        elif tipo_qr == "solido":
            sucesso = gerar_qr_solido(
                texto, nome_arquivo, versao, correcao,
                tamanho_modulo, borda
            )
        else:
            sucesso = gerar_qr_personalizado(
                texto, nome_arquivo, versao, correcao,
                tamanho_modulo, borda, "path"
            )

        if sucesso:
            print(f"🎉 QR Code criado: {nome_arquivo}")
            print("💡 Dica: Abra o arquivo SVG em qualquer navegador ou editor vetorial")

        print("\n" + "=" * 50)

def mostrar_menu_opcoes():
    """Mostra menu de opções disponíveis"""
    print("\n🎨 OPÇÕES DISPONÍVEIS:")
    print("=" * 30)
    print("• Tipo de QR Code:")
    print("  - Padrão: Módulos separados (melhor para leitura por apps de celular)")
    print("  - Otimizado: Módulos individuais (melhor para CAD/CAM, mantém leitura)")
    print("  - Visual Sólido: Blocos conectados (aparência sólida ⚠️ pode afetar leitura)")
    print("• Versão: Controla tamanho do QR (1-40)")
    print("• Correção de erro:")
    print("  - L: 7% (padrão, menor)")
    print("  - M: 15% (bom equilíbrio)")
    print("  - Q: 25% (alta)")
    print("  - H: 30% (máxima, maior)")
    print("• Tamanho do módulo: Pixels por quadrado")
    print("• Borda: Margem em módulos")
    print("\n💡 Dicas:")
    print("• Use correção H para ambientes com interferência")
    print("• Versão automática funciona para a maioria dos casos")
    print("• SVG é vetorial - pode ser redimensionado sem perder qualidade")
    print("• Tipo sólido: Ideal para usinagem e CAD/CAM")
    print("\nPressione Enter para continuar...")
    input()

def main():
    """Ponto de entrada do programa"""
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrompido pelo usuário!")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()