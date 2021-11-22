import websocket
import logger
import sys
import requests
import json
import config
import threading

class Market:
    def __init__(self):
        self.wsAddr = "ws://echo.websocket.org/"
        self.ws = None
        self.wst = None
        self.working = False

    def on_message(self, ws, msg):
        self.getData(msg)
        return

    def on_error(self, ws, msg):
        logger.error(msg)
        return

    def on_close(self, ws):
        self.closeWebSocket()
        return

    def isAlive(self) : 
        if self.ws != None :
            return True
        else :
            return False

    def isWorking(self) : 
        if self.isAlive() :
            return self.working
        else :
            return False

    def connect(self) : 
        websocket.enableTrace(False) # quite mode
        self.ws = websocket.WebSocketApp(self.wsAddr,
                    on_message = lambda ws,msg: self.on_message(ws, msg),
                    on_error   = lambda ws,msg: self.on_error(ws, msg),
                    on_close   = lambda ws:     self.on_close(ws),
                    on_open    = lambda ws:     self.on_open(ws))
        self.wst = threading.Thread(target=self.ws.run_forever)
        self.wst.daemon = True

    def closeWebSocket(self) : 
        if self.isAlive() : 
            self.ws.close()
            self.ws = None

    def getRequest(self, url, headers=None, data=None, params=None):
        resp = requests.get(url, headers=headers, data=data, params=params, verify=False)
        if resp.status_code not in [200, 201]:
            logger.critical('get(%s) failed(%d)' % (url, resp.status_code))
            sys.exit()
        return json.loads(resp.text)

    def start(self) : 
        try :
            logger.info("Try to connect to server : " + self.wsAddr)
            self.connect()
            self.wst.start()
        except : 
            logger.critical("Cannot connect to server : " + self.wsAddr)
            sys.exit()

    def sendMessage(self, msg) : 
        if self.isAlive() : 
            self.working = True
            logger.debug("Send to message : " + msg)
            self.ws.send(msg)
        else :
            logger.error("Cannot find websocket object.")
            self.working = False
            self.start()

    def setExchangeRate(self) :
        try : 
            logger.info("Find out what the exchange rate is")
            data = self.getRequest("https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD")
            config.USD_CURRENCY = data[0]["basePrice"]
        except : 
            logger.info("Cannot find out what the exchange rate is")

    #override method
    def on_open(self, ws):
        return

    def getData(self, data) :
        return

