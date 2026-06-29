from datetime import datetime    # 从 datetime 模块导入 datetime 类，用于后续处理日期和时间。
import backtrader as bt         # 导入 backtrader 量化回测框架，并简写为 bt。
import pandas as pd             # 导入 pandas 数据分析库，并简写为 pd，用于处理表格数据。
import numpy as np              # 导入 numpy 数学计算库，并简写为 np（当前策略中虽未直接用到，但常用于 TA-Lib 传参）。
import talib                    # 导入 TA-Lib 技术指标库（当前使用的是 Backtrader 自带的 RSI，此行暂未用到）。

class RsiStrategy(bt.Strategy): # 创建一个名为 RsiStrategy 的自定义策略类，它继承自 Backtrader 的标准策略基类 bt.Strategy。
    params = (                  # 定义该策略的参数元组，方便后续在外部进行调整或参数调优。
        ('rsi_period', 14),     # 定义参数：RSI 指标的计算周期，默认设置为 14 天。
        ('rsi_overbought', 70), # 定义参数：RSI 的“超买”界限，默认设置为 70。
        ('rsi_oversold', 30),   # 定义参数：RSI 的“超卖”界限，默认设置为 30。
    )                           # 参数定义结束。

    def __init__(self):
        self.order = None
        # 1. 计算基本的 RSI 指标
        self.rsi = bt.indicators.RSI(self.datas[0].close, period=self.params.rsi_period)
        
        # 2. 【使用 CrossOver 替代点 1】：计算 RSI 向上突破 30 
        # 当 RSI 从下往上穿过 30 时，crossover_buy 会输出 1.0
        self.crossover_buy = bt.indicators.CrossOver(self.rsi, self.params.rsi_oversold)
        
        # 3. 【使用 CrossOver 替代点 2】：计算 RSI 向下跌破 70
        # 当 RSI 从上往下穿过 70 时，crossover_sell 会输出 -1.0
        self.crossover_sell = bt.indicators.CrossOver(self.rsi, self.params.rsi_overbought)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'【买入成功】时间: {self.data.datetime.date(0)} | 价格: {order.executed.price:.2f} | 数量: {order.executed.size:.4f}')
            else:
                print(f'【卖出成功】时间: {self.data.datetime.date(0)} | 价格: {order.executed.price:.2f} | 数量: {order.executed.size:.4f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(f'【订单失败】时间: {self.data.datetime.date(0)} —— 资金不足或点位错误！')
        self.order = None


# 1. 加载 1000 日的本地 BTC-USDT 历史数据
btc_df = pd.read_csv('btc_usdt_daily_lim1000.csv', index_col='date', parse_dates=True)
# print(btc_df.head())    

data_feed = bt.feeds.PandasData(dataname=btc_df)

cerebro = bt.Cerebro()
cerebro.addstrategy(RsiStrategy)

cerebro.adddata(data_feed)

# 设置初始配置（10000 USDT，币安千一手续费）
cerebro.broker.setcash(10000.0)
cerebro.broker.setcommission(commission=0.001)

print('==================== 开始 策略回测 ====================')

# 打印初始资金
initial_value = cerebro.broker.getvalue()
print('初始总资产 (USDT): %.2f' % initial_value)

# 运行回测并获取运行后的策略实例结果
results = cerebro.run()
strat = results[0]
print(strat)
# cerebro.plot()
