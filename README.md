# B3 Trading Bot

Bot automatizado para trading na Bolsa de Valores Brasileira (B3) usando Python e MetaTrader 5.

## 🚀 Funcionalidades

- Conexão com MetaTrader 5 (suporte a conta demo e real)
- Múltiplas estratégias de trading:
  - Momentum (cruzamento de médias + RSI)
  - Mean Reversion (Bandas de Bollinger + RSI)
- Sistema de gerenciamento de risco
- Backtesting integrado
- Logging completo de operações
- Verificação automática de horário da B3

## 📋 Pré-requisitos

- Python 3.8+
- MetaTrader 5 instalado
- Conta demo/real em corretora que ofereça MT5

## 🔧 Instalação

1. Clone o repositório:
```bash
python
``` 
```bash
git clone https://github.com/seu-usuario/b3-trading-bot.git
cd b3-trading-bot
```

2. Crie um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure o arquivo `.env` com suas preferências

## 🎯 Uso

**Modo Trading Real**
```bash
python b3_bot.py
```

**Modo Backtest**
```bash
python backtest.py
```

## ⚙️ Configuração

Edite o arquivo `.env` para ajustar:

- `RISCO_POR_OPERACAO`: Percentual do capital arriscado por operação
- `CAPITAL_INICIAL`: Capital inicial para cálculos
- `MODO_SIMULADO`: True para conta demo, False para real

## 📊 Estratégias Implementadas

### Momentum
Entrada: Cruzamento de médias (9/21) com confirmação do RSI

Saída: Cruzamento contrário ou stop loss/take profit

### Mean Reversion
Entrada: Preço nas bandas de Bollinger + RSI extremo

Saída: Retorno à média ou stop loss/take profit

## ⚠️ Avisos

- Risco: Trading envolve risco significativo de perda
- Teste sempre em conta demo primeiro
- Nunca arrisque dinheiro que você não pode perder
- Este é um software experimental - use por sua conta e risco

## 📝 Licença

Este projeto está sob a licença MIT.

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

