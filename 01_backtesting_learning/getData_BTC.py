import pandas as pd
from datetime import datetime
import backtrader as bt
import matplotlib.pyplot as plt


# import tushare as ts
import ccxt
import talib


# 修复中文标签
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False 

# ----------------- 1. 获取币安历史数据 -----------------
def fetch_binance_data(symbol='BTC/USDT', timeframe='1h',limit = 50000):
    """
    使用 CCXT 无需 API Key 获取币安公开 K 线数据
    timeframe 可选: '1m', '5m', '1h', '4h', '1d' 等
    """
    # 初始化币安交易所对象 (开启自带限速，防止被交易所封 IP)
    exchange = ccxt.binance({'enableRateLimit': True})
    
    print(f"正在从币安获取 {symbol} 的 {timeframe} K线数据...")
    # fetch_ohlcv 返回结构: [时间戳, 开盘, 最高, 最低, 收盘, 成交量]
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe,limit=limit)  
    
    # 转换为 DataFrame
    cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    df = pd.DataFrame(ohlcv, columns=cols)
    
    # 将时间戳转换为可读的时间并设为索引
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    df.drop(columns=['timestamp'], inplace=True)
    
    # 增加 openinterest 列以符合 Backtrader 标准
    df['openinterest'] = 0

    return df


# df = fetch_binance_data(symbol='BTC/USDT', timeframe='1h',limit=50000)
# df.to_csv('btc_usdt_1D_data.csv')

# ----------------- 1. 循环获取币安 10 年日线数据 (Daily) -----------------

import time


# ----------------- 升级版：支持指定精确日期开始 -----------------
def fetch_binance_daily_from_date(symbol='BTC/USDT', start_date_str='2018-01-01'):
    """
    通过指定任意具体开始日期（格式: YYYY-MM-DD），获取至今的 Daily 日线数据
    """
    timeframe = '1d'
    exchange = ccxt.binance({'enableRateLimit': True, 'timeout': 30000})
    
    # 【核心修改点】将输入的精确字符串日期转换为毫秒级时间戳
    try:
        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError("❌ 日期格式错误！请输入标准的 'YYYY-MM-DD' 格式，例如 '2018-01-01'")
        
    since_timestamp = int(start_dt.timestamp() * 1000)
    now_timestamp = exchange.milliseconds()
    
    all_ohlcv = []
    limit = 1000  
    
    print(f"🚀 开始从币安获取 {symbol} 自 【{start_date_str}】 至今的 Daily 日线数据...")
    
    while since_timestamp < now_timestamp:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_timestamp, limit=limit)
            if not ohlcv or len(ohlcv) == 0:
                break
            all_ohlcv.extend(ohlcv)
            
            # 推移时间戳
            last_timestamp = ohlcv[-1][0] # 最后一条数据的时间戳
            since_timestamp = last_timestamp + 1
            
            current_date_str = datetime.fromtimestamp(last_timestamp / 1000).strftime('%Y-%m-%d')
            print(f"📥 已成功同步日线至: {current_date_str} | 累计已下载: {len(all_ohlcv)} 天数据", end='\r')
            
            time.sleep(exchange.rateLimit / 1000)
        except Exception as e:
            print(f"\n⚠️ 网络闪断，重试中... 原因: {e}")
            time.sleep(5)
            continue
            
    print("\n\n📊 开始清洗日线数据...")
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    df.drop(columns=['timestamp'], inplace=True)
    df['openinterest'] = 0
    df = df[~df.index.duplicated(keep='first')]
    
    return df

# ----------------- 执行下载（这里可以修改为你想要的任意日期） -----------------
# 示例：你想从 2018 年 1 月 1 日开始看后续的大牛市：
my_start_date = '2018-01-01' 

df_custom = fetch_binance_daily_from_date(symbol='BTC/USDT', start_date_str=my_start_date)

# 自动以开始日期命名文件，防止数据覆盖混淆
file_output = f"BTC_USDT_daily_from_{my_start_date}.csv"
df_custom.to_csv(file_output)

print(f"🎉 抓取成功！数据已保存至：【{file_output}】")
print(df_custom.head(3))



