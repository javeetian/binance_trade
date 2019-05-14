import os
import sys
import time
import requests
import logging
import binance
import ConfigParser
from datetime import datetime
from binance.client import Client

def telegram_bot_sendtext(bot_token, bot_chatID, bot_message):
    response = requests.get('https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message)
    return response.json()
	
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
    telegram_bot_sendtext(bot_token, bot_chatID, str)
    #notify("Warning", str)

if(len(sys.argv) < 5):
	print('Not enough parameters exit!')
	exit(1)
	
logging.basicConfig(filename=datetime.now().strftime('./log/%Y_%m_%d_%H_%M.log'),level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

api_key = sys.argv[1]
api_secret = sys.argv[2]
bot_token = sys.argv[3]
bot_chatID = sys.argv[4]

sleep_time = 300
config_file = 'monitor.ini'

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
                    sell_count += 1
                    Config.set(sym, 'Price', str(float(bids3[2][0])))
                    Config.set(sym, 'Count', str(sell_count))
                    with open(config_file, 'wb') as configfile:
                        Config.write(configfile)
                    response = client.create_order(symbol=sym, side='SELL', type='LIMIT', quantity=order_quantity, price=float(bids3[2][0]), timeInForce='GTC')
                    #logging.warn(response)
                    alert('SELL ' +  sym + ' price: ' + bids3[2][0] + ' quantity: ' + str(order_quantity) + 'sell_count: ' + sell_count + ' now left: ' + str(avail_quantity - order_quantity))
                else:
                    if(order_quantity > avail_quantity):
                        logging.warn('SELL ' +  sym + ' quantity: ' + str(order_quantity) + ' not enough,' + ' now only: ' + str(avail_quantity))

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
                    alert('BUY ' + sym + ' price: ' + asks3[2][0] + ' quantity: ' + str(order_quantity) + 'sell_count: ' + sell_count + ' now left: ' + str(avail_quantity - order_quantity))
                else:
                    if(order_amount > avail_amount):
						logging.warn('BUY ' +  sym + ' amount: ' + str(order_amount) + ' not enough,' + ' now only: ' + str(avail_amount))

            logging.info('symbol: ' + sym + ', sell_count: ' + str(sell_count))
            #if(sell_count > 3 or sell_count < -3):
                #alert('abnormal sell_count!!!!!!')
                
            time.sleep(0.5)
    #time.sleep(sleep_time)
    break

