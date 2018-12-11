import os
import time
import requests
from binance.client import Client
from myzodb import MyZODB, transaction
import paho.mqtt.client as mqtt
 
def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))

def on_message(client, userdata, msg):
  print(msg.topic+" "+str(msg.payload))


def notify(title, text):
    os.system("""
              osascript -e 'display notification "{}" with title "{}"'
              """.format(text, title))

def fetch_configs():
    db = MyZODB('./Data.fs')
    dbroot = db.dbroot
    price = dbroot['last_price']
    key = dbroot['api_key']
    secret = dbroot['api_secret']
    db.close()
    return price, key, secret

def store_price(price):
    db = MyZODB('./Data.fs')
    dbroot = db.dbroot
    dbroot['last_price'] = price
    transaction.commit()
    db.close()

def get_balances(client):
    try:
        eos = client.get_asset_balance('EOS')
        bnb = client.get_asset_balance('BNB')
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        print e
    else:
        ask_quantity = float(eos['free']) * 0.2
        if(ask_quantity < 20):
            ask_quantity = 0
        bid_quantity = float(bnb['free']) * 0.2
        if(bid_quantity < 10):
            bid_quantity = 0
    return round(ask_quantity, 2), round(bid_quantity, 2)

def get_bids_asks(client):
    try:
        depth = client.get_order_book(symbol='EOSBNB')
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        print e
    else:
        bids = depth['bids']
        asks = depth['asks']
        if float(bids[0][0]) > float(bids[1][0]):
            if float(bids[1][0]) > float(bids[2][0]):
                bids3 = [bids[0], bids[1], bids[2]]
        if float(asks[0][0]) < float(asks[1][0]):
            if float(asks[1][0]) < float(asks[2][0]):
                asks3 = [asks[0], asks[1], asks[2]]
    return bids3, asks3

def cancel_all_orders(client):
    try:
        orders = client.get_open_orders(symbol='EOSBNB')
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        print e
    else:
        for order in orders:
            client.cancel_order(symbol='EOSBNB', orderId=order['orderId'])

last_price, api_key, api_secret = fetch_configs()
client = Client(api_key, api_secret)
profit = 0.06
sell_count = 0
mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect("test.mosquitto.org")
mqttc.loop_start()
while (1):
    print time.asctime( time.localtime(time.time()) )
    print 'last_price: ' + str(last_price)
    sell_price = last_price * (1 + profit)
    buy_price = last_price * (1 - profit)
    print 'buy price: ', buy_price, 'sell price:', sell_price
    order_ask_quantity, order_bid_quantity = get_balances(client)
    print 'buy quantity: ', order_bid_quantity, 'sell quantity: ', order_ask_quantity
    bids3, asks3 = get_bids_asks(client)
    print 'bids: ', bids3
    print 'asks: ', asks3
    cancel_all_orders(client)
    #sell
    if(sell_price < float(bids3[2][0])):
        if((order_ask_quantity > 0) and (order_ask_quantity < (float(bids3[0][1]) + float(bids3[1][1]) + float(bids3[2][1])))):
            notify_str = 'SELL EOS price: ' + bids3[2][0] + ' quantity: ' + str(order_ask_quantity)
            print notify_str
            last_price = float(bids3[2][0])
            store_price(last_price)
            sell_count += 1
            response = client.create_test_order(symbol='EOSBNB', side='SELL', type='LIMIT', quantity=order_ask_quantity, price=float(bids3[2][0]), timeInForce='GTC')
            print response
            notify("Notify", notify_str)
            mqttc.publish('tjwtjwtjw',payload=notify_str,qos=0)
    #buy
    if(buy_price > float(asks3[2][0])):
        if((order_bid_quantity > 0) and (order_bid_quantity < (float(asks3[0][1]) + float(asks3[1][1]) + float(asks3[2][1])))):
            notify_str = 'BUY EOS price: ' + asks3[2][0] + ' quantity: ' + str(order_bid_quantity)
            last_price = float(asks3[2][0])
            store_price(last_price)
            sell_count -= 1
            response = client.create_test_order(symbol='EOSBNB', side='BUY', type='LIMIT', quantity=order_bid_quantity, price=float(asks3[2][0]), timeInForce='GTC')
            print response
            notify("Notify", notify_str)
            mqttc.publish('tjwtjwtjw',payload=notify_str,qos=0)
    print 'sell_count: ', sell_count
    if(sell_count > 3 or sell_count < -3):
        print 'abnormal sell_count!!!!!!'
        notify("Warning", "abnormal sell_count!!!!!!")
        mqttc.publish('tjwtjwtjw',payload='abnormal sell_count!!!!!!',qos=0)
    time.sleep(50)

