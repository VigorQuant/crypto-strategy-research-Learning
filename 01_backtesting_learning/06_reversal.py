import datetime
import pandas_ta as ta
import pandas as pd
from backtesting import Backtest
from backtesting import Strategy
from backtesting.lib import FractionalBacktest, crossover, resample_apply,barssince
import matplotlib.pyplot as plt
import talib



class RsiOscillator(Strategy):

    upper_bound = 70
    lower_bound = 30
    rsi_window = 14
    position_size = 0.1

    def init(self): # 初始化方法，在回测开始前执行一次，用于设置指标和变量
        # 1. 计算日线级别的 RSI 指标，周期为 14
        self.daily_rsi = self.I(
            talib.RSI, 
            self.data.Close, 
            timeperiod=self.rsi_window)

    def next(self):
        # 获取当前价格
        price = self.data.Close[-1]

        if (self.daily_rsi[-1] > self.upper_bound and
                barssince(self.daily_rsi < self.upper_bound == 3)):
                self.position.close()

        elif crossover(self.lower_bound, self.daily_rsi):
                
                # 设置止损价为当前价格的 80%，即止损点为 20% 的亏损，
                # size 参数设置为 0.1，表示买入 10% 的仓位
                self.buy(size=self.position_size)
            



# 1. 加载 1000 日的本地 BTC-USDT 历史数据
btc_df = pd.read_csv('BTC_USDT_daily_from_2018-01-01.csv', index_col='date', parse_dates=True)
btc_df.columns = btc_df.columns.str.capitalize()

bt = FractionalBacktest(btc_df, RsiOscillator, cash=10000)


stats = bt.run()

# print(stats['_trades'])

bt.plot()