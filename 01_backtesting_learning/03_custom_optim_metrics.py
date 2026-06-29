from backtesting import Backtest, Strategy
from backtesting.lib import crossover, FractionalBacktest # from backtesting.test import GOOG
import pandas as pd
import talib

# stragety optimization

def optim_func(series):

    # 交易次数过少的策略不予考虑，避免过拟合
    if series['# Trades'] < 10: 
        return -float('inf') 

    # 以最终资产和暴露时间的比率 作为优化目标，兼顾收益和风险
    return series['Equity Final [$]'] / series['Exposure Time [%]'] 


class RsiOscillator(Strategy):

    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    def init(self): # 初始化方法，在回测开始前执行一次，用于设置指标和变量
        # 1. 计算 RSI 指标，周期为 14
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_window)

    def next(self): # 这里是核心逻辑，定义了每个时间点的交易决策
        
        if crossover(self.rsi, self.upper_bound):
            self.position.close() # 卖出后立即平仓，确保不持有空头仓位
        elif crossover(self.lower_bound, self.rsi):
            self.buy(size=0.1) # 买入 0.1 个 BTC，
            # 使用 FractionalBacktest 支持部分仓位交易，提升策略的资金利用效率和风险控制能力


# 1. 加载 1000 日的本地 BTC-USDT 历史数据
btc_df = pd.read_csv('btc_usdt_daily_lim1000.csv', index_col='date', parse_dates=True)
btc_df.columns = btc_df.columns.str.capitalize()

bt = FractionalBacktest(btc_df, RsiOscillator, cash=10000)


stats = bt.optimize(
    upper_bound=range(50, 85, 5), 
    lower_bound=range(10, 45, 5),
    rsi_window=range(10, 30, 2), # RSI 周期从 10 到 20
    maximize=optim_func, # 优化目标：最大化最终资产
    constraint = lambda param: param.upper_bound - param.lower_bound >= 20,
    # Random Grid Search
    # max_tries = 100, # 限制优化尝试次数，避免过度拟合和计算资源浪费

)

print(stats)

bt.plot()