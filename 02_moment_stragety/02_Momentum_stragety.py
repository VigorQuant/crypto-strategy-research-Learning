import numpy as np
import pandas as pd
import backtrader as bt

class OptimizedADXMomentum(bt.SignalStrategy):
    params = (
            ('adx_period', 14),
            ('di_period', 14),       # 【修改】从 25 缩短到 14（标准的DMI周期，大幅提升灵敏度）
            ('mom_period', 14),
            ('adx_threshold', 20),   # 【修改】从 25 降低到 20（让牛市主升浪初期更容易触发）
            ('di_threshold', 20),    # 【修改】从 25 降低到 20
            ('stop_loss_pct', 0.04), # 4% 保护性止损
            ('take_profit_pct', 0.12),# 12% 动量波段止盈（放大盈利空间）
        )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buy_price = None # 记录买入成本价

        # 指标计算
        self.adx = bt.indicators.DirectionalMovementIndex(self.datas[0], period=self.params.adx_period).adx
        dmi = bt.indicators.DirectionalMovement(self.datas[0], period=self.params.di_period)
        self.plus_di = dmi.plusDI
        self.minus_di = dmi.minusDI
        self.mom = bt.indicators.Momentum(self.dataclose, period=self.params.mom_period)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price # 记录进场价
                print(f'【动量开多】时间: {self.data.datetime.datetime(0)} | 价格: {self.buy_price:.2f}')
            else:
                self.buy_price = None # 清空进场价
                print(f'【动量平仓】时间: {self.data.datetime.datetime(0)} | 价格: {order.executed.price:.2f}')
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # 严格保持原开仓动量逻辑
            condition_entry = (
                (self.adx[0] > self.params.adx_threshold) and
                (self.mom[0] > 0) and
                (self.plus_di[0] > self.params.di_threshold) and
                (self.plus_di[0] > self.minus_di[0])
            )
            if condition_entry:
                self.buy()
                
        else:
            # --- 【主动风控优化点】优先触发止盈止损检查 ---
            current_pnl = (self.dataclose[0] - self.buy_price) / self.buy_price
            
            if current_pnl <= -self.params.stop_loss_pct:
                print(f">> [风控触发] 达到 4% 止损线，强制割肉保本！")
                self.sell(size=self.position.size)
                return
                
            if current_pnl >= self.params.take_profit_pct:
                print(f">> [风控触发] 达到 12% 止盈线，锁定动量暴利！")
                self.sell(size=self.position.size)
                return

            # 原策略的常规指标平仓逻辑（保留作为双重保险）
            condition_exit = (
                (self.adx[0] > self.params.adx_threshold) and
                (self.mom[0] < 0) and
                (self.minus_di[0] > self.params.di_threshold) and
                (self.plus_di[0] < self.minus_di[0])
            )
            if condition_exit:
                self.sell(size=self.position.size)

# ==================== 运行环境架设 ====================
btc_df = pd.read_csv('btc_usdt_1h_data.csv', index_col='date', parse_dates=True)
data_feed = bt.feeds.PandasData(dataname=btc_df)

cerebro = bt.Cerebro()
cerebro.addstrategy(OptimizedADXMomentum)
cerebro.adddata(data_feed)
cerebro.broker.setcash(10000.0)
cerebro.broker.setcommission(commission=0.001)
cerebro.addsizer(bt.sizers.AllInSizer, percents=90)

cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='my_sharpe', timeframe=bt.TimeFrame.Days, annualize=True)
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='my_drawdown')

print('==================== 开始 优化版ADX动量回测 ====================')
results = cerebro.run()
strat = results[0]

print('\n==================== 优化后绩效评估报告 ====================')
print('结束资产 (USDT): %.2f' % cerebro.broker.getvalue())
dd_analysis = strat.analyzers.my_drawdown.get_analysis()
print(f"最大回撤 (Max Drawdown): {dd_analysis.get('max', {}).get('drawdown', 0.0):.2f}%")

cerebro.plot()