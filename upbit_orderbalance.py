from market import Market
from coin import Coin
import json
import config
import logger
class UpbitOrderBalance(Market) :
    def __init__(self, coinDict):
        Market.__init__(self)
        self.wsAddr = config.UPBIT_WSS_URL
        self.coinDict = coinDict
        self.coinList = list(coinDict.keys())

    def on_open(self, ws):
        logger.info("Check Upbit Market for order balance")
        message = json.dumps([{"ticket":"test"},{"type":"orderbook","codes": self.coinList}])
        self.sendMessage(message)
    
    def getData(self, data) :
        coinInfo = json.loads(data)
        key = coinInfo['code']
        if key in self.coinDict :
            coin = self.coinDict[key]
            coin.setOrderBalance(coinInfo['total_ask_size'], coinInfo['total_bid_size'])
