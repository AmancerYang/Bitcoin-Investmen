import backtrader as bt
import backtrader.feeds as btfeeds
import pytz
import talib
a= 16

# 创建策略
class TestStrategy(bt.Strategy):
    params = (
        ('rsi_period', a),
    )

    def __init__(self):
        self.rsi = bt.talib.RSI(self.data.close, timeperiod=self.params.rsi_period)
        self.order = None

    def next(self):
        if self.order:  # check if an order is pending
            return

        if not self.position:  # not in the market
            if self.rsi <30:  # RSI is less than 30, indicating oversold condition
                self.order = self.buy()  # enter long position
        else:  # in the market
            if self.rsi >70:  # RSI is greater than 70, indicating overbought condition
                self.order = self.sell()  # close long position

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return

        if order.status in [bt.Order.Completed]:
            if order.isbuy():
                print(f'BUY EXECUTED, {order.executed.price}')
            elif order.issell():
                print(f'SELL EXECUTED, {order.executed.price}')
        elif order.status in [bt.Order.Canceled, bt.Order.Margin, bt.Order.Rejected]:
            print('Order Failed')

        self.order = None  # write down that there is no order pending

# 创建 Cerebro 引擎
cerebro = bt.Cerebro()

# 加载数据
data = btfeeds.GenericCSVData(
    dataname='data-1696942025290_fixed.csv',
    dtformat=('%Y-%m-%d %H:%M:%S%z'),  # 修改这里
    timeframe=bt.TimeFrame.Minutes,
    datetime=0,
    high=4,
    low=5,
    open=3,
    close=6,
    volume=7,
    openinterest=-1,
    tz=pytz.timezone('UTC')
)

# 添加数据到 Cerebro
cerebro.adddata(data)

# 添加策略到 Cerebro
cerebro.addstrategy(TestStrategy, rsi_period=a)

# 设置初始资金
cerebro.broker.setcash(100000.0)

# 打印初始资金
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# 运行回测
cerebro.run()

# 打印最后资金
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
