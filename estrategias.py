import numpy as np
import pandas as pd


class EstrategiaBase:
    """Classe base para estratégias"""
    
    def gerar_sinal(self, df):
        """Deve ser implementado pelas subclasses"""
        raise NotImplementedError
    
    def calcular_medias_moveis(self, df, periodo_rapido=9, periodo_lento=21):
        """Calcula médias móveis"""
        df['MA_rapida'] = df['close'].rolling(window=periodo_rapido).mean()
        df['MA_lenta'] = df['close'].rolling(window=periodo_lento).mean()
        return df
    
    def calcular_rsi(self, df, periodo=14):
        """Calcula RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

class EstrategiaMomentum(EstrategiaBase):
    """Estratégia de momentum com cruzamento de médias + RSI"""
    
    def gerar_sinal(self, df):
        df = self.calcular_medias_moveis(df, 9, 21)
        df = self.calcular_rsi(df)
        
        ultimo = df.iloc[-1]
        anterior = df.iloc[-2]
        
        # Condições de compra
        if (anterior['MA_rapida'] <= anterior['MA_lenta'] and 
            ultimo['MA_rapida'] > ultimo['MA_lenta'] and 
            ultimo['RSI'] > 30 and ultimo['RSI'] < 70):
            return 'COMPRA'
        
        # Condições de venda
        elif (anterior['MA_rapida'] >= anterior['MA_lenta'] and 
              ultimo['MA_rapida'] < ultimo['MA_lenta'] and 
              ultimo['RSI'] < 70):
            return 'VENDA'
        
        return 'NEUTRO'

class EstrategiaMeanReversion(EstrategiaBase):
    """Estratégia de reversão à média usando Bandas de Bollinger"""
    
    def calcular_bollinger(self, df, periodo=20, desvios=2):
        """Calcula Bandas de Bollinger"""
        df['BB_media'] = df['close'].rolling(window=periodo).mean()
        df['BB_desvio'] = df['close'].rolling(window=periodo).std()
        df['BB_superior'] = df['BB_media'] + (df['BB_desvio'] * desvios)
        df['BB_inferior'] = df['BB_media'] - (df['BB_desvio'] * desvios)
        return df
    
    def gerar_sinal(self, df):
        df = self.calcular_bollinger(df)
        df = self.calcular_rsi(df)
        
        ultimo = df.iloc[-1]
        
        # Compra quando preço toca banda inferior e RSI < 30
        if ultimo['close'] <= ultimo['BB_inferior'] and ultimo['RSI'] < 30:
            return 'COMPRA'
        
        # Venda quando preço toca banda superior e RSI > 70
        elif ultimo['close'] >= ultimo['BB_superior'] and ultimo['RSI'] > 70:
            return 'VENDA'
        
        return 'NEUTRO'
