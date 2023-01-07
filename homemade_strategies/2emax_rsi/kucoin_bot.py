import sys
import pandas as pd
import ta
import time
import requests
import json
from datetime import datetime
from math import floor, log10

from kucoin.client import Trade
from kucoin.client import Market
from kucoin.client import User


########################
### Authentification ###
########################
api_key = ""
api_secret = ""
api_passphrase = ""

user = User(api_key, api_secret, api_passphrase)          # for account stuff
market = Market(api_key, api_secret, api_passphrase)      # for prices stuff
trade = Trade(api_key, api_secret, api_passphrase)        # for orders stuff


############
### Data ###
############
symbol_base = "ETH"
symbol_quote = "USDT"
timeframe = "1day"
days_back = 18

url='https://api.kucoin.com'
starting_date = float(round(time.time()))-days_back*24*3600

check = True
while check:
    data = requests.get(url + f'/api/v1/market/candles?type={timeframe}&symbol={symbol_base}-{symbol_quote}&startAt={int(starting_date)}')
    data = data.json()
    check = 'msg' in data.keys()


data = pd.DataFrame(data['data'], columns = ['timestamp', 'open', 'close', 'high', 'low', 'amount', 'volume'])
data["close"] = pd.to_numeric(data["close"])
data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s')


################
### Strategy ###
################
data['EMA-st'] = ta.trend.ema_indicator(data['close'], 12)
data['EMA-lt'] = ta.trend.ema_indicator(data['close'], 18)
data['RSI'] = ta.momentum.rsi(data['close'])
data = data.iloc[-1]

entry = data['EMA-st'] > data['EMA-lt'] and data['RSI'] < 70
take_profit = data['EMA-st'] < data['EMA-lt'] and data['RSI'] > 30


############
### Prep ###
############
### Balances
balance_quote = float(user.get_account_list(currency=symbol_quote)[0]['available'])
balance_base = float(user.get_account_list(currency=symbol_base)[0]['available'])


### Price
price = market.get_ticker(f'{symbol_base}-{symbol_quote}')
price = float(market.get_ticker(f'{symbol_base}-{symbol_quote}')['price'])


### Minimum requirements
info = requests.get(url + f'/api/v1/symbols/{symbol_base}-{symbol_quote}')
info = info.json()['data']

# Truncation
min_truncate = int(abs(log10(float(info['baseIncrement']))))
def truncate(n):
    r = floor(float(n)*10**min_truncate)/10**min_truncate
    return str(r)

# Min amounts
min_quote_for_buy = float(info['minFunds'])
min_base_for_sell = float(truncate(float(min_quote_for_buy)/price))


##############
### Orders ###
##############
now = datetime.now()
current_time = now.strftime("%d/%m/%Y %H:%M:%S")

if entry and balance_quote > min_quote_for_buy:
        amount = truncate(balance_quote/price)
        trade.create_market_order(f'{symbol_base}-{symbol_quote}', 'buy', size=amount)
        print(f"{current_time}: bought {amount} {symbol_base} at {price}")
        # print(f"Bought {amount} {symbol_base} at {price}  (EMA-st = {data['EMA-st']}, EMA-lt = {data['EMA-lt']}, RSI = {data['RSI']})")

elif take_profit and balance_base > min_base_for_sell:
        amount = truncate(balance_base)
        trade.create_market_order(f'{symbol_base}-{symbol_quote}', 'sell', size=amount)
        print(f"{current_time}: sold {amount} {symbol_base} at {price}")
        # print(f"Sold {amount} {symbol_base} at {price} (EMA-st = {data['EMA-st']}, EMA-lt = {data['EMA-lt']}, RSI = {data['RSI']})")

# else:
        # print(f"Sorry mate, nothing much to do (EMA-st = {data['EMA-st']}, EMA-lt = {data['EMA-lt']}, RSI = {data['RSI']})")
