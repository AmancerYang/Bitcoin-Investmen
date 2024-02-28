from datetime import datetime
import backtrader as bt
import os.path  # 管理路径
import sys  # 发现脚本名字(in argv[0])
from backtrader.feeds import GenericCSVData  # 用于扩展DataFeed
import quantstats as qs

class GenericCSV_PE(GenericCSVData):

    # 增加pe线
    lines = ('pe', )
    # 默认第8列（从0开始数）
    params = (('pe', 8), )


# 创建新的data feed类
# class GenericCSV_PE(GenericCSVData):
#
#     # 增加pe线
#     lines = ('pe', )
#     # 默认第8列（从0开始数）
#     params = (('pe', 8), )


# 创建策略类
class SmaCross(bt.Strategy):
    # 定义参数wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww
    params = dict(period=15  # 移动平均期数
                  )

    # 日志函数
    def log(self, txt, dt=None):
        '''日志函数'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单状态 submitted/accepted，无动作
            return

        # 订单完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('买单执行, %.2f' % order.executed.price)

            elif order.issell():
                self.log('卖单执行, %.2f' % order.executed.price)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单 Canceled/Margin/Rejected')

    # 记录交易收益情况（可省略，默认不输出结果）
    def notify_trade(self, trade):
        if trade.isclosed:
            print('毛收益 %0.2f, 扣佣后收益 % 0.2f, 佣金 %.2f' %
                  (trade.pnl, trade.pnlcomm, trade.commission))

    def __init__(self):


        # 移动平均线指标
        self.move_average = bt.ind.MovingAverageSimple(
            self.data, period=self.params.period)

        # 交叉信号指标
        self.crossover = bt.ind.CrossOver(self.data, self.move_average)

    def next(self):

        if not self.position:  # 还没有仓位
            # 当日收盘价上穿5日均线，创建买单，买入100股
            if self.crossover > 0:
                self.log('创建买单')
                self.buy(size=0.6)
        # 有仓位，并且当日收盘价下破5日均线，创建卖单，卖出100股
        elif self.crossover < 0:
            self.log('创建卖单')
            self.sell(size=0.6)


##########################
# 主程序开始
#########################

# 创建大脑引擎对象
cerebro = bt.Cerebro()

# 获取本脚本文件所在路径
modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
# 拼接得到数据文件全路径
datapath = os.path.join(modpath, './data.csv')

    # 创建行情数据对象，加载数据
data = GenericCSV_PE(
    dataname=datapath,
    datetime=2,  # 日期行所在列
    open=3,  # 开盘价所在列
    high=3,  # 最高价所在列
    low=3,  # 最低价所在列
    close=3,  # 收盘价价所在列
    volume=10,  # 成交量所在列
    openinterest=-1,  # 无未平仓量列
    pe=12,  # pe所在列
    dtformat=('%Y/%m/%d'),  # 日期格式
    fromdate=datetime(2016, 9, 12),  # 起始日
    todate=datetime(2021, 9, 10))  # 结束日
x = 0.002
cerebro.adddata(data)  # 将行情数据对象注入引擎
cerebro.addstrategy(SmaCross)  # 将策略注入引擎
cerebro.addanalyzer(bt.analyzers.PyFolio,_name='PyFolio')
cerebro.broker.setcash(1000.0)  # 设置初始资金
cerebro.broker.setcommission(x)  # 佣金费率
# 固定滑点，也可用cerebro.broker.set_slippage_perc()设置百分比滑点
cerebro.broker.set_slippage_fixed(0.05)
print('初始市值: %.2f' % cerebro.broker.getvalue())
cerebro.run()  # 运行
print('最终市值: %.2f' % cerebro.broker.getvalue())


thestrats = cerebro.run()
thestrat = thestrats[0]
portfolio_status = thestrat.analyzers.getbyname("PyFolio")
returns,positions,transactions,gross_lev = portfolio_status.get_pf_items()
returns.index = returns.index.tz_convert(None)
print(x)
print("rar%.4f" % qs.stats.rar(returns=returns))
print("sharpe%.4f" % qs.stats.sharpe(returns=returns,rf=0.0))

print("_________________________________________________________")
