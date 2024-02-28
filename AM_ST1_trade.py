
import configparser
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
import talib

# Configuration setup
config = configparser.ConfigParser()
config.read('config.ini')
api_key = config['BINANCE']['API_KEY']
api_secret = config['BINANCE']['API_SECRET']
client = Client(api_key, api_secret)
client.API_URL = 'https://fapi.binance.com/api/v1'


# Parameters
symbol = 'BTCUSDT'

leverage = int(6)
stop_loss = -0.02  # 2%
take_profit_point = [0.01, 0.04]  # take profits at 2% and 4%
take_profit_quantities = [0.618, 1]  # quantities for each take profit level
rsi_period = 14  # RSI calculation period in minutes
max_position = 600  # maximum position size in USDT
risk_fraction = 0.33  # risk percentage of balance on each trade

# CSV file for trade history
#csv_file = 'trade_history.csv'
#fieldnames = ['Timestamp', 'Trade_Type', 'Size', 'Entry_Price', 'Exit_Price', 'Profit/Loss']

# Initialize the list of open orders
order_book = []

def get_rsi(period):
    try:
        klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=period + 2)
    except Exception as e:
        print(f'Error getting RSI: {e}')
        return None
    close_prices = np.array([float(k[4]) for k in klines]) #k[4]是收盘价
    rsi = talib.RSI(close_prices, timeperiod=period)
    return rsi[-1]  #cReturn the last RSI value

def get_position():
    try:
        positions = client.futures_position_information()
    except Exception as e:
        print(f'Error getting position: {e}')
        return None
    position = [p for p in positions if p['symbol'] == symbol]
    return float(position[0]['positionAmt']) if position else 0

def get_balance():
    try:
        balance = client.futures_account_balance()
    except Exception as e:
        print(f'Error getting balance: {e}')
        return None
    usdt_balance = [b for b in balance if b['asset'] == 'USDT'][0]
    return float(usdt_balance['balance'])

def get_current_price():
    try:
        ticker = client.futures_ticker(symbol=symbol)
    except Exception as e:
        print(f'Error getting current price: {e}')
        return None
    return float(ticker['lastPrice'])


# # Calculate the floating profit/loss for each order
# def calculate_floating_pl():
#     current_price = get_current_price()
#     floating_pl = 0.0
#     for order in order_book:
#         if order['side'] == 'long':
#             floating_pl += (current_price - order['entry_price']) * order['quantity']*leverage
#         else:  # assuming short position
#             floating_pl += (order['entry_price'] - current_price) * order['quantity']*leverage
#     return floating_pl

def open_long(quantity):
    current_balance = get_balance()
    current_price = get_current_price()
    current_leverage_balance = current_balance * leverage
    order = None

    if current_leverage_balance < quantity:
        print(f'余额不足以开新仓位。当前余额: {current_balance}, 需要: {quantity}')
        return
    if get_position() + quantity*leverage > max_position:
        print(f'超过仓位限制，不开新仓位')
        return

    try:
        #
        client.futures_change_leverage(symbol=symbol, leverage=leverage)

        order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )


    except Exception as e:
        print(f'开启多头仓位时发生意外错误: {e}')
    # if order:
    #     # 将订单添加到开放订单列表
    #     order_total_qty = 0.0
    #     order_usdtAmt = 0.0
    #     order_commission = 0.0
    #     fills = order['fills']
    #     for fill in fills:
    #         price = float(fill['price'])
    #         qty = float(fill['qty'])
    #         commission = float(fill['commission'])
    #
    #         order_total_qty += qty
    #         order_usdtAmt += price * qty
    #         order_commission += commission


    return order if order else None  #Return the order

def close_long(quantity):
    # Check if there is a position to close
    if get_position() <= 0:
        print('没有开放的仓位可关闭')
        return
    order = None
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f'关闭 {quantity} {symbol} 的多头仓位')
    except BinanceAPIException as e:
        print(e)
    except Exception as e:
        print(f'关闭多头仓位时发生意外错误: {e}')

    return order if order else None  #Return the order
