from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yfinance as yf

from estrategias import EstrategiaMeanReversion, EstrategiaMomentum


class Backtester:
    """Classe para backtest de estratégias"""
    
    def __init__(self, ativo, capital_inicial=10000):
        self.ativo = ativo
        self.capital_inicial = capital_inicial
        self.capital = capital_inicial
        self.positions = []
        self.trades = []
        
    def obter_dados_historicos(self, periodo="6mo"):
        """Obtém dados históricos do Yahoo Finance"""
        ticker = f"{self.ativo}.SA"  # Formato para B3 no Yahoo Finance
        df = yf.download(ticker, period=periodo, interval="5m")
        df.columns = ['close', 'high', 'low', 'open', 'volume']
        return df
    
    def executar_backtest(self, estrategia, df):
        """Executa backtest para uma estratégia"""
        capital = self.capital_inicial
        posicao = None
        
        for i in range(50, len(df)):  # Começa após período de aquecimento
            df_slice = df.iloc[:i+1]
            sinal = estrategia.gerar_sinal(df_slice)
            
            preco_atual = df.iloc[i]['close']
            
            # Fecha posição existente
            if posicao is not None:
                if (posicao['tipo'] == 'COMPRA' and sinal == 'VENDA') or \
                   (posicao['tipo'] == 'VENDA' and sinal == 'COMPRA'):
                    
                    # Calcula resultado
                    if posicao['tipo'] == 'COMPRA':
                        resultado = (preco_atual - posicao['preco']) * 100
                    else:
                        resultado = (posicao['preco'] - preco_atual) * 100
                    
                    capital += resultado
                    
                    self.trades.append({
                        'data_entrada': posicao['data'],
                        'data_saida': df.index[i],
                        'tipo': posicao['tipo'],
                        'preco_entrada': posicao['preco'],
                        'preco_saida': preco_atual,
                        'resultado': resultado,
                        'capital': capital
                    })
                    
                    posicao = None
            
            # Abre nova posição
            if posicao is None and sinal != 'NEUTRO':
                posicao = {
                    'tipo': sinal,
                    'preco': preco_atual,
                    'data': df.index[i]
                }
        
        return capital
    
    def analisar_resultados(self):
        """Analisa resultados do backtest"""
        if not self.trades:
            print("Nenhum trade executado")
            return
        
        df_trades = pd.DataFrame(self.trades)
        
        # Estatísticas
        total_trades = len(df_trades)
        trades_ganhadores = len(df_trades[df_trades['resultado'] > 0])
        win_rate = (trades_ganhadores / total_trades * 100) if total_trades > 0 else 0
        
        resultado_total = df_trades['resultado'].sum()
        resultado_medio = df_trades['resultado'].mean()
        
        print("\n" + "="*50)
        print(f"RESULTADOS DO BACKTEST - {self.ativo}")
        print("="*50)
        print(f"Capital Inicial: R$ {self.capital_inicial:.2f}")
        print(f"Capital Final: R$ {self.capital:.2f}")
        print(f"Retorno Total: R$ {resultado_total:.2f} ({((self.capital/self.capital_inicial)-1)*100:.2f}%)")
        print(f"Total de Trades: {total_trades}")
        print(f"Trades Ganhadores: {trades_ganhadores}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Resultado Médio: R$ {resultado_medio:.2f}")
        print("="*50)
        
        # Plot resultados
        self.plot_resultados(df_trades)
        
    def plot_resultados(self, df_trades):
        """Plota gráficos dos resultados"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Evolução do capital
        axes[0,0].plot(df_trades['capital'], marker='o')
        axes[0,0].set_title('Evolução do Capital')
        axes[0,0].set_xlabel('Trade')
        axes[0,0].set_ylabel('Capital (R$)')
        axes[0,0].grid(True)
        
        # Distribuição dos resultados
        axes[0,1].hist(df_trades['resultado'], bins=20, edgecolor='black')
        axes[0,1].axvline(x=0, color='red', linestyle='--')
        axes[0,1].set_title('Distribuição dos Resultados')
        axes[0,1].set_xlabel('Resultado (R$)')
        axes[0,1].set_ylabel('Frequência')
        axes[0,1].grid(True)
        
        # Win/Loss por tipo
        tipos = df_trades.groupby('tipo')['resultado'].agg(['count', 'mean'])
        tipos.plot(kind='bar', ax=axes[1,0])
        axes[1,0].set_title('Desempenho por Tipo de Operação')
        axes[1,0].set_xlabel('Tipo')
        axes[1,0].set_ylabel('Quantidade / Média (R$)')
        axes[1,0].grid(True)
        
        # Cumulative returns
        df_trades['cumulative'] = df_trades['resultado'].cumsum()
        axes[1,1].fill_between(df_trades.index, df_trades['cumulative'], 0, 
                               where=(df_trades['cumulative'] >= 0), color='green', alpha=0.3)
        axes[1,1].fill_between(df_trades.index, df_trades['cumulative'], 0, 
                               where=(df_trades['cumulative'] < 0), color='red', alpha=0.3)
        axes[1,1].plot(df_trades['cumulative'], color='blue', linewidth=2)
        axes[1,1].set_title('Resultado Acumulado')
        axes[1,1].set_xlabel('Trade')
        axes[1,1].set_ylabel('Resultado Acumulado (R$)')
        axes[1,1].grid(True)
        
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    # Exemplo de uso
    ativos_teste = ["PETR4", "VALE3", "ITUB4"]
    estrategias = {
        "Momentum": EstrategiaMomentum(),
        "Mean Reversion": EstrategiaMeanReversion()
    }
    
    for ativo in ativos_teste:
        print(f"\n\n{'='*60}")
        print(f"BACKTEST PARA {ativo}")
        print('='*60)
        
        backtester = Backtester(ativo)
        df = backtester.obter_dados_historicos("3mo")
        
        for nome_estrategia, estrategia in estrategias.items():
            print(f"\n--- Estratégia: {nome_estrategia} ---")
            backtester.capital = backtester.capital_inicial
            resultado = backtester.executar_backtest(estrategia, df.copy())
            backtester.analisar_resultados()
