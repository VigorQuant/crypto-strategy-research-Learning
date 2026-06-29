import pandas_ta as ta # pip install pandas-ta
import pandas as pd
from backtesting import Backtest # pip install backtesting
from backtesting import Strategy
from backtesting.lib import FractionalBacktest, crossover




class RsiOscillator(Strategy):
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    # Do as much initial computation as possible
    def init(self):
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_window)


    # Step through bars one by one
    # Note that multiple buys are a thing here

    def next(self):
        if crossover(self.rsi, self.upper_bound):
            self.position.close()
        elif crossover(self.lower_bound, self.rsi):
            self.buy(size=0.1) # FractionalBacktest 支持部分仓位交易，提升策略的资金利用效率和风险控制能力


# 1. 加载 1000 日的本地 BTC-USDT 历史数据
btc_df = pd.read_csv('BTC_USDT_daily_from_2018-01-01.csv', index_col='date', parse_dates=True)
btc_df.columns = btc_df.columns.str.capitalize()

bt = FractionalBacktest(btc_df, RsiOscillator, cash=10000)

stats = bt.optimize(
    upper_bound = range(55, 85, 5),
    lower_bound = range(10, 45, 5),
    rsi_window = range(10, 30, 2),
    maximize = "Sharpe Ratio",
    constraint = lambda param: param.upper_bound > param.lower_bound
)

print(stats)
# bt.plot()


'''输出结果：
Start                     2018-01-01 00:00:00
End                       2026-06-08 00:00:00
Duration                   3080 days 00:00:00
Exposure Time [%]                     40.3765
Equity Final [$]                  33236.08019
Equity Peak [$]                   34103.62363
Return [%]                           232.3608
Buy & Hold Return [%]               452.38004
Return (Ann.) [%]                    15.29065
Volatility (Ann.) [%]                 11.3771
CAGR [%]                             15.29598
Sharpe Ratio                          1.34398
Sortino Ratio                         2.75104
Calmar Ratio                          1.43083
Alpha [%]                           197.45359
Beta                                  0.07716
Max. Drawdown [%]                   -10.68659
Avg. Drawdown [%]                    -1.53172
Max. Drawdown Duration      461 days 00:00:00
Avg. Drawdown Duration       25 days 00:00:00
# Trades                                    8
Win Rate [%]                            100.0
Best Trade [%]                      570.34131
Worst Trade [%]                      44.01921
Avg. Trade [%]                      163.74502
Max. Trade Duration         772 days 00:00:00
Avg. Trade Duration         330 days 00:00:00
Profit Factor                             NaN
Expectancy [%]                      213.82236
SQN                                   2.95328
Kelly Criterion                           NaN
_strategy                 RsiOscillator(up...
_equity_curve                             ...
_trades                         Size  Entr...
'''