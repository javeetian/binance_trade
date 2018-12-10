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
profit = 0.05

def get_balances(client):
    try:
        account = client.get_account()
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        print e
    else:
        balances = account['balances']
        for val in balances:
            if val['asset'] == 'EOS':
                ask_quantity = float(val['free']) * 0.2
                if(ask_quantity < 20):
                    ask_quantity = 0
            if val['asset'] == 'BNB':
                bid_quantity = float(val['free']) * 0.2
                if(bid_quantity < 10):
                    bid_quantity = 0
    return ask_quantity, bid_quantity

def get_bids(bids):
            if float(bids[0][0]) > float(bids[1][0]):
                if float(bids[1][0]) > float(bids[2][0]):
                    return [bids[0], bids[1], bids[2]]

def get_asks(asks):
            if float(asks[0][0]) < float(asks[1][0]):
                if float(asks[1][0]) < float(asks[2][0]):
                    return [asks[0], asks[1], asks[2]]

def get_bids_asks(client):
    try:
        depth = client.get_order_book(symbol='EOSBNB')
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        print e
    else:
        print time.asctime( time.localtime(time.time()) )
    return get_bids(depth['bids']), get_asks(depth['asks'])

def cancel_all_orders(client):
    orders = client.get_open_orders(symbol='EOSBNB')
    for order in orders:
        client.cancel_order(symbol='EOSBNB', orderId=order['orderId'])

while (1):
    order_ask_quantity, order_bid_quantity = get_balances(client)
    print order_ask_quantity, order_bid_quantity
    bids3, asks3 = get_bids_asks(client)
    print bids3
    print asks3
    cancel_all_orders(client)
    '''卖'''
    if(last_price * (1 + profit) < bids3[2][0]):
        if((order_ask_quantity > 0) and (order_ask_quantity < bids3[0][1] + bids3[1][1] + bids3[2][1])):
            client.create_test_order(symbol='EOSBNB', side='SELL', type='limited')
    time.sleep(50)

