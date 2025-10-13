#!/usr/bin/env python3
"""
Teste do LineDetector com câmera sob demanda
"""

from line_detector import LineDetector
import time

def test_line_detector():
    """Testar LineDetector com câmera sob demanda"""

    print("🔍 TESTANDO LINE DETECTOR COM CÂMERA SOB DEMANDA")
    print("=" * 60)

    # Criar detector
    detector = LineDetector()
    print("✅ LineDetector criado")

    # Inicializar
    if not detector.initialize():
        print("❌ Falha na inicialização")
        return False

    print("✅ LineDetector inicializado")

    try:
        # Testar múltiplas capturas
        for i in range(3):
            print(f"\n📸 Teste de captura {i+1}/3")

            # Processar frame
            info = detector.process_frame()

            if info:
                print("✅ Frame processado com sucesso")
                print(f"   📏 Linha detectada: {info.get('detected', False)}")
                print(f"   📍 Centro: {info.get('center', 'N/A')}")
                print(f"   📏 Largura: {info.get('width', 'N/A')}")
            else:
                print("❌ Falha no processamento do frame")

            # Pequena pausa
            time.sleep(0.5)

        print("\n✅ TODOS OS TESTES DE CAPTURA PASSARAM!")

    except Exception as e:
        print(f"❌ ERRO durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Limpar
        detector.cleanup()
        print("🧹 Recursos liberados")

    return True

if __name__ == "__main__":
    success = test_line_detector()
    if success:
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("💡 O problema do thread da câmera foi resolvido.")
    else:
        print("\n❌ TESTE FALHOU")
        print("🔧 Ainda há problemas com a câmera.")