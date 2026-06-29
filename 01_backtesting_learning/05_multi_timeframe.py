import datetime
import pandas_ta as ta
import pandas as pd
from backtesting import Backtest
from backtesting import Strategy
from backtesting.lib import FractionalBacktest, crossover, resample_apply
import matplotlib.pyplot as plt
from seaborn import heatmap
import talib


class RsiOscillator(Strategy):

    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    def init(self): # 初始化方法，在回测开始前执行一次，用于设置指标和变量
        # 1. 计算日线级别的 RSI 指标，周期为 14
        self.daily_rsi = self.I(
            talib.RSI, 
            self.data.Close, 
            timeperiod=self.rsi_window)

        # 2. 计算周线级别的 RSI 指标，周期同样为 14
        self.weekly_rsi = resample_apply(
            'W-SUN', ta.rsi, self.data.Close, self.rsi_window)
        

    def next(self): 
        
        # 卖出条件：当日线 RSI 出现超买信号，并且周线 RSI 也处于相对较高水平，
        # 表明整体趋势较弱，适合逢高卖出
        if (crossover(self.daily_rsi, self.upper_bound) and
                self.weekly_rsi[-1] > self.upper_bound):
            self.position.close()

        # 买入条件：当日线 RSI 出现超卖信号，并且周线 RSI 也处于相对较高水平，
        # 表明整体趋势仍然较强，适合逢低买入
        elif (crossover(self.lower_bound, self.daily_rsi) 
              and self.weekly_rsi[-1] > self.lower_bound):
            self.buy(size= 0.1)


# 1. 加载 1000 日的本地 BTC-USDT 历史数据
btc_df = pd.read_csv('btc_usdt_daily_lim1000.csv', index_col='date', parse_dates=True)
btc_df.columns = btc_df.columns.str.capitalize()

bt = FractionalBacktest(btc_df, RsiOscillator, cash=10000)


stats = bt.run()

print(stats)

bt.plot()