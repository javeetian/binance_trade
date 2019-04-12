import os
import time
from datetime import datetime
import requests
import logging
import binance
from binance.client import Client
from myzodb import MyZODB, transaction
import paho.mqtt.client as mqtt
 
def on_connect(client, userdata, flags, rc):
  logging.info("Connected with result code "+str(rc))

def on_message(client, userdata, msg):
  logging.info(msg.topic+" "+str(msg.payload))


def notify(title, text):
    os.system("""
              osascript -e 'display notification "{}" with title "{}"'
              """.format(text, title))

def fetch_configs():
    db = MyZODB('./Data.fs')
    dbroot = db.dbroot
    price = 0
    count = 0
    key = ''
    secret = ''
    try:
        price = dbroot['last_price']
    except KeyError as e:
        logging.debug(e)
        dbroot['last_price'] = 0  # set to last trade price

    try:
        count = dbroot['sell_count']
    except KeyError as e:
        logging.debug(e)
        dbroot['sell_count'] = 0

    try:
        key = dbroot['api_key']
    except KeyError as e:
        logging.debug(e)
        dbroot['api_key'] = "Your api key"

    try:
        secret = dbroot['api_secret']
    except KeyError as e:
        logging.debug(e)
        dbroot['api_secret'] = "Your api secret"
        
    transaction.commit()
    db.close()
    return price, count, key, secret

def store_price(price):
    db = MyZODB('./Data.fs')
    dbroot = db.dbroot
    dbroot['last_price'] = price
    transaction.commit()
    db.close()

def store_sell_count(count):
    db = MyZODB('./Data.fs')
    dbroot = db.dbroot
    dbroot['sell_count'] = count
    transaction.commit()
    db.close()

def get_price(client, sym):
    result = client.get_symbol_ticker(symbol=sym)
    return result['price']

def get_availalbe_quantity(res, sym):
    # find asset balance in list of balances
    if "balances" in res:
        for bal in res['balances']:
            if bal['asset'].lower() == sym.lower():
                return float(bal['free'])
    return 0

def get_availalbe_quantity(res, sym):
    # find asset balance in list of balances
    if "balances" in res:
        for bal in res['balances']:
            if bal['asset'].lower() == sym.lower():
                return float(bal['free'])
    return 0

def get_balances(client, sym):
    ret = 0
    ask_quantity = 0
    bid_quantity = 20
    try:
        res = client.get_account()
        prices = client.get_symbol_ticker()
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        logging.error(e)
        ret = -1
    except requests.exceptions.ReadTimeout as e:
        logging.error(e)
        ret = -2
    else:
        print res
        print prices
        if(ask_quantity > 1000):
            ask_quantity = 0
            notify("Notify", 'Not enough EOS')
        if(bid_quantity > get_availalbe_quantity(res,'BNB')):
            bid_quantity = 0
            notify("Notify", 'Not enough BNB')
        logging.debug('Balances EOS: ' + str(eos['free']) + ' BNB: ' + str(bnb['free']))
    return ret, round(ask_quantity, 2), round(bid_quantity, 2)

def get_bids_asks(client, sym):
    ret = 0
    bids3 = 0
    asks3 = 0
    try:
        depth = client.get_order_book(symbol=sym)
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        logging.error(e)
        ret = -1
    except requests.exceptions.ReadTimeout as e:
        logging.error(e)
        ret = -2
    else:
        bids = depth['bids']
        asks = depth['asks']
        if float(bids[0][0]) > float(bids[1][0]):
            if float(bids[1][0]) > float(bids[2][0]):
                bids3 = [bids[0], bids[1], bids[2]]
        if float(asks[0][0]) < float(asks[1][0]):
            if float(asks[1][0]) < float(asks[2][0]):
                asks3 = [asks[0], asks[1], asks[2]]
    return ret, bids3, asks3

def check_open_orders(client, sym):
    ret = 0
    try:
        orders = client.get_open_orders()
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        logging.error(e)
        ret = -1
    except requests.exceptions.ReadTimeout as e:
        logging.error(e)
        ret = -2
    except binance.exceptions.BinanceAPIException as e:
        logging.error(e)
        ret = -2
    else:
        logging.info('Open orders: ' + str(orders))
        for order in orders:
            notify_str = 'have open orders, please check, now exit program!!!!'
            notify("Notify", notify_str)
            #mqttc.publish(PUB_TOPIC,payload=notify_str,qos=0)
            exit(1)
            #client.cancel_order(symbol=sym, orderId=order['orderId'])
    return ret


