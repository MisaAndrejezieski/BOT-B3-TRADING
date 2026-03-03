import logging
import os
from datetime import time

import MetaTrader5 as mt5
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfigB3:
    """Configurações específicas para trading na B3"""
    
    # Horário de funcionamento da B3
    HORARIO_ABERTURA = time(10, 0)  # 10:00
    HORARIO_FECHAMENTO = time(18, 0)  # 18:00
    
    # Feriados da B3 2026 (adicionar mais conforme necessário)
    FERIADOS_B3 = [
        "2026-01-01",  # Confraternização Universal
        "2026-02-17",  # Carnaval
        "2026-02-18",  # Quarta-feira de Cinzas (meio dia)
        "2026-04-03",  # Paixão de Cristo
        "2026-04-21",  # Tiradentes
        "2026-05-01",  # Dia do Trabalho
        "2026-06-11",  # Corpus Christi
        "2026-09-07",  # Independência
        "2026-10-12",  # Nossa Senhora Aparecida
        "2026-11-02",  # Finados
        "2026-11-15",  # Proclamação da República
        "2026-12-25",  # Natal
    ]
    
    # Mapeamento de ativos para símbolos MT5
    ATIVOS = {
        "PETR4": "PETR4",
        "VALE3": "VALE3",
        "ITUB4": "ITUB4",
        "BBDC4": "BBDC4",
        "ABEV3": "ABEV3",
        "WINFUT": "WINJ25",  # Mini-Índice (atualizar conforme vencimento)
        "WDOFUT": "WDOJ25",  # Mini-Dólar (atualizar conforme vencimento)
    }
    
    # Configurações de risco
    RISCO_POR_OPERACAO = float(os.getenv('RISCO_POR_OPERACAO', 0.01))
    CAPITAL_INICIAL = float(os.getenv('CAPITAL_INICIAL', 10000))
    MODO_SIMULADO = os.getenv('MODO_SIMULADO', 'True').lower() == 'true'
    
    @staticmethod
    def mercado_aberto():
        """Verifica se o mercado da B3 está aberto"""
        from datetime import datetime
        
        agora = datetime.now()
        hora_atual = agora.time()
        
        # Verifica se é dia útil
        if agora.weekday() >= 5:  # Sábado = 5, Domingo = 6
            return False
        
        # Verifica se é feriado
        data_str = agora.strftime("%Y-%m-%d")
        if data_str in ConfigB3.FERIADOS_B3:
            return False
        
        # Verifica horário
        if hora_atual < ConfigB3.HORARIO_ABERTURA or hora_atual > ConfigB3.HORARIO_FECHAMENTO:
            return False
        
        return True
