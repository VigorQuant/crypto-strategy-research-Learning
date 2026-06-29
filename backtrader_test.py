import pandas as pd
from datetime import datetime
import backtrader as bt
import matplotlib.pyplot as plt

# import tushare as ts
import ccxt
import talib



plt.rcParams['font.sans-serif'] = ['SimHei'] #显示中文标签
plt.rcParams['axes.unicode_minus'] = False #显示负号

# 1. 数据加载
def get_data(code = '600519',starttime = '2017-01-01',endtime = '2020-01-01'):
    df = ts.get_k_data(code, start=starttime, end=endtime)
    df.index = pd.to_datetime(df['date'])
    df['openinterest'] = 0
    # 对数据进行排序，保证时间顺序正确
    df = df['open high low close volume openinterest'.split()]
    # OHLCV数据必须按照时间顺序排列，且列名必须为open、high、low、close、volume和openinterest
    return df


stock_df = get_data()
# 加载并读取数据源,fromdata,todate
fromdate=datetime(2017, 1, 1)
todate=datetime(2020, 1, 1)
data = bt.feeds.PandasData(dataname=stock_df,fromdate=fromdate,todate=todate)

# 2. 策略编写
# 上穿20日均线买入，下穿20日均线卖出
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 20), #均线周期
    )

    def __init__(self):
        self.order = None #订单
        self.ma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod) #均线指标


    # 交易逻辑，每个bar都会执行一次，回测的每个日期都会执行一次
    def next(self):
        if(self.order): #如果有订单在执行中，返回
            return

        if not self.position: #如果没有持仓
            if self.dataclose[0] > self.ma[0]: #如果收盘价上穿均线
                self.order = self.buy(size=200) #买入

        else: #如果有持仓
            if self.dataclose[0] < self.ma[0]: #如果收盘价下穿均线
                self.order = self.sell(size=200) #卖出


# 3. 策略设置
cerebro = bt.Cerebro() #创建Cerebro引擎
cerebro.addstrategy(TestStrategy) #添加策略

cerebro.adddata(data) #添加数据

cerebro.broker.setcash(100000.0) #设置初始资金

cerebro.broker.setcommission(commission=0.002) #设置佣金

# 4. 运行回测
print('初始资金: %.2f' % cerebro.broker.getvalue())

s = fromdate.strftime('%Y-%m-%d')
t = todate.strftime('%Y-%m-%d')
print('回测时间: %s - %s' % (s, t))

cerebro.run() #运行回测

print('回测结束，最终资金: %.2f' % cerebro.broker.getvalue())
cerebro.plot() #绘制图形




