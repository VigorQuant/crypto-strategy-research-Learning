import numpy as np
import pandas as pd
import backtrader as bt

class OptimizedADXMomentum(bt.SignalStrategy):
    params = (
        ('adx_period', 14),
        ('di_period', 14),       # 已优化为14周期
        ('mom_period', 14),
        ('adx_threshold', 20),   # 已优化为20阈值
        ('di_threshold', 20),    # 已优化为20阈值
        ('stop_loss_pct', 0.04), # 4% 保护性止损
        ('take_profit_pct', 0.12),# 12% 动量波段止盈
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buy_price = None 

        # 指标计算
        self.adx = bt.indicators.DirectionalMovementIndex(self.datas[0], period=self.params.adx_period).adx
        dmi = bt.indicators.DirectionalMovement(self.datas[0], period=self.params.di_period)
        self.plus_di = dmi.plusDI
        self.minus_di = dmi.minusDI
        self.mom = bt.indicators.Momentum(self.dataclose, period=self.params.mom_period)

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price 
            else:
                self.buy_price = None 
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            condition_entry = (
                (self.adx[0] > self.params.adx_threshold) and
                (self.mom[0] > 0) and
                (self.plus_di[0] > self.params.di_threshold) and
                (self.plus_di[0] > self.minus_di[0])
            )
            if condition_entry:
                self.buy()
                
        else:
            current_pnl = (self.dataclose[0] - self.buy_price) / self.buy_price
            
            if current_pnl <= -self.params.stop_loss_pct:
                self.sell(size=self.position.size)
                return
                
            if current_pnl >= self.params.take_profit_pct:
                self.sell(size=self.position.size)
                return

            condition_exit = (
                (self.adx[0] > self.params.adx_threshold) and
                (self.mom[0] < 0) and
                (self.minus_di[0] > self.params.di_threshold) and
                (self.plus_di[0] < self.minus_di[0])
            )
            if condition_exit:
                self.sell(size=self.position.size)


# ==================== 自动化回测运行环境架设 ====================
btc_df = pd.read_csv('btc_usdt_daily_lim1000.csv', index_col='date', parse_dates=True)
data_feed = bt.feeds.PandasData(dataname=btc_df)

cerebro = bt.Cerebro()
cerebro.addstrategy(OptimizedADXMomentum)
cerebro.adddata(data_feed)

cerebro.broker.setcash(10000.0)
cerebro.broker.setcommission(commission=0.001)
cerebro.addsizer(bt.sizers.AllInSizer, percents=90)

# ----------------- 注入高级短线评估分析器 -----------------
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='my_sharpe', timeframe=bt.TimeFrame.Days, annualize=True)
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='my_drawdown')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='my_trades')
cerebro.addanalyzer(bt.analyzers.Returns, _name='my_returns')

print('==================== 开始高级短线动量回测 ====================')
initial_value = cerebro.broker.getvalue()

results = cerebro.run()
strat = results[0]

print('\n==================== 📊 短线动量策略终极评估报告 ====================')
final_value = cerebro.broker.getvalue()

# 1. 基础收益
total_return = (final_value - initial_value) / initial_value * 100
returns_analysis = strat.analyzers.my_returns.get_analysis()
cagr = returns_analysis.get('rnorm100', 0.0)

# 2. 核心风险控制
dd_analysis = strat.analyzers.my_drawdown.get_analysis()
max_dd = dd_analysis.get('max', {}).get('drawdown', 0.0)

# 计算卡玛比率 (Calmar Ratio)
calmar_ratio = cagr / max_dd if max_dd > 0 else 0.0

# 3. 效率与周转
trade_analysis = strat.analyzers.my_trades.get_analysis()

print(f"最终总资产: {final_value:.2f} USDT")
print(f"累计总收益率: {total_return:.2f}%")
print(f"复合年化收益率 (CAGR): {cagr:.2f}%")
print(f"历史最大回撤 (Max Drawdown): {max_dd:.2f}%")
print(f"卡玛比率 (Calmar Ratio): {calmar_ratio:.2f}  (及格线 >1.0, 优秀 >2.0)")

# 提取夏普比率
sharpe_analysis = strat.analyzers.my_sharpe.get_analysis()
print(f"💎 每日夏普比率 (Sharpe Ratio): {sharpe_analysis.get('sharperatio', 0.0) or 0.0:.2f}")

# 4. 交易结构与统计学期望
if 'total' in trade_analysis and trade_analysis['total']['total'] > 0:
    total_trades = trade_analysis['total']['total']
    won_trades = trade_analysis['won']['total']
    lost_trades = trade_analysis['lost']['total']
    win_rate = (won_trades / total_trades) * 100
    
    avg_win = trade_analysis['won']['pnl']['average']
    avg_loss = abs(trade_analysis['lost']['pnl']['average'])
    profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0
    
    # 提取最大连续亏损次数 (Consecutive Losses)
    # 使用 .get() 设定默认值，如果框架还没算出来连败纪录，默认显示 0，绝不崩溃
    lost_data = trade_analysis.get('lost', {})
    max_streak_loss = lost_data.get('streak', {}).get('max', 0)
    
    # 计算平均每笔盈利百分比 (Avg. Trade Return)
    # 用总盈利金额除以总资产再除以交易次数来估算
    avg_trade_pnl = trade_analysis['pnl']['net']['average']
    avg_trade_pct = (avg_trade_pnl / initial_value) * 100

    print(f"\n--- 🔄 交易结构与抗摩测试 ---")
    print(f"总交易笔数: {total_trades} 笔")
    print(f"策略实战胜率: {win_rate:.2f}%")
    print(f"真实盈亏比: {profit_loss_ratio:.2f}:1")
    print(f"最大连续割肉次数: {max_streak_loss} 次  (核心心理承受力指标)")
    print(f"平均每笔纯收益率: {avg_trade_pct:.2f}%  (必须显著大于手续费摩擦)")
    
    # 摩擦力健康度警告
    if avg_trade_pct < 0.2:
        print("🚨 警告: 每笔平均收益太低，实盘中极易被手续费和滑点吃精光！")
    else:
        print("✅ 提示: 每笔平均收益足以抵抗交易所常规摩擦成本。")
else:
    print("\n提示：当前参数在此周期内未触发任何完整交易。")
print('=====================================================================')


cerebro.plot()