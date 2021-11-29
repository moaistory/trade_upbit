from upbit_trade import UpbitTrade
from binance_trade import BinanceTrade
from upbit_orderbalance import UpbitOrderBalance
from auto_trade import AutoTrade

import config
import logger
import json
import time

def main() :
    name = config.NAME
    logger.info("main start")
    coinDict = {}

    logger.info("upbitTrade start")
    upbitTrade = UpbitTrade(coinDict)
    # 코인 목록을 받아와서 필터링해야함
    # 현재 가격이 일봉기준 15일 선 위에 있고
    # 기울기가 양수인 종목만 찾아서 업비트 데이터 축적
    
    upbitTrade.start()
    while not upbitTrade.isWorking() :
        time.sleep(1)
    
    logger.info("upbitOrderbalance start")
    upbitOrderbalance = UpbitOrderBalance(coinDict)
    upbitOrderbalance.start()
    while not upbitOrderbalance.isWorking() :
        time.sleep(1)
    
    logger.info("binanceTrade start")
    binanceTrade = BinanceTrade(coinDict)
    binanceTrade.start()

    autoTrade = AutoTrade()
    while upbitOrderbalance.isWorking() :
        autoTrade.trade(coinDict)

    logger.info("main end")

if __name__ == "__main__":
    main()
