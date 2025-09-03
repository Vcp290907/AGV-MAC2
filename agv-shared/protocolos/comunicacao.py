"""
Protocolos de Comunicação entre Sistema Web e Raspberry Pi
Define as estruturas de dados e APIs usadas na comunicação
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

# ========================================
# COMANDOS DO SISTEMA WEB PARA RASPBERRY
# ========================================

@dataclass
class ComandoMover:
    """Comando para mover AGV para um destino"""
    tipo: str = "mover"
    destino: str = ""  # Ex: "A1", "B2", "ORIGEM"
    itens: List[int] = None  # IDs dos itens para coletar
    prioridade: str = "normal"  # "baixa", "normal", "alta"
    
@dataclass
class ComandoParar:
    """Comando para parar AGV imediatamente"""
    tipo: str = "parar"
    motivo: str = "solicitacao_usuario"
    
@dataclass
class ComandoStatus:
    """Comando para obter status do AGV"""
    tipo: str = "status"
    detalhado: bool = False

# ========================================
# RESPOSTAS DO RASPBERRY PARA SISTEMA WEB
# ========================================

@dataclass
class StatusAGV:
    """Status completo do AGV"""
    ativo: bool
    posicao: Dict[str, float]  # {"x": 1.5, "y": 2.3, "orientacao": 90}
    bateria: int  # Percentual de 0 a 100
    status: str  # "parado", "movendo", "coletando", "erro"
    velocidade: float  # m/s
    destino_atual: Optional[str]
    itens_coletados: List[int]
    timestamp: float
    
@dataclass
class ResultadoComando:
    """Resultado da execução de um comando"""
    success: bool
    status: str  # "concluido", "em_andamento", "erro", "cancelado"
    mensagem: str
    dados: Optional[Dict] = None
    timestamp: float = 0

# ========================================
# APIS DE COMUNICAÇÃO
# ========================================

class ProtocoloWebRaspberry:
    """Define os endpoints de comunicação"""
    
    # Endpoints no Raspberry Pi (recebe comandos)
    RASPBERRY_BASE_URL = "http://{ip}:8080"
    EXECUTAR_COMANDO = "/executar"
    OBTER_STATUS = "/status"
    STREAM_CAMERA = "/camera"
    
    # Endpoints no Sistema Web (recebe atualizações)
    WEB_BASE_URL = "http://{ip}:5000"
    ATUALIZAR_STATUS = "/agv/status_update"
    NOTIFICAR_EVENTO = "/agv/evento"

# ========================================
# UTILITÁRIOS DE COMUNICAÇÃO
# ========================================

def criar_comando_mover(destino: str, itens: List[int] = None) -> Dict:
    """Cria comando de movimento formatado"""
    return {
        "tipo": "mover",
        "destino": destino,
        "itens": itens or [],
        "timestamp": __import__('time').time()
    }

def criar_comando_parar(motivo: str = "solicitacao_usuario") -> Dict:
    """Cria comando de parada formatado"""
    return {
        "tipo": "parar",
        "motivo": motivo,
        "timestamp": __import__('time').time()
    }

def validar_comando(comando: Dict) -> bool:
    """Valida se um comando tem a estrutura correta"""
    tipos_validos = ["mover", "parar", "status"]
    
    if not isinstance(comando, dict):
        return False
        
    if "tipo" not in comando:
        return False
        
    if comando["tipo"] not in tipos_validos:
        return False
        
    # Validações específicas por tipo
    if comando["tipo"] == "mover":
        return "destino" in comando
        
    return True

# ========================================
# CONFIGURAÇÕES DE REDE
# ========================================

class ConfiguracaoRede:
    """Configurações de rede para comunicação"""
    
    # Portas padrão
    PORTA_WEB_BACKEND = 5000
    PORTA_WEB_FRONTEND = 3000
    PORTA_RASPBERRY = 8080
    
    # Timeouts (segundos)
    TIMEOUT_COMANDO = 30
    TIMEOUT_STATUS = 5
    
    # Intervalos de atualização (segundos)
    INTERVALO_STATUS = 2
    INTERVALO_HEARTBEAT = 10
