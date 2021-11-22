import datetime
import config
import queue
import time

class Coin :
    def __init__(self) :
        self.market = ""
        self.marketCode = ""

        self.code = ""
        self.koranName = ""
        self.englishName = ""
        self.baseTime = 60

        self.price = 0.0
        self.krwPrice = 0.0

        self.tradeDateTime = datetime.datetime.now()
        self.tradeDateTimeStr = ""
        self.buyVolume = 0.0
        self.sellVolume = 0.0
        self.tradeVolume = 0.0
        self.basePrice = 0.0
        self.difference = 0.0
        self.rate = 0.0
        self.speed = 0
        self.orderBalance = 0.5
        self.premium = 0.0

        self.buyVolumeDict = {}
        self.sellVolumeDict = {}
        self.priceDict = {}
        self.tradeTimeQ = queue.Queue()

    def getJson(self) : 
        jsonData = {}
        jsonData["marketCode"] = self.marketCode
        jsonData["code"] = self.code
        jsonData["koranName"] = self.koranName
        jsonData["englishName"] = self.englishName
        jsonData["krwPrice"] = self.krwPrice
        jsonData["buyVolume"] = self.buyVolume
        jsonData["sellVolume"] = self.sellVolume
        jsonData["tradeVolume"] = self.tradeVolume
        jsonData["basePrice"] = self.basePrice
        jsonData["difference"] = self.difference
        jsonData["rate"] = self.rate
        jsonData["speed"] = self.speed
        jsonData["orderBalance"] = self.orderBalance
        jsonData["premium"] = self.premium
        jsonData["tradeDateTimeStr"] = self.tradeDateTimeStr
        jsonData["tradeDateTime"] = self.tradeDateTime
        return jsonData

    def addTradeTime(self, time, timeStr) : 
        self.tradeTimeQ.put(time)
        self.tradeDateTime = time
        self.tradeDateTimeStr = timeStr

    def setPrice(self, time, price) :
        if self.market == config.MARKET_UPBIT_NAME :
            if self.price == 0.0 :
                self.basePrice = price
            self.difference = ((price / self.basePrice) -1) * 100
            self.priceDict[time] = price
            self.price = price
            if "KRW-" in self.marketCode : 
                self.krwPrice = price
            elif "USDT-" in self.marketCode : 
                self.krwPrice = price * config.USD_CURRENCY
            elif "BTC-" in self.marketCode : 
                self.krwPrice = price * config.BTC_CURRENCY
            elif "ETH-" in self.marketCode : 
                self.krwPrice = price * config.ETH_CURRENCY

    def setBuyVolume(self, time, buyVolume) : 
        if buyVolume * self.krwPrice <= config.BOT_FILTER_PRICE : 
            return
        
        if time in self.buyVolumeDict :
            self.buyVolumeDict[time] += buyVolume
        else : 
            self.buyVolumeDict[time] = buyVolume
        self.buyVolume += buyVolume

    def setSellVolume(self, time, sellVolume) : 
        if sellVolume * self.krwPrice <= config.BOT_FILTER_PRICE : 
            return
        
        if time in self.sellVolumeDict :
            self.sellVolumeDict[time] += sellVolume
        else : 
            self.sellVolumeDict[time] = sellVolume
        self.sellVolume += sellVolume

    def setOrderBalance(self, totalAskSize, totalBidSize) : 
        self.orderBalance = totalAskSize / (totalAskSize + totalBidSize)

    def setPremium(self, foreignPrice ) : 
        self.premium = ((self.krwPrice / foreignPrice) -1) * 100

    def sync(self) : 
        while not self.tradeTimeQ.empty() :
            curTime = int(time.time()) 
            tradeTime = self.tradeTimeQ.queue[0]
            if curTime - tradeTime > self.baseTime :
                self.tradeTimeQ.get()
                if tradeTime in self.buyVolumeDict :
                    self.buyVolume -= self.buyVolumeDict[tradeTime]
                    del self.buyVolumeDict[tradeTime]
                if tradeTime in self.sellVolumeDict :
                    self.sellVolume -= self.sellVolumeDict[tradeTime]
                    del self.sellVolumeDict[tradeTime]
                if tradeTime in self.priceDict :
                    self.basePrice = self.priceDict[tradeTime]
                    del self.priceDict[tradeTime]
            else :
                break
        if self.buyVolume == 0.0 and self.sellVolume == 0.0 :
            rate = 0.0
        else : 
            self.rate = ((self.buyVolume - self.sellVolume)/ (self.buyVolume + self.sellVolume)) * 100;
        self.tradeVolume = self.buyVolume + self.sellVolume
        self.speed = self.tradeTimeQ.qsize()

        
        print ("---------------------------------------------------")
        print ("marketCode : "  + str(self.marketCode))
        print ("code : "  + str(self.code))
        print ("koranName : "  + str(self.koranName))
        print ("englishName : "  + str(self.englishName))
        print ("krwPrice : "  + str(self.krwPrice))
        print ("buyVolume : "  + str(self.buyVolume))
        print ("sellVolume : "  + str(self.sellVolume))
        print ("tradeVolume : "  + str(self.tradeVolume))
        print ("basePrice : "  + str(self.basePrice))
        print ("difference : "  + str(self.difference))
        print ("rate : "  + str(self.rate))
        print ("speed : "  + str(self.speed))
        print ("orderBalance : "  + str(self.orderBalance))
        print ("premium : "  + str(self.premium))
        print ("tradeDateTimeStr : "  + str(self.tradeDateTimeStr))
        print ("tradeDateTime : "  + str(self.tradeDateTime))
        