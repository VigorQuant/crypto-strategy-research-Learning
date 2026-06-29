import requests
import pandas as pd

def get_funding(symbol="BTCUSDT", start_time=None, end_time=None):

    url = "https://fapi.binance.com/fapi/v1/fundingRate"

    params = {
        "symbol": symbol,
        "limit": 1000
    }

    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time

    res = requests.get(url, params=params)
    data = res.json()

    df = pd.DataFrame(data)

    df["fundingTime"] = pd.to_datetime(df["fundingTime"], unit="ms")
    df["fundingRate"] = df["fundingRate"].astype(float)

    return df[["fundingTime", "fundingRate"]]


get_funding('BTCUSDT', start_time='2018-1-1', end_time='2021-7-1')
