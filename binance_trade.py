from market import Market
from coin import Coin
import json
import config
import logger
class BinanceTrade(Market) :
    def __init__(self, coinDict):
        Market.__init__(self)
        self.wsAddr = config.BINANCE_WSS_URL
        self.coinDict = coinDict
        self.coinList = list(coinDict.keys())

    def on_open(self, ws):
        logger.info("Check Binance Market for transaction information")
    
    def getData(self, data) :
        binanceDict = {}
        coinInfos = json.loads(data)
        for coinInfo in coinInfos :
            code = coinInfo['s']
            price = coinInfo['c']
            binanceDict[code] = float(price)
            
        if not 'BTCUSDT' in binanceDict :
            return
        
        for code, coin in self.coinDict.items() :
            if coin.price == 0 : 
                continue
            
            if not '-' in code :
                return

            market, coinname = code.split("-")
            binancePrice = config.USD_CURRENCY
            if market == 'KRW'  : 
                market = 'USDT'
            elif market == 'BTC' : 
                binancePrice *= binanceDict['BTCUSDT']

            if coinname + market in binanceDict : 
                binancePrice *= binanceDict[coinname + market]
                coin.setPremium(binancePrice)