logging.basicConfig(filename=datetime.now().strftime('./log/%Y_%m_%d_%H_%M.log'),level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())


last_price, sell_count, api_key, api_secret = fetch_configs()
client = Client(api_key, api_secret)
profit = 0.06
sleep_time = 50
PUB_TOPIC = 'tjwtjwtjw'
trade_pairs = ['EOSBNB','LTCBNB','ADABNB','XRPBNB','TRXBNB','FETBNB','BTTBNB','RVNBNB', 'CELRBNB', 'NEOBNB', 'NANOBNB', 'IOSTBNB', 'THETABNB', 'ONTBNB', 'ENJBNB', 'XLMBNB']
#mqttc = mqtt.Client()
#mqttc.on_connect = on_connect
#mqttc.on_message = on_message
#mqttc.connect("test.mosquitto.org")
#mqttc.loop_start()


while (1):
    logging.info('\n')
    logging.info(time.asctime( time.localtime(time.time()) ))
    logging.debug('last_price: ' + str(last_price))
    sell_price = last_price * (1 + profit)
    buy_price = last_price * (1 - profit)
    logging.info('buy price: ' + str(buy_price) + 'sell price:' + str(sell_price))
    ret = check_open_orders(client, trade_pairs)
    if ret <  0:
        time.sleep(10)
        continue
    ret, order_ask_quantity, order_bid_quantity = get_balances(client, trade_pairs)
    if ret <  0:
        time.sleep(10)
        continue
    logging.info('buy quantity: ' + str(order_bid_quantity) + 'sell quantity: ' + str(order_ask_quantity))
    ret, bids3, asks3 = get_bids_asks(client, trade_pairs)
    if ret <  0:
        time.sleep(10)
        continue
    logging.info('bids: ' + str(bids3))
    logging.info('asks: ' + str(asks3))
    time.sleep(sleep_time)
    continue
    #sell
    if(sell_price < float(bids3[2][0])):
        if((order_ask_quantity > 0) and (order_ask_quantity < (float(bids3[0][1]) + float(bids3[1][1]) + float(bids3[2][1])))):
            notify_str = 'SELL EOS price: ' + bids3[2][0] + ' quantity: ' + str(order_ask_quantity)
            logging.warn(notify_str)
            last_price = float(bids3[2][0])
            store_price(last_price)
            sell_count += 1
            store_sell_count(sell_count)
            response = client.create_order(symbol=trade_pairs, side='SELL', type='LIMIT', quantity=order_ask_quantity, price=float(bids3[2][0]), timeInForce='GTC')
            logging.warn(response)
            notify("Notify", notify_str)
            #mqttc.publish(PUB_TOPIC,payload=notify_str,qos=0)
        else:
            if(order_ask_quantity > 0):
                sleep_time = 5
    #buy
    if(buy_price > float(asks3[2][0])):
        if((order_bid_quantity > 0) and (order_bid_quantity < (float(asks3[0][1]) + float(asks3[1][1]) + float(asks3[2][1])))):
            notify_str = 'BUY EOS price: ' + asks3[2][0] + ' quantity: ' + str(order_bid_quantity)
            logging.warn(notify_str)
            last_price = float(asks3[2][0])
            store_price(last_price)
            sell_count -= 1
            store_sell_count(sell_count)
            response = client.create_order(symbol=trade_pairs, side='BUY', type='LIMIT', quantity=order_bid_quantity, price=float(asks3[2][0]), timeInForce='GTC')
            logging.warn(response)
            notify("Notify", notify_str)
            #mqttc.publish(PUB_TOPIC,payload=notify_str,qos=0)
        else:
            if(order_ask_quantity > 0):
                sleep_time = 5
    logging.info('sell_count: ' + str(sell_count))
    if(sell_count > 3 or sell_count < -3):
        logging.warn('abnormal sell_count!!!!!!')
        notify("Warning", "abnormal sell_count!!!!!!")
        #mqttc.publish(PUB_TOPIC,payload='abnormal sell_count!!!!!!',qos=0)
    time.sleep(sleep_time)

