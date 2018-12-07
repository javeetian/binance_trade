from binance.client import Client
import time
import requests
from myzodb import MyZODB, transaction
db = MyZODB('./Data.fs')
dbroot = db.dbroot
last_price = dbroot['last_price']
api_key = dbroot['api_key']
api_secret = dbroot['api_secret']
print last_price
transaction.commit()
db.close()
client = Client(api_key, api_secret)
bid_price = 0.0
bid_quantity = 0.0
bid_index = 0
ask_price = 1000000.0
ask_quantity = 0.0
ask_index = 0
str_eos = 'EOS'
while (1):
    try:
        account = client.get_account()
        depth = client.get_order_book(symbol='EOSBNB')
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        print e
    else:
        print time.asctime( time.localtime(time.time()) )
        balances = account['balances']
        for i, val in enumerate(balances):
            if val['asset'] == 'EOS'
                print val['free']
            if val['asset'] == 'BNB'
                print val['free']
        bids = depth['bids']
        print 'bids:'
        for i, val in enumerate(bids):
            if float(val[0]) > bid_price:
                bid_price = float(val[0])
                bid_quantity = float(val[1])
                bid_index = i
        print bid_index, bid_price, bid_quantity
        asks = depth['asks']
        print 'asks:'
        for i, val in enumerate(asks):
            if float(val[0]) < ask_price:
                ask_price = float(val[0])
                ask_quantity = float(val[1])
                ask_index = i
        print ask_index, ask_price, ask_quantity
    time.sleep(50)



# get info
#info = client.get_symbol_info('EOSBNB')
#print info
# get market depth
#depth = client.get_order_book(symbol='EOSBNB')
#print depth
# get all symbol prices
#prices = client.get_all_tickers()
#print prices
# get historical kline data from any date range

# fetch 1 minute klines for the last day up until now
#klines = client.get_historical_klines("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")
#print klines
# fetch 30 minute klines for the last month of 2017
#klines = client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_30MINUTE, "1 Dec, 2017", "1 Jan, 2018")
#print klines
# fetch weekly klines since it listed
#klines = client.get_historical_klines("NEOBTC", Client.KLINE_INTERVAL_1WEEK, "1 Jan, 2017")
#print klines
