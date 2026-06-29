import backtrader as bt

class FundingData(bt.feeds.PandasData):

    lines = ('funding_rate',)

    params = (
        ('datetime', None),
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1),
        ('funding_rate', -1),
    )

class FundingStrategy(bt.Strategy):

    params = dict(
        threshold=0.0001
    )

    def __init__(self):
        self.funding = self.datas[0].funding_rate

    def next(self):

        fr = self.funding[0]

        # === 开仓条件 ===
        if fr > self.p.threshold and not self.position:

            # Long spot (simulated)
            self.buy()

            # Short perp (simulated hedge)
            self.sell()

        # === 平仓条件 ===
        elif fr <= 0 and self.position:

            self.close()





data = load_data()

cerebro = bt.Cerebro()

feed = FundingData(dataname=data)
cerebro.adddata(feed)

cerebro.addstrategy(FundingStrategy)

cerebro.broker.set_cash(10000)

results = cerebro.run()

cerebro.plot()