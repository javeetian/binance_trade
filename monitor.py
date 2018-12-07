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
db.close()
client = Client(api_key, api_secret)
while (1):
    try:
        price = client.get_symbol_ticker(symbol='EOSBNB')
        depth = client.get_order_book(symbol='EOSBNB')
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        print e
    else:
        print time.asctime( time.localtime(time.time()) )
        print price
        print depth
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
