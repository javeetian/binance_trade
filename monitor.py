import os
import time
from datetime import datetime
import requests
import logging
import binance
import ConfigParser
from binance.client import Client
import paho.mqtt.client as mqtt
 
def on_connect(client, userdata, flags, rc):
  logging.info("Connected with result code "+str(rc))

def on_message(client, userdata, msg):
  logging.info(msg.topic+" "+str(msg.payload))


def notify(title, text):
    os.system("""
              osascript -e 'display notification "{}" with title "{}"'
              """.format(text, title))

def get_price(client, sym):
    result = client.get_symbol_ticker(symbol=sym)
    return result['price']

def get_available_quantity(res, sym):
    # find asset balance in list of balances
    if "balances" in res:
        for bal in res['balances']:
            if bal['asset'].lower() == sym[:-3].lower():
                return float(bal['free'])
    return 0

def get_available_price(prices, sym):
    ret = -1
    for res in prices:
        if res['symbol'].lower() == sym.lower():
            ret = float(res['price'])
    return ret


def get_balances(client, syms):
    ret = 0
    try:
        account_info = client.get_account()
        prices = client.get_symbol_ticker()
    except requests.exceptions.ConnectionError as e:  # This is the correct syntax
        logging.error(e)
        ret = -1
    except requests.exceptions.ReadTimeout as e:
        logging.error(e)
        ret = -2
    else:
        #print account_info
        #print prices
        for sym in syms:
            sym['balance'] = get_available_quantity(account_info,sym['symbol'])
            sym['price'] = get_available_price(prices,sym['symbol'])
            sym['quantity'] = round(float(sym['amount'])/get_available_price(prices,sym['symbol']),1)

        print syms
        
    return ret, syms

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
            alert('have open orders, please check, now exit program!!!!')
            time.sleep(5)
            exit(1)
            #client.cancel_order(symbol=sym, orderId=order['orderId'])
    return ret

def alert(str):
    logging.warn(str)
    #notify("Warning", str)
    #mqttc.publish(PUB_TOPIC,payload=str,qos=0)

logging.basicConfig(filename=datetime.now().strftime('./log/%Y_%m_%d_%H_%M.log'),level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

api_key = ''
api_secret = '' 

sleep_time = 300
PUB_TOPIC = 'tjwtjwtjw'
config_file = 'monitor.ini'

#mqttc = mqtt.Client()
#mqttc.on_connect = on_connect
#mqttc.on_message = on_message
#mqttc.connect("test.mosquitto.org")
#mqttc.loop_start()


while (1):
    client = Client(api_key, api_secret)
    logging.info('\n')
    logging.info(time.asctime( time.localtime(time.time()) ))
    if(os.path.isfile(config_file)):
        Config = ConfigParser.ConfigParser()
        Config.read(config_file)
    else:
        exit(1)
    pairs_info = [{'symbol':section,'last_price':Config.get(section,"Price"),'count':Config.get(section,"Count"),'profit':Config.get(section,"Profit"),'amount':Config.get(section,"Amount")} for section in Config.sections()]
    print pairs_info
    ret = check_open_orders(client, pairs_info)
    if ret <  0:
        time.sleep(10)
        continue
    ret, pairs_info = get_balances(client, pairs_info)
    if ret <  0:
        time.sleep(10)
        continue
    for pair in pairs_info:
        if pair != pairs_info[0]:
            ret, pair['bids'], pair['asks'] = get_bids_asks(client, pair['symbol'])
    if ret <  0:
        time.sleep(10)
        continue
    logging.info('pairs: ' + str(pairs_info))
    avail_amount = pairs_info[0]['balance']
    for pl in pairs_info:
        try:
            sell_price = float(pl['last_price']) * (1 + float(pl['profit'])/100)
            buy_price = float(pl['last_price']) / (1 + float(pl['profit'])/100)
            bids3 = pl['bids']
            asks3 = pl['asks']
            order_quantity = pl['quantity']
            order_amount = float(pl['amount'])
            avail_quantity = pl['balance']
            sell_count = int(pl['count'])
            sym = pl['symbol']
        except KeyError as e:
            print e.message, e.args
            continue
        else:
            print pl['symbol'],sell_price, buy_price, float(bids3[2][0]), float(asks3[2][0])
            print order_quantity, avail_quantity, order_amount, avail_amount
            #sell
            if(sell_price < float(bids3[2][0]) and sell_price > 0):
                if((order_quantity > 0) and (order_quantity < avail_quantity) and (order_quantity < (float(bids3[0][1]) + float(bids3[1][1]) + float(bids3[2][1])))):
                    notify_str = 'SELL ' +  sym + ' price: ' + bids3[2][0] + ' quantity: ' + str(order_quantity)

                    sell_count += 1
                    Config.set(sym, 'Price', str(float(bids3[2][0])))
                    Config.set(sym, 'Count', str(sell_count))
                    with open(config_file, 'wb') as configfile:
                        Config.write(configfile)
                    response = client.create_order(symbol=sym, side='SELL', type='LIMIT', quantity=order_quantity, price=float(bids3[2][0]), timeInForce='GTC')
                    #logging.warn(response)
                    alert(notify_str)
                else:
                    print order_quantity, avail_quantity
                    if(order_quantity > avail_quantity):
                        alert('SELL ' +  sym + ' not enough quantity')

            #buy
            if(buy_price > float(asks3[2][0]) and buy_price > 0):
                if((order_quantity > 0) and (order_amount < avail_amount) and (order_quantity < (float(asks3[0][1]) + float(asks3[1][1]) + float(asks3[2][1])))):
                    sell_count -= 1
                    Config.set(sym, 'Price', str(float(asks3[2][0])))
                    Config.set(sym, 'Count', str(sell_count))
                    with open(config_file, 'wb') as configfile:
                        Config.write(configfile)
                    response = client.create_order(symbol=sym, side='BUY', type='LIMIT', quantity=order_quantity, price=float(asks3[2][0]), timeInForce='GTC')
                    #logging.warn(response)
                    alert('BUY ' + sym + ' price: ' + asks3[2][0] + ' quantity: ' + str(order_quantity))
                else:
                    print order_amount, avail_amount
                    if(order_amount > avail_amount):
                        alert('BUY ' +  sym + ' not enough amount')

            logging.info('symbol: ' + sym + ', sell_count: ' + str(sell_count))
            if(sell_count > 3 or sell_count < -3):
                alert('abnormal sell_count!!!!!!')
                
            time.sleep(0.5)
    #time.sleep(sleep_time)
    break

