import os
import sys
import time
import requests
import logging
import binance
import configparser
from datetime import datetime
from binance.client import Client

def telegram_bot_sendtext(bot_token, bot_chatID, bot_message):
    response = requests.get('https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message)
    return response.json()

def notify(title, text):
    os.system("""
              osascript -e 'display notification "{}" with title "{}"'
              """.format(text, title))

# sym=ETH
def get_available_quantity(res, sym):
    # find asset balance in list of balances
    if "balances" in res:
        for bal in res['balances']:
            if bal['asset'].lower() == sym.lower():
                return float(bal['free'])
    return 0

# sym=ETHBTC
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
        #logging.info(account_info)
        #print prices
        for sym in syms:
            sym['balance0'] = get_available_quantity(account_info,sym['symbol'].split("|")[0])
            sym['balance1'] = get_available_quantity(account_info,sym['symbol'].split("|")[1])
            sym['price'] = get_available_price(prices,sym['symbol'].replace('|',''))
            sym['quantity'] = round(float(sym['amount'])/get_available_price(prices,sym['symbol'].replace('|','')),int(sym['round']))

        #print syms

    return ret, syms

# sym=ETHBTC
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

# sym=ETHBTC
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
        #logging.info('Open orders: ' + str(orders))
        for order in orders:
            alert('have open orders, please check, now exit program!!!!')
            time.sleep(5)
            exit(1)
            #client.cancel_order(symbol=sym, orderId=order['orderId'])
    return ret

def alert(str):
    logging.warn(str)
    response = telegram_bot_sendtext(bot_token, bot_chatID, str)
    logging.info(response)
    #notify("Warning", str)

def sec2read(seconds):
    ss = int(seconds)
    d = ss/(3600*24)
    h = (ss - d*24*3600)/3600
    m = (ss - d*24*3600 - h*3600)/60
    s = ss%60
    return str(d)+'D '+str(h)+'H '+str(m)+'M '+str(s)+'S'

#print time.time()
if(len(sys.argv) < 6):
	print('Not enough parameters exit!')
	exit(1)

logging.basicConfig(filename=datetime.now().strftime('./log/%Y_%m_%d_%H_%M.log'),level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

api_key = sys.argv[1]
api_secret = sys.argv[2]
bot_token = sys.argv[3]
bot_chatID = sys.argv[4]
config_file = sys.argv[5]

sleep_time = 300

while (1):
    client = Client(api_key, api_secret)
    logging.info('\n')
    logging.info(time.asctime( time.localtime(time.time()) ))
    logging.info(client.get_server_time())
    if(os.path.isfile(config_file)):
        Config = configparser.ConfigParser()
        Config.read(config_file)
    else:
        exit(1)
    pairs_info = [{'symbol':section,'last_price':Config.get(section,"Price"),'count':Config.get(section,"Count"),'total':Config.get(section,"total"),'round':Config.get(section,"round"),'time_last_order':Config.get(section,"time_last_order"),'time_gap_buy':Config.get(section,"time_gap_buy"),'time_gap_sell':Config.get(section,"time_gap_sell"),'profit_buy':Config.get(section,"profit_buy"),'profit_sell':Config.get(section,"profit_sell"),'profit_base':Config.get(section,"profit_base"),'profit_gap':Config.get(section,"profit_gap"),'amount':Config.get(section,"amount")} for section in Config.sections()]
    #print pairs_info
    ret = 1#check_open_orders(client, pairs_info)
    if ret <  0:
        time.sleep(10)
        continue
    ret, pairs_info = get_balances(client, pairs_info)
    if ret <  0:
        time.sleep(10)
        continue
    for pair in pairs_info:
        ret, pair['bids'], pair['asks'] = get_bids_asks(client, pair['symbol'].replace('|',''))
    if ret <  0:
        time.sleep(10)
        continue
    #logging.info('pairs: ' + str(pairs_info))
    for pl in pairs_info:
        try:
            sell_count = int(pl['count'])
            total = int(pl['total'])
            time_last_order = float(pl['time_last_order'])
            time_gap_buy = float(pl['time_gap_buy'])
            time_gap_sell = float(pl['time_gap_sell'])

            bids3 = pl['bids']
            asks3 = pl['asks']
            bids_price = float(bids3[2][0])
            asks_price = float(asks3[2][0])
            bids_count = float(bids3[0][1]) + float(bids3[1][1]) + float(bids3[2][1])
            asks_count = float(asks3[0][1]) + float(asks3[1][1]) + float(asks3[2][1])
            order_quantity = pl['quantity']
            order_amount = float(pl['amount'])
            avail_quantity = pl['balance0']
            avail_amount = pl['balance1']
            sym = pl['symbol']
            asks_price_max = 1.3*asks_price
            bids_price_min = 0.7*bids_price

            if(time_gap_sell > 86400):
                sell_price = abs(float(pl['last_price']) * (1 + abs(float(pl['profit_base'])) / 100))
            else:
                sell_price = abs(float(pl['last_price']) * (1 + abs(float(pl['profit_sell'])) / 100))

            if(time_gap_buy > 86400):
                buy_price  = abs(float(pl['last_price']) / (1 + abs(float(pl['profit_base'])) / 100))
            else:
                buy_price  = abs(float(pl['last_price']) / (1 + abs(float(pl['profit_buy'])) / 100))

            if(buy_price > asks_price_max):
                alert('\nAbnormal Buy Price: ' + sym + '\nBuy Price: ' + str(buy_price))
                continue
            if(sell_price < bids_price_min):
                alert('\nAbnormal Sell Price: ' + sym + '\nSell Price: ' + str(sell_price))
                continue
        except KeyError as e:
            print(e.message, e.args)
            continue
        else:
            logging.info("\n")
            #print pl['symbol'], sell_price, float(pl['last_price']), buy_price, bids_price, asks_price
            #print order_quantity, avail_quantity, order_amount, avail_amount
            logging.info(""+pl['symbol']+" sell: "+str(sell_price)+" last: "+str(float(pl['last_price']))+" buy: "+str(buy_price)+" act: "+str(bids_price)+", "+str(asks_price))
            logging.info('order: '+str(order_quantity)+' avail: '+str(avail_quantity)+' order: '+str(order_amount)+' avail: '+str(avail_amount))

            #sell
            if(sell_price < bids_price and sell_price > bids_price_min and sell_price > 0):
                if((order_quantity > 0) and (order_quantity < avail_quantity) and (order_quantity < bids_count)):
                    sell_count += 1
                    total += 1
                    time_last_order = float(time.time())
                    response = client.create_order(symbol=sym.replace('|',''), side='SELL', type='LIMIT', quantity=order_quantity, price=bids_price, timeInForce='GTC')
                    #logging.warn(response)
                    # profit = ax^2 + b
                    a = float(pl['profit_gap'])
                    x = abs(sell_count) * abs(sell_count)
                    b = float(pl['profit_base'])
                    profit = a * x + b
                    print(a, x, b, profit)
                    if(sell_count == 0):
                        Config.set(sym, 'profit_sell', str(profit))
                        Config.set(sym, 'profit_buy', str(profit))
                    else:
                        if(sell_count > 0):
                            Config.set(sym, 'profit_sell', str(profit))
                        else:
                            Config.set(sym, 'profit_buy', str(profit))
                    Config.set(sym, 'Price', str(bids_price))
                    Config.set(sym, 'Count', str(sell_count))
                    Config.set(sym, 'total', str(total))
                    Config.set(sym, 'time_last_order', str(time_last_order))
                    with open(config_file, 'w') as configfile:
                        Config.write(configfile)
                    alert('\nSELL: ' +  sym + '\nPrice: ' + str(bids_price) + '\nQuantity: ' + str(order_quantity) + '\nSellCount: ' + str(sell_count) + '\nTotalCount: ' + str(total) + '\nNow left: ' + str(avail_quantity - order_quantity))
                else:
                    if(order_quantity > avail_quantity):
                        logging.warn('SELL ' +  sym + ' quantity: ' + str(order_quantity) + ' not enough,' + ' now only: ' + str(avail_quantity))

            #buy
            if(buy_price > asks_price and buy_price < asks_price_max and buy_price > 0):
                if((order_quantity > 0) and (order_amount < avail_amount) and (order_quantity < asks_count)):
                    sell_count -= 1
                    total += 1
                    time_last_order = float(time.time())
                    response = client.create_order(symbol=sym.replace('|',''), side='BUY', type='LIMIT', quantity=order_quantity, price=asks_price, timeInForce='GTC')
                    #logging.warn(response)
                    # profit = ax^2 + b
                    a = float(pl['profit_gap'])
                    x = abs(sell_count) * abs(sell_count)
                    b = float(pl['profit_base'])
                    profit = a * x + b
                    print(a, x, b, profit)
                    if(sell_count == 0):
                        Config.set(sym, 'profit_sell', str(profit))
                        Config.set(sym, 'profit_buy', str(profit))
                    else:
                        if(sell_count > 0):
                            Config.set(sym, 'profit_sell', str(profit))
                        else:
                            Config.set(sym, 'profit_buy', str(profit))
                    Config.set(sym, 'Price', str(asks_price))
                    Config.set(sym, 'Count', str(sell_count))
                    Config.set(sym, 'total', str(total))
                    Config.set(sym, 'time_last_order', str(time_last_order))
                    with open(config_file, 'w') as configfile:
                        Config.write(configfile)
                    alert('\nBUY: ' + sym + '\nPrice: ' + str(asks_price) + '\nQuantity: ' + str(order_quantity) + '\nSellCount: ' + str(sell_count) + '\nTotalCount: ' + str(total) + '\nNow left: ' + str(avail_quantity + order_quantity))
                else:
                    if(order_amount > avail_amount):
                        logging.warn('BUY ' +  sym + ' amount: ' + str(order_amount) + ' not enough,' + ' now only: ' + str(avail_amount))

            # continue sell
            print("time_gap_sell: "+sec2read(time_gap_sell))
            if(time_gap_sell > 86400 and (float(time.time()) - time_last_order) > time_gap_sell and sell_price > 0):
                if((order_quantity > 0) and (order_quantity < avail_quantity) and (order_quantity < bids_count)):
                    sell_count += 1
                    total += 1
                    time_last_order = float(time.time())
                    response = client.create_order(symbol=sym.replace('|',''), side='SELL', type='LIMIT', quantity=order_quantity, price=bids_price, timeInForce='GTC')
                    #logging.warn(response)
                    Config.set(sym, 'Price', str(bids_price))
                    Config.set(sym, 'Count', str(sell_count))
                    Config.set(sym, 'total', str(total))
                    Config.set(sym, 'time_last_order', str(time.time()))
                    with open(config_file, 'w') as configfile:
                        Config.write(configfile)
                    alert('\nSELL: ' +  sym + '\nPrice: ' + str(bids_price) + '\nQuantity: ' + str(order_quantity) + '\nSellCount: ' + str(sell_count) + '\nTotalCount: ' + str(total) + '\nNow left: ' + str(avail_quantity - order_quantity))
                else:
                    if(order_quantity > avail_quantity):
                        logging.warn('SELL ' +  sym + ' quantity: ' + str(order_quantity) + ' not enough,' + ' now only: ' + str(avail_quantity))

            # continue buy
            print("time_gap_buy: "+sec2read(time_gap_buy))
            if(time_gap_buy > 86400 and (float(time.time()) - time_last_order) > time_gap_buy and buy_price > 0):
                if((order_quantity > 0) and (order_amount < avail_amount) and (order_quantity < asks_count)):
                    sell_count -= 1
                    total += 1
                    time_last_order = float(time.time())
                    response = client.create_order(symbol=sym.replace('|',''), side='BUY', type='LIMIT', quantity=order_quantity, price=asks_price, timeInForce='GTC')
                    #logging.warn(response)
                    Config.set(sym, 'Price', str(asks_price))
                    Config.set(sym, 'Count', str(sell_count))
                    Config.set(sym, 'total', str(total))
                    Config.set(sym, 'time_last_order', str(time.time()))
                    with open(config_file, 'w') as configfile:
                        Config.write(configfile)
                    alert('\nConBUY: ' + sym + '\nPrice: ' + str(asks_price) + '\nQuantity: ' + str(order_quantity) + '\nSellCount: ' + str(sell_count) + '\nTotalCount: ' + str(total) + '\nNow left: ' + str(avail_quantity + order_quantity))
                else:
                    if(order_amount > avail_amount):
                        logging.warn('ConBUY ' +  sym + ' amount: ' + str(order_amount) + ' not enough,' + ' now only: ' + str(avail_amount))


            print("time_gap_last: " + sec2read((float(time.time()) - time_last_order)))
            logging.info('symbol: ' + sym + ', sell_count: ' + str(sell_count))

            #if(sell_count > 3 or sell_count < -3):
                #alert('abnormal sell_count!!!!!!')

            time.sleep(0.5)
    #time.sleep(sleep_time)
    break

