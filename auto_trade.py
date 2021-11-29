import time
import pyupbit
import datetime
import requests
import schedule
from fbprophet import Prophet
import config
import logger

class AutoTrade():
    def __init__(self):
        self.slackToken = config.SLACK_TOKEN
        self.slackChannel = "#auto_coin"
        # 로그인
        access = config.UPBIT_ACCESS
        secret = config.UPBIT_SECRET
        self.upbit = pyupbit.Upbit(access, secret)
        logger.info("autotrade start")
        self.post_message("autotrade start")
        self.post_message("현재잔고(KRW): " + str(int(self.get_balance('KRW'))))
        self.is_buy_wait = False
        self.is_partial_loss = False
        self.next_trade_time = self.get_now()

    def post_message(self, text):
        """슬랙 메시지 전송"""
        logger.debug(text)
        response = requests.post("https://slack.com/api/chat.postMessage",
            headers={"Authorization": "Bearer "+self.slackToken},
            data={"channel": self.slackChannel,"text": text}
        )

    def get_target_price(self, ticker, k):
        """변동성 돌파 전략으로 매수 목표가 조회"""
        df = pyupbit.get_ohlcv(ticker, interval="minute240", count=2)
        target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
        return target_price # 목표가

    def get_stoploss_price(self, ticker, k):
        """손절가 조회"""
        df = pyupbit.get_ohlcv(ticker, interval="minute240", count=2)
        stoploss_price = df.iloc[0]['close'] * (1-k)
        return stoploss_price # 목표가

    def get_start_time(self, ticker):
        """시작 시간 조회"""
        df = pyupbit.get_ohlcv(ticker, interval="minute240", count=2)
        start_time = df.index[0]
        return start_time

    def get_ma15(self, ticker, time):
        """15일 이동 평균선 조회"""
        df = pyupbit.get_ohlcv(ticker, interval=time, count=30)
        ma15 = df['close'].rolling(15).mean().iloc[-1]
        return ma15

    def get_ma20(self, ticker, time):
        """20일 이동 평균선 조회"""
        df = pyupbit.get_ohlcv(ticker, interval=time, count=30)
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        return ma20

    def get_mfi(self, ticker, time):
        df = pyupbit.get_ohlcv(ticker, interval="minute5", count=100)
        df['TP'] = (df['high'] + df['low'] + df['close'])
        df['PMF'] = 0
        df['NMF'] = 0
        for i in range(len(df.close)-1):
            if df['TP'].values[i] < df['TP'].values[i+1]:
                df['PMF'].values[i+1] = df['TP'].values[i+1] * df.volume.values[i+1]
                df['NMF'].values[i+1] = 0
            else:
                df['NMF'].values[i+1] = df['TP'].values[i+1] * df.volume.values[i+1]
                df['PMF'].values[i+1] = 0
        df['MFR'] = (df['PMF'].rolling(window=14).sum() /
            df['NMF'].rolling(window=14).sum())
        df['MFI14'] = 100 - 100 / (1 + df['MFR'])
        latest = df.iloc[-1]
        return latest['MFI14']

    def get_balance(self, ticker):
        """잔고 조회"""
        balances = self.upbit.get_balances()

        for b in balances:
            if b['currency'] == ticker:
                if b['balance'] is not None:
                    return float(b['balance'])
                else:
                    return 0
        return 0

    def get_now(self):
        return datetime.datetime.now()# + datetime.timedelta(hours=9)

    def get_krw_tiker(self, ticker):
        return "KRW-" + ticker

    def get_current_price(self, ticker):
        """현재가 조회"""
        return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

    def buy_coin(self, ticker, percent):
        krw = self.get_balance("KRW")
        if self.is_partial_loss == True and self.get_now() < self.next_trade_time + datetime.timedelta(minutes=45):
            return # 부분 매도 후 한시간 동안은 다시 사지 않음
        if krw > 10000 and self.get_now() > self.next_trade_time: # 현재 잔액이 5천원 이상
            self.upbit.buy_market_order("KRW-" + ticker, krw * percent * 0.9995)
            self.post_message("Buy " + ticker + ": " + str(krw))
            self.is_partial_loss = False

    def sell_coin(self, ticker, percent):
        if self.is_partial_loss == True and percent < 1: 
            return # 부분 손절 후 완전 매도가 아니면 부분손절은 더이상 하지 않음
        balance = self.get_balance(ticker)
        current_price = get_current_price(self.get_krw_tiker(ticker))
        if balance * current_price > 10000: 
            self.upbit.sell_market_order("KRW-" + ticker, balance * percent) # 수수료 제외 매도
            self.next_trade_time = self.get_now() + datetime.timedelta(minutes=15)
            self.post_message("Sell " + ticker + ": " +str(balance))
            self.is_partial_loss = True

    def trade(self, coinDict):
        newday = True
        #coinDcit에서 코인 찾기
        coinTicker = "BTC"
        coinKRWTicker = self.get_krw_tiker(coinTicker)
        # 자동매매 시작
        while True:
            try:
                # 시간 설정
                now = self.get_now()
                start_time = self.get_start_time(coinKRWTicker) 
                end_time = start_time + datetime.timedelta(hours=4)

                # 가격 설정
                target_price = self.get_target_price(coinKRWTicker, 0.3) # 목표가
                stoploss_price = self.get_stoploss_price(coinKRWTicker, 0.02) # 손절가
                current_price = self.get_current_price(coinKRWTicker) # 현재가

                # 보조 지표 설정
                ma15_1min = self.get_ma15(coinKRWTicker, 'minute1') # 15일 이평선
                ma15_5min = self.get_ma15(coinKRWTicker, 'minute5') # 15일 이평선
                ma20_5min = self.get_ma20(coinKRWTicker, 'minute5') # 15일 이평선
                mfi14_5min = self.get_mfi(coinKRWTicker, 'minute5') # 14일 MFI
                # 손절
                if current_price < stoploss_price:
                    self.sell_coin(coinTicker, 1.0) # 100% 매도
                # 부분 익절
                elif mfi14_5min > 78:
                    self.sell_coin(coinTicker, 0.5) # 50% 매도
                # 부분 손절 or 익절
                elif current_price < ma20_5min and mfi14_5min < 50:  # 지표를 통해 확인
                    self.sell_coin(coinTicker, 0.5) # 50% 매도

                # 기본 매수 전략
                if start_time < now < end_time - datetime.timedelta(seconds=70): # 58분
                    # 가격 예측
                    # mfi14를 이용
                    if target_price < current_price and current_price > ma15_5min * 1.005 and ma15_5min > ma20_5min and mfi14_5min > 50 and mfi14_5min < 60:
                        self.is_buy_wait = True # 기다렸다가 사야함
                    else:
                        self.is_buy_wait = False

                    if self.is_buy_wait == True and current_price < ma15_1min:
                        self.buy_coin(coinTicker, 1.0)
                        self.is_buy_wait = False
                # 기본 매도 전략, 4시간 지나면 바로 매도
                else:
                    self.sell_coin(coinTicker, 1.0) # 100% 매도
                logger.info("목표가 {} MFI {} 현재가 {} ".format(target_price, mfi14_5min, current_price))
                time.sleep(1)
            except Exception as e:
                self.post_message(e)
                time.sleep(1)
