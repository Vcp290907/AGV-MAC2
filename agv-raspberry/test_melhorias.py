#!/usr/bin/env python3
"""
Teste rápido das melhorias na navegação
"""

from line_following_navigation import LineFollowingNavigation
import time

def test_melhorias():
    print("TESTANDO MELHORIAS NA NAVEGAÇÃO")
    print("=" * 40)

    # Criar navegação com feedback visual
    nav = LineFollowingNavigation(visual_feedback=True)

    # Inicializar
    if not nav.initialize():
        print("❌ Falha na inicialização")
        return

    print("✅ Inicialização OK")

    # Verificar parâmetros de velocidade
    print(f"Velocidade base: {nav.speed_base} (era 55)")
    print(f"Velocidade mínima: {nav.speed_min} (era 25)")
    print(f"Velocidade máxima: {nav.speed_max} (era 75)")

    # Verificar campos de subcorredor
    print(f"Subcorredor atual: {nav.current_subcorredor}")
    print(f"Status subcorredor: {nav.status_info['subcorredor']}")

    # Teste rápido de detecção (sem movimento)
    print("\nTestando detecção de linha...")
    try:
        for i in range(3):
            line_info = nav.line_detector.process_frame()
            if line_info and line_info['detected']:
                print(f"✅ Linha detectada - Centro: {line_info['center']}, Largura: {line_info['width']}")
                break
            else:
                print(f"⚠️ Tentativa {i+1}: Linha não detectada")
            time.sleep(0.5)
    except Exception as e:
        print(f"Erro no teste de detecção: {e}")

    # Limpar
    nav.cleanup()
    print("✅ Teste concluído")

if __name__ == "__main__":
    test_melhorias()