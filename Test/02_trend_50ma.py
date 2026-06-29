from datetime import datetime
import backtrader as bt
import pandas as pd

'''
BTC-USDT 50日均线策略回测示例

策略逻辑：
- 买入条件：当 BTC-USDT 的收盘价上穿 50 日简单移动平均线时，买入 90% 可用资金的 BTC。
- 卖出条件：当 BTC-USDT 的收盘价下穿 50 日简单移动平均线时，卖出全部持仓。
回测设置：
- 初始资金：10000 USDT
- 交易手续费：0.1%（币安现货交易费率） 
- 数据范围：使用本地 CSV 文件中的 BTC-USDT 日线数据，包含 1000 条记录。
绩效评估：
- 总收益率
- 年化收益率
- 夏普比率
- 最大回撤
- 胜率
- 盈亏比
'''

class SmaCross(bt.SignalStrategy):

    def __init__(self):
        sma = bt.ind.SMA(self.data.close, period=50)
        price = self.data.close 

        crossover = bt.ind.CrossOver(price, sma) # 价格与均线的交叉指标
        self.signal_add(bt.SIGNAL_LONG, crossover) # 将交叉信号添加到策略中，作为做多信号

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'【买入成功】时间: {self.data.datetime.date(0)} | 价格: {order.executed.price:.2f} | 数量: {order.executed.size:.4f}')
            else:
                print(f'【卖出成功】时间: {self.data.datetime.date(0)} | 价格: {order.executed.price:.2f} | 数量: {order.executed.size:.4f}')
        elif order.status in [order.Margin, order.Rejected]:
            print(f'【订单被拒】时间: {self.data.datetime.date(0)} —— 资金不足或点位错误！')


# 1. 加载 1000 日的本地 BTC-USDT 历史数据
btc_df = pd.read_csv('btc_usdt_daily_lim300.csv', index_col='date', parse_dates=True)
print(btc_df.head())    

data_feed = bt.feeds.PandasData(dataname=btc_df)

cerebro = bt.Cerebro()
cerebro.addstrategy(SmaCross)

cerebro.adddata(data_feed)

# 设置初始配置（10000 USDT，币安千一手续费）
cerebro.broker.setcash(10000.0)
cerebro.broker.setcommission(commission=0.001)

# 添加百分比仓位管理器：每次买入使用可用资金的 90%
cerebro.addsizer(bt.sizers.AllInSizer, percents=90)

# 2. 添加分析器 backtrader.analyzers

# 夏普比率分析器 (假设无风险利率为 0)
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='my_sharpe', timeframe=bt.TimeFrame.Days, annualize=True, riskfreerate=0.0)

# 最大回撤分析器
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='my_drawdown')

# 交易详情分析器 (用于计算胜率、盈亏比)
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='my_trades')

# 年度回报分析器
cerebro.addanalyzer(bt.analyzers.Returns, _name='my_returns')
# ------------------------------------------------------------------------


print('==================== 开始 策略回测 ====================')

# 打印初始资金
initial_value = cerebro.broker.getvalue()
print('初始总资产 (USDT): %.2f' % initial_value)

# 运行回测并获取运行后的策略实例结果
results = cerebro.run()
strat = results[0] # 获取第一个策略实例


print('\n==================== 策略绩效评估报告 ====================')
final_value = cerebro.broker.getvalue()
print('回测结束总资产 (USDT): %.2f' % final_value)

# 1. 提取并打印【总收益率】与【年化收益率】
returns_analysis = strat.analyzers.my_returns.get_analysis()
total_return = (final_value - initial_value) / initial_value * 100
print(f"总收益率 (Total Return): {total_return:.2f}%")
# rlog 为对数连续年化收益率，转换为普通百分比年化收益率
if 'rnorm100' in returns_analysis:
    print(f"年化收益率 (CAGR): {returns_analysis['rnorm100']:.2f}%")

# 2. 提取并打印【夏普比率】
sharpe_analysis = strat.analyzers.my_sharpe.get_analysis()
sharpe_ratio = sharpe_analysis.get('sharperatio', 0.0)
print(f"夏普比率 (Sharpe Ratio): {sharpe_ratio if sharpe_ratio is not None else 0.0:.2f}")

# 3. 提取并打印【最大回撤】
dd_analysis = strat.analyzers.my_drawdown.get_analysis()
max_dd = dd_analysis.get('max', {}).get('drawdown', 0.0)
print(f"最大回撤 (Max Drawdown): {max_dd:.2f}%")

# 4. 提取并打印【胜率】与【盈亏比】
trade_analysis = strat.analyzers.my_trades.get_analysis()

# 确保有交易发生才进行计算，防止除以 0 报错
if 'total' in trade_analysis and trade_analysis['total']['total'] > 0:
    total_trades = trade_analysis['total']['total']
    won_trades = trade_analysis['won']['total']
    lost_trades = trade_analysis['lost']['total']
    
    # 计算胜率
    win_rate = (won_trades / total_trades) * 100
    print(f"总交易笔数 (Total Trades): {total_trades}")
    print(f"胜率 (Win Rate): {win_rate:.2f}% (胜: {won_trades} / 败: {lost_trades})")
    
    # 计算盈亏比 (总盈利金额的平均值 / 总亏损金额的平均值)
    avg_win = trade_analysis['won']['pnl']['average']
    
    # 框架返回的亏损通常是负数，取绝对值计算比例
    avg_loss = abs(trade_analysis['lost']['pnl']['average']) 
    
    if avg_loss > 0:
        profit_loss_ratio = avg_win / avg_loss
        print(f"平均每笔盈利 (Avg Win): {avg_win:.2f} USDT")
        print(f"平均每笔亏损 (Avg Loss): {avg_loss:.2f} USDT")
        print(f"盈亏比 (Profit-Loss Ratio): {profit_loss_ratio:.2f}:1")
    else:
        print("盈亏比 (Profit-Loss Ratio): 无法计算 (没有发生过亏损的交易)")
else:
    print("提示：在当前回测周期内，策略未触发任何完整的买入平仓交易。")
print('==========================================================')

# cerebro.plot(style='candlestick')
cerebro.plot()


