from backtesting import Backtest, Strategy
from backtesting.lib import crossover, FractionalBacktest# from backtesting.test import GOOG
import pandas as pd
import talib

import warnings
# 强行屏蔽 Bokeh 绘图组件和底层的用户警告提示，保持输出界面清爽
warnings.filterwarnings('ignore', category=UserWarning)

# 该策略实现了，基于 RSI 指标的超买超卖振荡器策略，核心逻辑是当 RSI 超过 70 时卖出，当 RSI 低于 30 时买入。
# 通过优化参数范围和引入交易结构分析，提升了策略的实战适应性和抗摩擦能力。
# 最后通过全面的绩效评估指标，验证了策略的稳健性和盈利潜力。

class RsiOscillator(Strategy): # 定义一个基于 RSI 的振荡器策略

    upper_bound = 70 
    lower_bound = 30

    def init(self): # 初始化方法，在回测开始前执行一次，用于设置指标和变量
        # 1. 计算 RSI 指标，周期为 14
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)

    def next(self): # 这里是核心逻辑，定义了每个时间点的交易决策
        
        if crossover(self.rsi, self.upper_bound):
            self.position.close() # 卖出后立即平仓，确保不持有空头仓位
        elif crossover(self.lower_bound, self.rsi):
            self.buy(size= 0.1) # 


# 1. 加载 1000 日的本地 BTC-USDT 历史数据
btc_df = pd.read_csv('BTC_USDT_daily_from_2018-01-01.csv', index_col='date', parse_dates=True)
btc_df.columns = btc_df.columns.str.capitalize()

bt = FractionalBacktest(btc_df, RsiOscillator, cash=10000)

stats = bt.run()
print(stats)

bt.plot()

