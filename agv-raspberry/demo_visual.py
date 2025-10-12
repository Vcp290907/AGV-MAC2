#!/usr/bin/env python3
"""
Demonstração do feedback visual no Windows
Mostra como o sistema de visão computacional funciona
"""

import sys
import os
import time
sys.path.append(os.path.dirname(__file__))

from line_following_navigation import LineFollowingNavigation

def demo_visual_feedback():
    """Demonstrar o feedback visual"""
    print("🎥 DEMONSTRAÇÃO DO FEEDBACK VISUAL")
    print("=" * 40)

    # Criar instância com feedback visual ativado
    nav = LineFollowingNavigation(visual_feedback=True)

    if not nav.initialize():
        print("❌ Falha na inicialização")
        return

    print("✅ Sistema inicializado com feedback visual")
    print("💡 Pressione Ctrl+C para parar a demonstração")

    try:
        # Loop de demonstração
        while True:
            # Simular processamento de frame
            line_info = nav.line_detector.process_frame()

            # Atualizar status simulado
            nav.status_info.update({
                'velocidade': 50,
                'direcao': 'simulacao',
                'erro_pixels': 10,
                'correcao': 0.1,
                'qr_detectado': False,
                'linha_detectada': line_info and line_info.get('detected', False),
                'confianca': line_info.get('confidence', 0.0) if line_info else 0.0
            })

            # Atualizar display visual
            nav.update_visual_frame(None, line_info)

            # Pequena pausa
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Demonstração interrompida pelo usuário")

    finally:
        nav.cleanup()
        print("👋 Demonstração finalizada")

if __name__ == "__main__":
    demo_visual_feedback()