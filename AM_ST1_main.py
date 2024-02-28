from AM_ST1_trade import *
import time

while True:
    try:
        #循环开始前先载入信息
        rsi = get_rsi(rsi_period)
        if rsi is None:  # MODIFICATION: Check if RSI is None
            continue
        balance = get_balance()
        if balance is None:  # MODIFICATION: Check if balance is None
            continue
        current_price = get_current_price()
        if current_price is None:  # MODIFICATION: Check if current price is None
            continue
        quantity = max(115,(balance * risk_fraction * leverage)) # calculate position size
        btc_quantity = round(quantity/current_price,3)

        positions = client.futures_account()['positions']
        position = next((p for p in positions if p['symbol'] == 'BTCUSDT'))
        current_position = position['positionAmt']

        print(f'RSI: {rsi}, Position:{current_position}, Balance: {balance}, Current Price: {current_price}, Quantity: {quantity}')


        # 第一步：检查持仓情况并进行止盈止损
        # 检查是否为多头持仓
        if float(position['positionAmt']) > 0:
            print("持有仓位%f"%float(position['positionAmt']))
            entry_price = float(position['entryPrice'])
            symbol = position['symbol']
            quantity = abs(float(position['positionAmt']))

            # 获取当前价格
            current_price = get_current_price()

            # 计算当前价格相对于入场价格的变化百分比
            price_change = (current_price - entry_price) / entry_price * leverage

            # 检查是否达到止损点
            if price_change <= stop_loss:
                try:
                    order = client.futures_create_order(
                        symbol=symbol,
                        side=Client.SIDE_SELL,
                        type=Client.ORDER_TYPE_MARKET,
                        quantity=quantity
                    )
                    print(f'Stop loss point reached for {symbol}, closing position.')
                except Exception as e:
                    print(f'Error occurred when closing position for {symbol}: {e}')

            # 检查是否达到止盈点
            else:
                for take_profit_point, take_profit_quantity in zip(take_profit_point, take_profit_quantities):
                    if price_change >= take_profit_point:
                        print(f'Take profit point reached for {symbol}, closing {take_profit_quantity * 100}% of existing position.')
                        try:
                            order = client.futures_create_order(
                                symbol=symbol,
                                side=Client.SIDE_SELL,
                                type=Client.ORDER_TYPE_MARKET,
                                quantity=round(quantity * take_profit_quantity,3)
                            )
                            # Update the remaining quantity
                            quantity *= (1 - take_profit_quantity)
                        except Exception as e:
                            print(f'Error occurred when closing position for {symbol}: {e}')
                        break

                            #当你持有仓位时检查是否触发止盈和止损条件
        #第二步：买入判断与操作
        if rsi < 30:  # RSI is less than 30, indicating oversold condition
            entry_order = open_long(btc_quantity)
            if entry_order is not None:
                print("成功开起多仓，orderid：%s" % (entry_order['orderId']))

        #第三步：风险控制触发超买但是未到止损点
        elif rsi > 70:  # RSI > 70,超买


            # 检查是否为多头仓位
            if float(position['positionAmt']) > 0:
                # 获取该仓位的交易对和数量
                symbol = position['symbol']
                quantity = round(float(position['positionAmt'],3))
                # 平仓
                try:
                    order = client.futures_create_order(
                        symbol=symbol,
                        side=Client.SIDE_SELL,
                        type=Client.ORDER_TYPE_MARKET,
                        quantity=quantity
                    )
                    positions = client.futures_account()['positions']
                    position = next((p for p in positions if p['symbol'] == 'BTCUSDT'))
                    current_position = position['positionAmt']
                    print("成功平仓，仓位剩余：%s"%current_position)

                except Exception as e:
                    print(f'Error occurred when closing position for {symbol}: {e},请手动检查仓位')
                    break



    except Exception as e:
        print(f'Unexpected error occurred in main loop: {e}')
        continue
    finally:
        print("这一轮运行完毕")
        time.sleep(60)