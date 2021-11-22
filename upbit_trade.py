from market import Market
from coin import Coin
import json
import config
import logger
class UpbitTrade(Market) :
    def __init__(self, coinDict):
        Market.__init__(self)
        self.wsAddr = config.UPBIT_WSS_URL
        self.coinDict = coinDict
        self.coinList = []

    def getMarketInfo(self) :
        logger.info("Try to acquire upbit market information")
        marketData = self.getRequest(config.UPBIT_MARKET_ALL_URL)
        marketData = str(marketData).replace("\'", "\"")
        coinInfoDict = json.loads(marketData)
        self.coinList = []
        for coinInfo in coinInfoDict :
            key = coinInfo['market']
            if not key in self.coinDict : 
                coin = Coin()
                coin.market = config.MARKET_UPBIT_NAME
                coin.marketCode = coinInfo['market']
                coin.code = coinInfo['market'].replace("KRW-","").replace("USDT-","").replace("BTC-","").replace("ETH-","")
                coin.koranName = coinInfo['korean_name']
                coin.englishName = coinInfo['english_name']
                #coin.baseTime = ...
                self.coinDict[key] = coin
        self.coinList = list(self.coinDict.keys())

    def on_open(self, ws):
        self.setExchangeRate()
        self.getMarketInfo()
        logger.info("Check Upbit Market for transaction information")
        message = json.dumps([{"ticket":"test"},{"type":"trade","codes": self.coinList}])
        self.sendMessage(message)
    
    def getData(self, data) :
        coinInfo = json.loads(data)
        key = coinInfo['code']
        if key in self.coinDict :
            if key == "KRW-BTC" : 
                config.BTC_CURRENCY = coinInfo['trade_price']
            elif key == "KRW-ETH" : 
                config.ETH_CURRENCY = coinInfo['trade_price']

            coin = self.coinDict[key]
            tradeTime = int(str(coinInfo['trade_timestamp'])[:-3])
            tradeTimeStr = coinInfo['trade_date'] + ' ' + coinInfo['trade_time']
            coin.addTradeTime(tradeTime, tradeTimeStr)
            coin.setPrice(tradeTime, coinInfo['trade_price'])
            if coinInfo['ask_bid'] == "BID" :
                coin.setBuyVolume(tradeTime, coinInfo['trade_price'])
            else : 
                coin.setSellVolume(tradeTime, coinInfo['trade_price'])
            coin.sync()
