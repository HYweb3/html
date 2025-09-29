import requests
import pandas as pd
import time,datetime
from binance.client import Client
from scipy import stats
import math

# 设置 Binance API 密钥
api_key = 'your_api_key'
api_secret = 'your_secret_key'

client = Client(api_key, api_secret)

def now():
    mlsec = repr(time.time()).split('.')[1][:3]
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.' + str(mlsec) + ' ')



# 用于存储最后交易时间
last_trade_time = None


def should_trade():
    global last_trade_time
    now = datetime.datetime.now()

    if last_trade_time is None:
        return True  # 如果没有记录最后交易时间，则允许交易

    # 计算距离上次交易的时间差
    time_since_last_trade = now - last_trade_time

    # 检查是否距离上次交易超过24小时
    return time_since_last_trade >= datetime.timedelta(hours=24)


# 获取每日BTC价格数据
def get_btc_data_AHR999():
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=366)
    klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1DAY, start_date.strftime("%d %b, %Y"),
                                          )
    data = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])

    # 转换数据类型
    data['close'] = data['close'].astype(float)
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')  # 将毫秒时间戳转换为日期

    # 提取 price_list 和 date_list
    price_list = data['close'].tolist()
    date_list = data['timestamp'].apply(lambda x: int(x.timestamp() * 1000)).tolist()  # 转换为毫秒时间戳

    return price_list, date_list


# 计算AHR999
def calculate_ahr999(end_time, price_list, date_list, GAP_time=200):
    # 获取当前时间点在时间列表中的索引
    end_index = date_list.index(end_time)

    # 计算开始时间（根据 GAP_time 计算的开始时间）
    start_time = end_time - GAP_time * 24 * 60 * 60 * 1000  # GAP_time天之前
    start_index = date_list.index(start_time)

    # 收集开始到结束时间范围内的价格数据
    scdict = {}
    for i in range(start_index, end_index):
        date = datetime.datetime.utcfromtimestamp(
            date_list[i] / 1000).strftime('%Y-%m-%d')  # 将时间戳转换为日期
        scdict[date] = price_list[i]  # 将日期与价格配对

    # 提取价格列表
    pcls = [scdict[key] for key in scdict.keys()]

    # 几何平均值
    thavg = round(stats.gmean(pcls), 2)

    # 从比特币创世块到当前时间的天数
    price_day = (end_time - 1230940800 * 1000) / (24 * 60 * 60 * 1000)

    # 计算对数价格模型
    logprice = 10 ** (5.84 * math.log(price_day, 10) - 17.01)



    try:
        # AHR999计算公式
        ahr999 = round((price_list[end_index] / thavg) * (price_list[end_index] / logprice), 4)
    except Exception as e:
        print("Error in AHR999 calculation:", e)
        return None

    #now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(datetime.datetime.utcfromtimestamp(
            date_list[end_index] / 1000).strftime('%Y-%m-%d %H:%M:%S'),date_list[end_index],price_list[end_index])

    print(f"======{now()} 当前价格:{price_list[end_index]} 几何平均200天：{thavg} 指数价格：{logprice} AHR999: {ahr999}")


    return ahr999






def get_ahr999():
    # 示例用法
    price_list, date_list = get_btc_data_AHR999()

    # print(date_list[-1],price_list[-1])
    # 获取当前时间的时间戳（以毫秒为单位）
    end_time = int(date_list[-1])

    # 计算AHR999
    ahr999 = calculate_ahr999(end_time, price_list, date_list)

    return int(price_list[-1]),ahr999



#ahr999 = get_ahr999()

# 推送消息的函数
def send_push_notification(message):
    try:
        # 消息接口URL
        url = "https://wxpusher.zjiecode.com/api/send/message/SPT_vYlwfEyMEs4juUBbx2d3bOS0PUfc/" + message

        # 发送GET请求到消息接口
        response = requests.get(url)
        response.raise_for_status()  # 如果请求失败，抛出HTTPError

        print(f"Push notification sent: {message}")
        print(response.json())
        return response.json()
    except requests.RequestException as e:
        print(f"Error sending push notification: {e}")
        return None



import requests
import pandas as pd
import time,datetime
import numpy as np
from binance.client import Client
from okx import Trade

# Binance API 配置
binance_api_key = "YOUR_BINANCE_API_KEY"
binance_secret_key = "YOUR_BINANCE_SECRET_KEY"
client = Client(binance_api_key, binance_secret_key)

# OKX API 配置

# 获取环境变量中的 API Key 和 Secret Key


okx_api_key = "fe560673-1983-4295-9dd5-ca3637018ae6"
okx_secret_key = "CA6B85847263BD6E187C17661B18ACD0"
okx_passphrase = '@Hnb116688'
tradeAPI = Trade.TradeAPI(okx_api_key, okx_secret_key, okx_passphrase, False, '0')

# 恐慌指数 API
FEAR_GREED_API = "https://api.alternative.me/fng/?limit=1"

# 获取每日BTC恐慌指数
def get_fear_greed_index():
    response = requests.get(FEAR_GREED_API)
    if response.status_code == 200:
        data = response.json()
        return int(data['data'][0]['value'])
    else:
        print("Error fetching fear and greed index")
        return None

