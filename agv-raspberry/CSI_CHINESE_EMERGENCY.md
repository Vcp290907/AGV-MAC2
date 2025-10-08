# 🚨 Guia de Emergência - Câmera CSI Chinesa Não Detectada

## ❌ Problema Identificado

Com base nos logs do sistema, o problema é claro:

```
[ 1430.749458] rp1-cfe 1f00128000.csi: csi2_ch0 node link is not enabled.
```

**Isso significa: NENHUMA câmera CSI está conectada ou funcionando!**

## 🔍 Diagnóstico Detalhado dos Resultados

### ✅ O Que Está Funcionando:
- Driver `rp1-cfe` carregado corretamente
- Dispositivo `/dev/video0` criado pelo sistema
- Raspberry Pi 5 reconhecendo barramento CSI
- V4L2 funcionando (40+ formatos suportados)

### ❌ O Que Não Está Funcionando:
- **Nenhum sinal de câmera** no barramento CSI
- `VIDIOC_STREAMON` falhando com "Invalid argument"
- Captura resultando em **0 bytes**
- Link CSI não habilitado

## 🛠️ Soluções Passo a Passo

### PASSO 1: Verificação Visual Básica
```bash
# Execute verificação rápida de sinal
bash check_csi_signal.sh
```

### PASSO 2: Verificar Conexão Física

#### 📍 Localização dos Conectores
- **Raspberry Pi 5**: Conector CSI na lateral, próximo ao HDMI
- **Câmera**: Cabo flat com conector azul voltado para o cabo USB

#### 🔧 Verificações:
1. **Cabo conectado?** ✓ Desconecte e reconecte
2. **Orientação correta?** ✓ Conector azul da câmera → cabo USB
3. **Cabo danificado?** ✓ Verifique se há dobras ou rasgos
4. **Pinos tortos?** ✓ Verifique alinhamento dos pinos

### PASSO 3: Verificar Alimentação ⚡

**IMPORTANTE:** Muitas câmeras chinesas CSI precisam de alimentação externa!

#### Tipos de Alimentação:
- **Câmeras com conector separado**: Conecte 5V externo ANTES do CSI
- **Câmeras "parasitas"**: Pegam energia do CSI (raras)

#### Como Verificar:
```bash
# Verificar tensão (se multímetro disponível)
# Ou testar com outra câmera conhecida
```

### PASSO 4: Teste com Câmera Diferente

Se possível, teste com:
- **Câmera oficial Raspberry Pi** (se tiver)
- **Outra câmera chinesa CSI** (se tiver)
- **Câmera USB** (para confirmar que OpenCV funciona)

### PASSO 5: Verificar Cabo CSI

#### Sintomas de Cabo Defeituoso:
- Câmera não detectada
- Logs mostram "node link is not enabled"
- v4l2-ctl consegue acessar mas captura 0 bytes

#### Como Testar:
1. Use outro cabo CSI conhecido
2. Teste o cabo atual em outro dispositivo
3. Verifique se os contatos estão limpos

## 🧪 Testes de Confirmação

### Teste 1: Verificação de Sinal
```bash
bash check_csi_signal.sh
```

### Teste 2: Diagnóstico Completo
```bash
bash diagnose_chinese_csi.sh
```

### Teste 3: Teste de Câmera
```bash
python3 test_chinese_csi_camera.py
```

## 🎯 Resultados Esperados

### ✅ Se a Câmera For Detectada:
```
[time] rp1-cfe 1f00128000.csi: csi2_ch0 node link is enabled.
```

### ✅ Se a Captura Funcionar:
```
✅ v4l2-ctl conseguiu acessar câmera
   📁 Dados brutos salvos: 614400 bytes  # (NÃO 0 bytes!)
```

## 🔧 Correções Avançadas (se necessário)

### 1. Reinicializar Driver CSI
```bash
# Descarregar e recarregar módulo
sudo modprobe -r rp1_cfe
sudo modprobe rp1_cfe

# Ou reiniciar sistema
sudo reboot
```

### 2. Verificar Device Tree
```bash
# Verificar overlays CSI
sudo vcdbg log msg 2>&1 | grep -i csi
```

### 3. Logs Detalhados
```bash
# Aumentar verbosidade dos logs
sudo dmesg -n 8
# Executar teste novamente
python3 test_chinese_csi_camera.py
```

## 📞 Quando Pedir Ajuda

Se nada funcionar, forneça estas informações:

1. **Modelo da câmera chinesa**: Marca, modelo, link de compra
2. **Conexão de alimentação**: Como está alimentada a câmera?
3. **Estado dos conectores**: Fotos dos conectores CSI
4. **Resultado completo**: `bash diagnose_chinese_csi.sh`
5. **Logs do kernel**: `dmesg | grep -i csi | tail -20`

## 💡 Conclusão

O problema é **físico/eletrônico**, não de software. O Raspberry Pi 5 e drivers estão funcionando perfeitamente. O problema está na **conexão da câmera** ou na **câmera em si**.

**Próximo passo:** Verifique a alimentação da câmera e a conexão física!