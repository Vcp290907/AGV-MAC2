#!/usr/bin/env python3
"""
Teste rápido da navegação no Windows
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from line_following_navigation import LineFollowingNavigation

def test_initialization():
    """Testar apenas a inicialização"""
    print("🧪 TESTE DE INICIALIZAÇÃO - WINDOWS")
    print("=" * 40)

    # Criar instância com feedback visual desativado por padrão
    nav = LineFollowingNavigation(visual_feedback=False)

    # Tentar inicializar
    if nav.initialize():
        print("✅ Inicialização bem-sucedida!")
        print("💡 Sistema pronto para testes visuais")
        nav.cleanup()
        return True
    else:
        print("❌ Falha na inicialização")
        return False

if __name__ == "__main__":
    test_initialization()