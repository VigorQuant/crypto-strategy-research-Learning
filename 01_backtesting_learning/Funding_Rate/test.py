from funding_rate_arbitrage.frarb import FundingRateArbitrage
import ccxt
import time

fr = FundingRateArbitrage()

# # 示例1: 查看单交易所高资金费率分化（spot vs perp，常用于基础套利）
# print("Bybit 高分化机会:")
# fr.display_large_divergence_single_exchange(exchange='bybit', display_num=5)

# # 示例2: 跨交易所分化（核心套利机会）
# print("\n跨 CEX 高分化:")
# fr.display_large_divergence_multi_exchange(display_num=5, sorted_by='revenue')

# 示例3: 获取 BTC 具体数据
btc_rates = fr.fetch_all_funding_rate(exchange='binance')  # 或 'bybit' 等
print(btc_rates.get('BTC/USDT:USDT'))  # 查看当前费率