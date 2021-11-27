import time
import pyupbit
import datetime
import requests
import schedule
from fbprophet import Prophet
import config

class AutoTrade():
    def __init__(self):
        self.predicted_close_price = 0
        self.slackToken = config.SLACK_TOKEN
        self.slackChannel = "#auto_coin"
        # 로그인
        access = config.UPBIT_ACCESS
        secret = config.UPBIT_SECRET
        self.upbit = pyupbit.Upbit(access, secret)
        print("autotrade start")
        self.post_message(slackToken, slackChannel, "autotrade start")
        self.post_message(slackToken, slackChannel, "현재잔고(KRW): " + str(int(self.get_balance('KRW'))))

    def post_message(self, token, channel, text):
        """슬랙 메시지 전송"""
        response = requests.post("https://slack.com/api/chat.postMessage",
            headers={"Authorization": "Bearer "+token},
            data={"channel": channel,"text": text}
        )

    def get_target_price(self, ticker, k):
        """변동성 돌파 전략으로 매수 목표가 조회"""
        df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
        target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
        return target_price # 목표가

    def get_start_time(self, ticker):
        """시작 시간 조회"""
        df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
        start_time = df.index[0]
        return start_time

    def get_ma15(self, ticker):
        """15일 이동 평균선 조회"""
        df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
        ma15 = df['close'].rolling(15).mean().iloc[-1]
        return ma15

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

    def get_current_price(self, ticker):
        """현재가 조회"""
        return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

    def predict_price(self, ticker):
        #Prophet으로 당일 종가 가격 예측
        df = pyupbit.get_ohlcv(ticker, interval="minute60")
        df = df.reset_index()
        df['ds'] = df['index']
        df['y'] = df['close']
        data = df[['ds','y']]
        model = Prophet()
        model.fit(data)
        future = model.make_future_dataframe(periods=24, freq='H')
        forecast = model.predict(future)
        closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
        if len(closeDf) == 0:
            closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
        closeValue = closeDf['yhat'].values[0]
        self.predicted_close_price = closeValue

    def trade(self, coinDict):
        newday = True

        self.predict_price("KRW-BTC")
        schedule.every().hour.do(lambda: predict_price("KRW-BTC"))

        # 자동매매 시작
        while True:
            try:
                now = datetime.datetime.now()
                start_time = self.get_start_time("KRW-BTC") # 9:00
                end_time = start_time + datetime.timedelta(days=1) # 9:00 + 1일
                # 9시 < 현재 < 8시 59분 50초

                schedule.run_pending() # 가격 예측

                if start_time < now < end_time - datetime.timedelta(seconds=10): 
                    target_price = self.get_target_price("KRW-BTC", 0.5) # 목표가
                    current_price = self.get_current_price("KRW-BTC") # 현재가
                    
                    # 이동평균선 조건 체크
                    #ma15 = get_ma15("KRW-BTC") 
                    #if target_price < current_price and ma15 < current_price: #and ma15 < current_price:

                    # 돌파성 매매이면서 AI로 종가보다 높을 것 같은 경우에만 매수진행
                    if newday:
                        newday = False
                        price_message = '목표가: ' + str(round(target_price,2)) + '  AI 예상: ' + str(round(self.predicted_close_price,2))
                        self.post_message(slackToken, slackChannel, price_message)

                    if target_price < current_price and current_price < self.predicted_close_price:
                        krw = self.get_balance("KRW")
                        if krw > 5000: # 현재 잔액이 5천원 이상
                            self.upbit.buy_market_order("KRW-BTC", krw*0.9995)
                            post_message(slackToken, slackChannel, "Buy BTC with KRW " +str(krw))
                else: # 8시 59분 50초 < 현재 < 9시
                    newday = True
                    btc = self.get_balance("BTC")
                    if btc > 0.00008: 
                        self.upbit.sell_market_order("KRW-BTC", btc*0.9995) # 수수료를 제외한 전량매도
                        self.post_message(slackToken, slackChannel, "Sell KRW for BTC " +str(btc))
                time.sleep(1)
            except Exception as e:
                print(e)
                self.post_message(slackToken, slackChannel, e)
                time.sleep(1)