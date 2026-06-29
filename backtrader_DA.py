import pandas as pd
from datetime import datetime
import backtrader as bt
import matplotlib.pyplot as plt

# import tushare as ts
import ccxt

# 修复中文标签
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False 

# ----------------- 1. 获取币安历史数据 -----------------
def fetch_binance_data(symbol='BTC/USDT', timeframe='1d', limit=100):
    """
    使用 CCXT 无需 API Key 获取币安公开 K 线数据
    timeframe 可选: '1m', '5m', '1h', '4h', '1d' 等
    """
    # 初始化币安交易所对象 (开启自带限速，防止被交易所封 IP)
    exchange = ccxt.binance({'enableRateLimit': True})
    
    print(f"正在从币安获取 {symbol} 的 {timeframe} K线数据...")
    # fetch_ohlcv 返回结构: [时间戳, 开盘, 最高, 最低, 收盘, 成交量]
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    
    # 转换为 DataFrame
    cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    df = pd.DataFrame(ohlcv, columns=cols)
    
    # 将时间戳转换为可读的时间并设为索引
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    df.drop(columns=['timestamp'], inplace=True)
    
    return df


# 获取最近 100 天的 BTC 日线数据
df = fetch_binance_data(symbol='BTC/USDT', timeframe='1d', limit=100)
# print(df.head(5))



# ----------------- 2. 简单的数据分析 -----------------
# 计算 20 日移动平均线 (MA20)
df['MA20'] = df['close'].rolling(window=20).mean()

# 计算布林带 (Bollinger Bands)
df['STD20'] = df['close'].rolling(window=20).std()
df['Upper_Band'] = df['MA20'] + (df['STD20'] * 2) # 上轨
df['Lower_Band'] = df['MA20'] - (df['STD20'] * 2) # 下轨

# 打印最近 5 天的分析结果
print("\n--- 最近 5 天的分析数据 ---")
print(df[['open', 'close', 'MA20', 'Upper_Band', 'Lower_Band']].tail())


# ----------------- 3. 可视化分析结果 -----------------
plt.figure(figsize=(12, 6))

# 绘制收盘价和均线
plt.plot(df.index, df['close'], label='BTC 收盘价', color='blue', linewidth=1.5)
plt.plot(df.index, df['MA20'], label='20日均线 (MA20)', color='orange', linestyle='--')

# 绘制布林带上下轨
plt.plot(df.index, df['Upper_Band'], label='布林带上轨 (压力线)', color='green', alpha=0.6)
plt.plot(df.index, df['Lower_Band'], label='布林带下轨 (支撑线)', color='red', alpha=0.6)

# 填充布林带区间
plt.fill_between(df.index, df['Lower_Band'], df['Upper_Band'], color='gray', alpha=0.1)

plt.title('币安 BTC/USDT 历史走势与布林带分析')
plt.xlabel('日期')
plt.ylabel('价格 (USDT)')
plt.legend(loc='upper left')
plt.grid(True, alpha=0.3)

plt.show()