#!/usr/bin/env python3
"""
Script de teste para descoberta automática dos ESP32
Valida se o sistema está identificando corretamente Motor e Garra
"""

import sys
import os
import time

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from esp32_discovery import ESP32Discovery, load_discovered_ports
from esp32_control import (
    connect_esp32_motor, connect_esp32_garra,
    get_status_motor, get_status_garra,
    rediscover_esp32_ports
)

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_discovery():
    """Teste 1: Descoberta automática"""
    print_header("TESTE 1: Descoberta Automática dos ESP32")
    
    discovery = ESP32Discovery()
    result = discovery.discover_all()
    
    if result['motor']:
        print(f"✅ ESP32 MOTOR encontrado: {result['motor']}")
    else:
        print("❌ ESP32 MOTOR não encontrado")
    
    if result['garra']:
        print(f"✅ ESP32 GARRA encontrado: {result['garra']}")
    else:
        print("❌ ESP32 GARRA não encontrado")
    
    return result

def test_save_load():
    """Teste 2: Salvar e carregar configuração"""
    print_header("TESTE 2: Salvar e Carregar Configuração")
    
    print("💾 Salvando configuração...")
    discovery = ESP32Discovery()
    if discovery.save_to_config('esp32_ports.json'):
        print("✅ Configuração salva")
    else:
        print("❌ Falha ao salvar")
        return False
    
    print("\n📂 Carregando configuração...")
    loaded = load_discovered_ports('esp32_ports.json')
    
    print(f"   Motor: {loaded.get('motor')}")
    print(f"   Garra: {loaded.get('garra')}")
    
    return True

def test_connection():
    """Teste 3: Conexão com os ESP32"""
    print_header("TESTE 3: Conexão com ESP32")
    
    print("\n🔌 Conectando ao ESP32 MOTOR...")
    if connect_esp32_motor():
        print("✅ ESP32 MOTOR conectado")
        
        print("   📊 Obtendo status...")
        status = get_status_motor()
        print(f"   Status: {status}")
        
        print("\n   🧪 Teste de movimento básico...")
        try:
            from esp32_control import move_forward_esp32, stop_esp32
            print("   ⏩ Movendo para frente por 0.5s...")
            move_forward_esp32(0.5)
            print("   🛑 Parando...")
            stop_esp32()
            print("   ✅ Teste de movimento OK")
        except Exception as e:
            print(f"   ⚠️ Erro no teste de movimento: {e}")
    else:
        print("❌ Falha ao conectar ESP32 MOTOR")
        return False
    
    print("\n🔌 Conectando ao ESP32 GARRA...")
    if connect_esp32_garra():
        print("✅ ESP32 GARRA conectado")
        
        print("   📊 Obtendo status...")
        status = get_status_garra()
        print(f"   Status: {status}")
        
        print("\n   🧪 Teste de movimento de servo...")
        try:
            from esp32_control import move_servos_esp32
            print("   🤖 Movendo servo de teste...")
            test_angles = {
                "giro": 90,
                "um": 90,
                "dois": 90,
                "garra": 70,
                "servo3": 90
            }
            move_servos_esp32(test_angles)
            print("   ✅ Teste de servo OK")
        except Exception as e:
            print(f"   ⚠️ Erro no teste de servo: {e}")
    else:
        print("❌ Falha ao conectar ESP32 GARRA")
        return False
    
    return True

def test_rediscovery():
    """Teste 4: Redescobrimento"""
    print_header("TESTE 4: Redescobrimento Forçado")
    
    print("🔄 Forçando redescobrimento...")
    ports = rediscover_esp32_ports()
    
    print(f"   Motor: {ports.get('motor')}")
    print(f"   Garra: {ports.get('garra')}")
    
    if ports['motor'] and ports['garra']:
        print("✅ Redescobrimento bem-sucedido")
        return True
    else:
        print("⚠️ Redescobrimento incompleto")
        return False

def test_port_identification():
    """Teste 5: Identificação individual de portas"""
    print_header("TESTE 5: Identificação Individual de Portas")
    
    import serial.tools.list_ports
    
    ports = serial.tools.list_ports.comports()
    usb_ports = [p.device for p in ports if 'USB' in p.device or 'ACM' in p.device]
    
    if not usb_ports:
        print("❌ Nenhuma porta USB/ACM encontrada")
        return False
    
    print(f"📍 Portas USB encontradas: {len(usb_ports)}")
    
    discovery = ESP32Discovery()
    
    for port in usb_ports:
        print(f"\n🔍 Testando porta: {port}")
        device_type = discovery.identify_esp32(port)
        
        if device_type:
            print(f"   ✅ Identificado como: {device_type.upper()}")
        else:
            print(f"   ❓ Não identificado")
    
    return True

def main():
    print("="*70)
    print("  🧪 TESTE COMPLETO DE DESCOBERTA AUTOMÁTICA DOS ESP32")
    print("="*70)
    print("\n⚠️ IMPORTANTE:")
    print("   - Certifique-se de que os dois ESP32 estão conectados")
    print("   - O firmware deve responder a comandos de identificação")
    print("   - Aguarde alguns segundos entre os testes")
    
    input("\n🔔 Pressione ENTER para iniciar os testes...")
    
    # Lista de testes
    tests = [
        ("Descoberta Automática", test_discovery),
        ("Salvar e Carregar Config", test_save_load),
        ("Identificação de Portas", test_port_identification),
        ("Conexão e Comunicação", test_connection),
        ("Redescobrimento", test_rediscovery),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            
            if result:
                print(f"\n✅ {test_name}: PASSOU")
            else:
                print(f"\n⚠️ {test_name}: FALHOU")
            
            # Pequena pausa entre testes
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Testes interrompidos pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ {test_name}: ERRO - {e}")
            results[test_name] = False
    
    # Resumo final
    print_header("RESUMO DOS TESTES")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name}: {status}")
    
    print(f"\n📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n💡 Sistema de descoberta automática está funcionando corretamente.")
        print("   Os ESP32 serão detectados automaticamente mesmo se trocarem de porta.")
        return True
    else:
        print("\n⚠️ Alguns testes falharam. Verifique:")
        print("   1. Ambos os ESP32 estão conectados?")
        print("   2. O firmware está programado nos ESP32?")
        print("   3. As portas USB estão funcionando?")
        print("   4. Permissões de acesso às portas serial?")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