# 获取 BTC 每小时价格数据
def get_btc_data():
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=10)
    klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_4HOUR, start_date.strftime("%d %b, %Y"))
    data = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    data['close'] = data['close'].astype(float)
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    data['timestamp'] = data['timestamp'] + datetime.timedelta(hours=8)
    return data

# 计算RSI
def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    avg_gain.iloc[period] = gain[:period + 1].mean()  # 初始的平均收益
    avg_loss.iloc[period] = loss[:period + 1].mean()  # 初始的平均损失

    for i in range(period + 1, len(avg_gain)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 检查 RSI 是否反转
def detect_rsi_reversal(rsi_current, rsi_previous, overbought=70, oversold=30):
    if rsi_previous > overbought and rsi_current < rsi_previous:
        return 'SELL'
    elif rsi_previous < oversold and rsi_current > rsi_previous:
        return 'BUY'
    return None

# 记录日志到文件
def log_trade(action, amount, reason):
    msg  = f"Executed {action} for {amount} BTC. Reason: {reason}"
    send_push_notification(msg)
    with open("trade_log.txt", "a") as log_file:
        log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{log_time} - Executed {action} for {amount} BTC. Reason: {reason}\n")
        print(f"{log_time} - Executed {action} for {amount} BTC. Reason: {reason}")

# 执行交易
def execute_trade(action, amount, reason):
    try:
        side = 'buy' if action == 'BUY' else 'sell'
        pos_side = 'long' if action == 'BUY' else 'short'

        log_trade(action, amount, reason)  # 调用日志函数记录交易详情


        #tradeAPI.place_order(instId='BTC-USDT', tdMode='cash', side=side, posSide=pos_side, ordType='market', sz=str(amount))

        # 将side转换为小写
        side = side.lower()

        # market order
        result = tradeAPI.place_order(
            instId="BTC-USDT-SWAP",
            tdMode="isolated",  # isolated 逐仓 #
            side=side,
            posSide=pos_side,
            ordType="market",
            sz=amount * 100  # sz="1"  1=0.01BTC
        )

        print(result)


    except Exception as e:
        print(f"Error executing trade: {str(e)}")
        with open("trade_log.txt", "a") as log_file:
            log_file.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error executing trade: {str(e)}\n")

# 定投或卖出逻辑
def daily_investment(fear_index, ahr999, rsi_signal):
    now = datetime.datetime.now()
    global last_trade_time
                                 

    # 限制每天的交易时间
    if fear_index and now.hour == 10:  # 每天10点恐慌指数交易

        if fear_index < 30:
            execute_trade('BUY', 0.1, 'Fear Index below 30')
        elif fear_index > 65:
            execute_trade('SELL', 0.1, 'Fear Index above 65')

    if ahr999 and (now.hour == 8 or now.hour == 16 or now.hour == 1):  # 每天8点、16点、20点 AHR999交易
        if ahr999 < 0.7:
            execute_trade('BUY', 0.01, 'AHR999 below 0.7')
        if ahr999 < 0.5:
            execute_trade('BUY', 0.1, 'AHR999 below 0.5')

    # 根据RSI信号
    if rsi_signal == 'BUY' and should_trade():
        # 更新最后交易时间
        last_trade_time = datetime.datetime.now()

        execute_trade('BUY', 0.6, f"RSI reversal upward detected")  # RSI反转上升，买入0.2BTC
    elif rsi_signal == 'SELL' and should_trade():

        # 更新最后交易时间
        last_trade_time = datetime.datetime.now()

        execute_trade('SELL', 0.2, f"RSI reversal downward detected")  # RSI反转下降，卖出0.2BTC

# 主循环
def main():
    #while True:
    if 1==1:
        # 获取数据
        fear_greed = get_fear_greed_index()
        df = get_btc_data()
        price,ahr999 = get_ahr999()
        rsi = calculate_rsi(df)

        # 检测RSI反转信号
        rsi_current, rsi_previous2,rsi_previous3 = round(rsi.iloc[-1],2), round(rsi.iloc[-2],2), round(rsi.iloc[-3],2)
        rsi_signal = detect_rsi_reversal(rsi_current, rsi_previous2)

        print("\r\n", '=' * 30, "\r\n", now(),'B价:',price, '恐慌: ',fear_greed,' AHR999: ',ahr999,'  RSI_4H: ',rsi_previous3,'/',rsi_previous2,'/',rsi_current,' RSI信号：',rsi_signal, "\r\n", '=' * 30)

        msg_tuple = ('B价:',str(price), '-恐慌:',str(fear_greed),'-九神:',round(ahr999,2),'-RSI_4H:',str(rsi_previous3),'_',str(rsi_previous2),'_',str(rsi_current),'-RSI信号：',rsi_signal)
        msg = ''.join(map(str, msg_tuple))

        hour = datetime.datetime.now().hour


        #每天发送一次通知：
        hour == 10 and send_push_notification(msg)



        # 执行交易逻辑
        daily_investment(fear_greed, ahr999, rsi_signal)

        # 每4小时检查一次
        #time.sleep(14400)  # 4小时

if __name__ == "__main__":
    main()






#print(f"======AHR999: {ahr999}")
