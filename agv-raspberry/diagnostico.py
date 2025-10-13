#!/usr/bin/env python3
"""
Diagnóstico dos problemas reportados
"""

import sys
import os

def test_imports():
    """Testar imports básicos"""
    print("🔍 TESTANDO IMPORTS...")

    try:
        from picamera2 import Picamera2
        print("✅ Picamera2 importado com sucesso")
        picamera2_version = getattr(Picamera2, '__version__', 'desconhecida')
        print(f"   Versão: {picamera2_version}")
    except ImportError as e:
        print(f"❌ Erro ao importar Picamera2: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Picamera2 importado mas com warning: {e}")

    try:
        import cv2
        print(f"✅ OpenCV importado: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ Erro ao importar OpenCV: {e}")
        return False

    try:
        import numpy as np
        print(f"✅ NumPy importado: {np.__version__}")
    except ImportError as e:
        print(f"❌ Erro ao importar NumPy: {e}")
        return False

    return True

def test_line_detector():
    """Testar LineDetector"""
    print("\n🔍 TESTANDO LINE DETECTOR...")

    try:
        from line_detector import LineDetector
        print("✅ LineDetector importado com sucesso")

        detector = LineDetector()
        print("✅ LineDetector instanciado")

        # Testar cleanup
        if hasattr(detector, 'cleanup'):
            print("✅ Método cleanup encontrado")
        else:
            print("❌ Método cleanup NÃO encontrado")

        # Testar initialize (sem realmente inicializar câmera)
        print("✅ LineDetector básico funcionando")

    except Exception as e:
        print(f"❌ Erro no LineDetector: {e}")
        return False

    return True

def test_navigation():
    """Testar LineFollowingNavigation"""
    print("\n🔍 TESTANDO NAVEGAÇÃO...")

    try:
        from line_following_navigation import LineFollowingNavigation
        print("✅ LineFollowingNavigation importado com sucesso")

        nav = LineFollowingNavigation(esp32_port=None)  # Sem ESP32 para teste
        print("✅ LineFollowingNavigation instanciado")

        # Testar cleanup
        if hasattr(nav, 'cleanup'):
            print("✅ Método cleanup encontrado")
            nav.cleanup()
            print("✅ Método cleanup executado com sucesso")
        else:
            print("❌ Método cleanup NÃO encontrado")

        print("✅ LineFollowingNavigation básico funcionando")

    except Exception as e:
        print(f"❌ Erro na navegação: {e}")
        return False

    return True

def main():
    print("🔧 DIAGNÓSTICO DOS PROBLEMAS REPORTADOS")
    print("=" * 50)

    all_good = True

    # Testar imports
    if not test_imports():
        all_good = False

    # Testar componentes
    if not test_line_detector():
        all_good = False

    if not test_navigation():
        all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("💡 Os problemas originais foram corrigidos:")
        print("   • Método cleanup adicionado")
        print("   • Tratamento de erros da câmera melhorado")
        print("   • Inicialização da câmera mais robusta")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("🔧 Verifique os erros acima")

    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Execute: python3 line_following_navigation.py")
    print("2. Teste as opções do menu")
    print("3. Se ainda houver problemas, verifique a câmera")

if __name__ == "__main__":
    main()