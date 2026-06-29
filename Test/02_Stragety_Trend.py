import pandas as pd
import numpy as np

# 集成了 TA-Lib 的 Backtrader 策略类
import backtrader as bt
import talib

'''
做多（买入）信号：
- 条件：
短期 EMA 12 向上突破（金叉）长期 EMA 26，并且 此时的 ADX 14 大于 25。
- 理由：
EMA 金叉代表短期多头力量开始占据绝对优势，趋势可能反转向上；
但均线交叉在震荡市中极易出现“假突破”频繁打脸，因此引入 ADX > 25 作为动能过滤器。
只有当 ADX 显示市场正处于“强趋势状态”时才允许开仓，从而过滤掉震荡市的无效信号。

平仓（卖出）信号：
- 条件：短期 EMA 12 向下跌破（死叉）长期 EMA 26。
- 理由：多头趋势已经瓦解，空头力量开始占优，必须无条件离场以保住利润、规避后续可能出现的暴跌。

'''

''' 核心指标
1. 短期指数移动平均线 (EMA 12)：由于 EMA 对近期价格变动的敏感度高于 SMA，我们用它来灵敏地捕捉短期价格趋势的启动。
2. 长期指数移动平均线 (EMA 26)：作为中期趋势的“分水岭”，用来过滤掉市场随机的噪音和短期震荡。平均趋向指数 (ADX 14)：用来衡量趋势的强弱。
3. ADX 无法告诉我们方向，但能告诉我们当前市场是在强劲趋势中，还是在无序震荡中。
'''

# ----------------- 2. 趋势跟踪策略编写 -----------------

class TrendStrategy(bt.Strategy):
    params = (
        ('fast_period', 12),  # 短期EMA周期
        ('slow_period', 26),  # 长期EMA周期
        ('adx_period', 14),   # ADX周期
        ('adx_threshold', 25) # 强趋势阈值
    )

    def __init__(self):
        # 保持对底层数据的引用
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        
        self.order = None  # 跟踪悬空订单

    def notify_order(self, order):
        """【修改 3】订单状态监听，防止策略因未重置订单状态而卡死"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'【买入成功】价格: {order.executed.price:.2f} | 数量: {order.executed.size:.4f}')
            else:
                print(f'【卖出成功】价格: {order.executed.price:.2f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(f'【订单失败】状态: {order.getstatusname()}')
        self.order = None

    def next(self):
        # 如果有订单在处理中，不进行新操作
        if self.order:
            return

        # --- 核心：动态调用 TA-Lib 计算指标 ---
        # 提取当前时间点及之前的所有历史价格数据（转为 numpy 数组满足 ta-lib 要求）
        closes = np.array(self.dataclose.get(size=len(self.dataclose)))
        highs = np.array(self.datahigh.get(size=len(self.datahigh)))
        lows = np.array(self.datalow.get(size=len(self.datalow)))

        # 确保有足够的数据计算指标
        if len(closes) < self.params.slow_period + self.params.adx_period:
            return

        # 使用 ta-lib 计算均线和 ADX
        ema_fast = talib.EMA(closes, timeperiod=self.params.fast_period)
        ema_slow = talib.EMA(closes, timeperiod=self.params.slow_period)
        adx = talib.ADX(highs, lows, closes, timeperiod=self.params.adx_period)

        # 获取当前最新的指标值（即 numpy 数组的最后一位 [-1]）
        current_ema_fast = ema_fast[-1]
        current_ema_slow = ema_slow[-1]
        current_adx = adx[-1]

        # 获取上一个周期的指标值（用于判断交叉情况 [-2]）
        prev_ema_fast = ema_fast[-2]
        prev_ema_slow = ema_slow[-2]

        # --- 交易逻辑判断 ---
        if not self.position:
            # 1. 做多条件：短期均线上穿长期均线（金叉） 且 ADX 指示强趋势(>25)
            is_gold_cross = (prev_ema_fast <= prev_ema_slow) and (current_ema_fast > current_ema_slow)
            is_strong_trend = current_adx > self.params.adx_threshold

            if is_gold_cross and is_strong_trend:
                # 动态仓位管理：使用 95% 的现金买入，预留 5% 应对加密货币的手续费和滑点
                cash = self.broker.get_cash()
                crypto_size = (cash * 0.95) / self.dataclose[0]
                print(f"【触发信号】金叉出现且ADX={current_adx:.2f}为强趋势，尝试买入...")
                self.order = self.buy(size=crypto_size)
        else:
            # 2. 平仓条件：短期均线下穿长期均线（死叉）
            is_death_cross = (prev_ema_fast >= prev_ema_slow) and (current_ema_fast < current_ema_slow)
            
            if is_death_cross:
                print(f"【触发信号】死叉出现，趋势走弱，全仓平仓...")
                self.order = self.sell(size=self.position.size)


# ----------------- 3. 回测环境配置与运行 -----------------
df = pd.read_csv('btc_usdt_daily_lim300.csv', index_col='date', parse_dates=True)
print(df.head())
data = bt.feeds.PandasData(dataname=df)
cerebro = bt.Cerebro()

# 注入策略与数据
cerebro.addstrategy(TrendStrategy)
cerebro.adddata(data)

# 设置初始配置（10000 USDT，币安千一手续费）
cerebro.broker.setcash(10000.0)
cerebro.broker.setcommission(commission=0.001)

# 打印初始资金
print('开始回测，初始总资产 (USDT): %.2f' % cerebro.broker.getvalue())

# 运行回测
cerebro.run()

# 打印回测结果并绘图
print('回测结束，最终总资产 (USDT): %.2f' % cerebro.broker.getvalue())
cerebro.plot(style='candlestick')
