import pandas as pd
import ta
import time
import requests
import json
from math import floor, log10

from kucoin.client import Trade
from kucoin.client import Market
from kucoin.client import User


########################
### Authentification ###
########################
account_to_select = "homemade_strategy_1"

with open("./live_tools/authentification.json") as file:
    auth = json.load(file)
key = auth[account_to_select]["key"]
secret = auth[account_to_select]["secret"]
passphrase = auth[account_to_select]["passphrase"]
user = User(key, secret, passphrase)          # for account stuff
market = Market(key, secret, passphrase)      # for prices stuff
trade = Trade(key, secret, passphrase)        # for orders stuff


#########################
### Data & Indicators ###
#########################
symbol_base = "ETH"
symbol_quote = "USDT"
# timeframe = "1day"
timeframe = "1min"
days_back = 18

# market.get_kline(symbol)
url='https://api.kucoin.com'
# starting_date = float(round(time.time()))-days_back*24*3600
starting_date = float(round(time.time()))-days_back*60
data = requests.get(url + f'/api/v1/market/candles?type={timeframe}&symbol={symbol_base}-{symbol_quote}&startAt={int(starting_date)}')
data = data.json()
# print(url + f'/api/v1/market/candles?type={timeframe}&symbol={symbol_base}-{symbol_quote}&startAt={int(starting_date)}')
# print(data)
# import sys
# sys.exit()

data = pd.DataFrame(data['data'], columns = ['timestamp', 'open', 'close', 'high', 'low', 'amount', 'volume'])
data["close"] = pd.to_numeric(data["close"])
data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s')
# print(data)
# import sys
# sys.exit()


################
### Strategy ###
################
# data['EMA-st'] = ta.trend.ema_indicator(data['close'], 12)
# data['EMA-lt'] = ta.trend.ema_indicator(data['close'], 18)
data['EMA-st'] = ta.trend.ema_indicator(data['close'], 1)
data['EMA-lt'] = ta.trend.ema_indicator(data['close'], 2)
data['RSI'] = ta.momentum.rsi(data['close'])
# print(data)
# import sys
# sys.exit()

data = data.iloc[-1]
# print(data)
# import sys
# sys.exit()

entry = data['EMA-st'] > data['EMA-lt'] and data['RSI'] < 70
take_profit = data['EMA-st'] < data['EMA-lt'] and data['RSI'] > 30
# print('entry', entry)
# print('take_profit', take_profit)
# import sys
# sys.exit()

############
### Prep ###
############
### Balances
# print(user.get_account_list(currency=symbol_quote))
# print(user.get_account_list(currency=symbol_base))
# import sys
# sys.exit()
balance_quote = float(user.get_account_list(currency=symbol_quote)[0]['available'])
balance_base = float(user.get_account_list(currency=symbol_base)[0]['available'])
# print(symbol_quote, balance_quote)
# print(symbol_base, balance_base)
# import sys
# sys.exit()

### Price
# price = market.get_ticker(f'{symbol_base}-{symbol_quote}')
# print(price)
price = float(market.get_ticker(f'{symbol_base}-{symbol_quote}')['price'])
# print(price)
# import sys
# sys.exit()

### Minimum requirements
info = requests.get(url + f'/api/v1/symbols/{symbol_base}-{symbol_quote}')
info = info.json()['data']
# print(info)
# import sys
# sys.exit()

# Truncation
min_truncate = int(abs(log10(float(info['baseIncrement']))))
# print(min_truncate)
# import sys
# sys.exit()

def truncate(n):
    r = floor(float(n)*10**min_truncate)/10**min_truncate
    return str(r)

# Min amounts
min_quote_for_buy = float(info['minFunds'])
min_base_for_sell = float(truncate(float(min_quote_for_buy)/price))


#############
### Trade ###
#############

# balance_quote = float(user.get_account_list(currency=symbol_quote)[0]['available'])
# balance_base = float(user.get_account_list(currency=symbol_base)[0]['available'])
# print(symbol_quote, balance_quote)
# print(symbol_base, balance_base)
# buy_amount = truncate(balance_quote/price)
# order_id = trade.create_market_order(f'{symbol_base}-{symbol_quote}', 'buy', size=buy_amount)
# print(order_id)
#
# balance_quote = float(user.get_account_list(currency=symbol_quote)[0]['available'])
# balance_base = float(user.get_account_list(currency=symbol_base)[0]['available'])
# print(symbol_quote, balance_quote)
# print(symbol_base, balance_base)
# sell_amount = truncate(balance_base)
# order_id = trade.create_market_order(f'{symbol_base}-{symbol_quote}', 'sell', size=sell_amount)
# print(order_id)
#
# balance_quote = float(user.get_account_list(currency=symbol_quote)[0]['available'])
# balance_base = float(user.get_account_list(currency=symbol_base)[0]['available'])
# print(symbol_quote, balance_quote)
# print(symbol_base, balance_base)


if entry and balance_quote > min_quote_for_buy:
        amount = truncate(balance_quote/price)
        trade.create_market_order(f'{symbol_base}-{symbol_quote}', 'buy', size=amount)
        print(f"Bought {amount} {symbol_base} at {price}  (EMA-st = {data['EMA-st']}, EMA-lt = {data['EMA-lt']}, RSI = {data['RSI']})")

elif take_profit and balance_base > min_base_for_sell:
        amount = truncate(balance_base)
        trade.create_market_order(f'{symbol_base}-{symbol_quote}', 'sell', size=amount)
        print(f"Sold {amount} {symbol_base} at {price} (EMA-st = {data['EMA-st']}, EMA-lt = {data['EMA-lt']}, RSI = {data['RSI']})")

else:
  print(f"Sorry mate, nothing much to do (EMA-st = {data['EMA-st']}, EMA-lt = {data['EMA-lt']}, RSI = {data['RSI']})")
