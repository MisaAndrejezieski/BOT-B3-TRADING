import time as tm
from datetime import datetime, timedelta

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import schedule

from config import ConfigB3, logger
from estrategias import EstrategiaMeanReversion, EstrategiaMomentum


class B3TradingBot:
    """Bot de trading para B3 usando MetaTrader 5"""
    
    def __init__(self):
        self.config = ConfigB3()
        self.conectado = False
        self.ativos_monitorados = ["PETR4", "VALE3", "ITUB4"]
        self.estrategias = {
            "momentum": EstrategiaMomentum(),
            "mean_reversion": EstrategiaMeanReversion()
        }
        self.positions = {}
        self.daily_stats = {
            'trades': 0,
            'win_rate': 0,
            'pnl': 0
        }
        
    def conectar_mt5(self):
        """Estabelece conexão com MetaTrader 5"""
        if not mt5.initialize():
            logger.error("Falha ao inicializar MT5")
            return False
        
        # Verifica se é para usar conta demo ou real
        if self.config.MODO_SIMULADO:
            logger.info("Conectado em MODO SIMULADO (conta demo)")
        else:
            logger.warning("Conectado em MODO REAL - CUIDADO!")
        
        self.conectado = True
        logger.info("MT5 inicializado com sucesso")
        
        # Informações da conta
        account_info = mt5.account_info()
        if account_info:
            logger.info(f"Conta: {account_info.login}")
            logger.info(f"Balance: R$ {account_info.balance:.2f}")
            logger.info(f"Equity: R$ {account_info.equity:.2f}")
        
        return True
    
    def obter_dados_historicos(self, ativo, timeframe=mt5.TIMEFRAME_M5, n_candles=100):
        """Obtém dados históricos do ativo"""
        if not self.conectado:
            logger.error("MT5 não conectado")
            return None
        
        rates = mt5.copy_rates_from_pos(ativo, timeframe, 0, n_candles)
        if rates is None:
            logger.error(f"Erro ao obter dados para {ativo}")
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        return df
    
    def calcular_lotes(self, ativo, preco, stop_points):
        """Calcula quantidade de lotes baseado no risco"""
        capital = mt5.account_info().balance
        risco_porcentagem = self.config.RISCO_POR_OPERACAO
        risco_valor = capital * risco_porcentagem
        
        # Valor do ponto para o ativo
        symbol_info = mt5.symbol_info(ativo)
        if symbol_info is None:
            logger.error(f"Ativo {ativo} não encontrado")
            return 0
        
        # Cálculo simplificado para ações
        valor_por_ponto = preco * 100  # 1 lote = 100 ações
        
        lotes = risco_valor / (stop_points * valor_por_ponto)
        
        # Arredonda para o mínimo permitido
        min_lote = 1  # 1 ação
        lotes = max(min_lote, int(lotes * 100) / 100)
        
        return lotes
    
    def executar_ordem(self, ativo, tipo, volume, sl_points=None, tp_points=None):
        """Executa ordem de compra/venda"""
        if not self.config.mercado_aberto():
            logger.warning("Mercado fechado - ordem não executada")
            return None
        
        symbol_info = mt5.symbol_info(ativo)
        if symbol_info is None:
            logger.error(f"Ativo {ativo} não encontrado")
            return None
        
        ponto = symbol_info.point
        preco_atual = mt5.symbol_info_tick(ativo).ask if tipo == "BUY" else mt5.symbol_info_tick(ativo).bid
        
        # Prepara request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": ativo,
            "volume": float(volume),
            "type": mt5.ORDER_TYPE_BUY if tipo == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": preco_atual,
            "deviation": 10,
            "magic": 234000,
            "comment": "B3 Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Adiciona stop loss e take profit se especificados
        if sl_points:
            if tipo == "BUY":
                request["sl"] = preco_atual - sl_points * ponto
            else:
                request["sl"] = preco_atual + sl_points * ponto
        
        if tp_points:
            if tipo == "BUY":
                request["tp"] = preco_atual + tp_points * ponto
            else:
                request["tp"] = preco_atual - tp_points * ponto
        
        # Envia ordem
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Falha na ordem: {result.comment}")
            return None
        
        logger.info(f"Ordem executada: {tipo} {volume} {ativo} @ {preco_atual}")
        
        # Registra posição
        self.positions[result.order] = {
            'ticket': result.order,
            'ativo': ativo,
            'tipo': tipo,
            'volume': volume,
            'preco_entrada': preco_atual,
            'sl': request.get('sl'),
            'tp': request.get('tp'),
            'time': datetime.now()
        }
        
        return result.order
    
    def verificar_sinais(self):
        """Verifica sinais de trading para todos os ativos monitorados"""
        if not self.config.mercado_aberto():
            return
        
        for ativo in self.ativos_monitorados:
            df = self.obter_dados_historicos(ativo)
            if df is None or len(df) < 50:
                continue
            
            # Aplica estratégias
            for nome_estrategia, estrategia in self.estrategias.items():
                sinal = estrategia.gerar_sinal(df)
                
                if sinal != 'NEUTRO':
                    logger.info(f"Sinal {sinal} para {ativo} pela estratégia {nome_estrategia}")
                    
                    # Executa ordem
                    if sinal == 'COMPRA':
                        volume = self.calcular_lotes(ativo, df['close'].iloc[-1], 50)  # 50 pontos de stop
                        self.executar_ordem(ativo, 'BUY', volume, sl_points=50, tp_points=100)
                    elif sinal == 'VENDA':
                        volume = self.calcular_lotes(ativo, df['close'].iloc[-1], 50)
                        self.executar_ordem(ativo, 'SELL', volume, sl_points=50, tp_points=100)
    
    def monitorar_posicoes(self):
        """Monitora posições abertas e atualiza estatísticas"""
        positions = mt5.positions_get()
        
        if positions:
            for position in positions:
                ticket = position.ticket
                if ticket in self.positions:
                    # Calcula P&L
                    pnl = position.profit
                    logger.info(f"Posição {ticket}: {position.symbol} - P&L: R$ {pnl:.2f}")
                    
                    # Atualiza estatísticas
                    self.daily_stats['pnl'] += pnl
    
    def run(self):
        """Loop principal do bot"""
        logger.info("Iniciando B3 Trading Bot...")
        
        if not self.conectar_mt5():
            return
        
        # Agenda verificações
        schedule.every(5).minutes.do(self.verificar_sinais)
        schedule.every(1).minutes.do(self.monitorar_posicoes)
        
        # Verifica a cada 15 segundos se é hora de executar tarefas agendadas
        while True:
            if self.config.mercado_aberto():
                schedule.run_pending()
            else:
                logger.info("Mercado fechado - aguardando...")
            
            tm.sleep(15)
    
    def encerrar(self):
        """Encerra conexão com MT5"""
        mt5.shutdown()
        logger.info("Bot encerrado")

if __name__ == "__main__":
    bot = B3TradingBot()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro: {e}")
    finally:
        bot.encerrar()
