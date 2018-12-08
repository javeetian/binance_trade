import time
from binance.client import Client
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
order_bid_quantity = 0.0
order_bid_price = 0.0
order_ask_quantity = 0.0
order_ask_price = 0.0

def get_balances(client):
    try:
        account = client.get_account()
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        print e
    else:
        balances = account['balances']
        for val in enumerate(balances):
            if val['asset'] == 'EOS':
                order_ask_quantity = float(val['free']) * 0.2
                print val['free'], order_ask_quantity
                if(order_ask_quantity < 10):
                    order_ask_quantity = 0
            if val['asset'] == 'BNB':
                order_bid_quantity = float(val['free']) * 0.2
                print val['free'], order_bid_quantity
                if(order_bid_quantity < 5):
                    order_bid_quantity = 0

def get_bids(bids):
        price = 0.0
        for i, val in enumerate(bids):
            if float(val[0]) > price:
                price = float(val[0])
                quantity = float(val[1])
                bid_index = i
        print bid_index, price, quantity
        return price, quantity

def get_asks(asks):
        price = 1000000.0
        for i, val in enumerate(asks):
            if float(val[0]) < price:
                price = float(val[0])
                quantity = float(val[1])
                ask_index = i
        print ask_index, price, quantity
        return price, quantity

def get_bids_asks(client):
    try:
        depth = client.get_order_book(symbol='EOSBNB')
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        print e
    else:
        print time.asctime( time.localtime(time.time()) )
        bids = depth['bids']
        bids_price, bids_quantity = get_bids(bids)
        asks = depth['asks']
        asks_price, asks_quantity = get_asks(asks)
    return bids_price, bids_quantity, asks_price, asks_quantity

while (1):
    get_balances(client)
    bids_price, bids_quantity, ask_price, asks_quantity = get_bids_asks(client)
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
