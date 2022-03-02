import os
import sys
import time
import logging
import requests
import numpy as np
import talib
from binance.client import Client
from config import api_key, api_secret, bot_token, bot_chatID

client = Client(api_key, api_secret)

SYMBOL = "AVAXUSDT"
TIME_PERIOD = "1m"
LIMIT = "500"
QTY = 20

def notify(title, text):
    os.system("""
              osascript -e 'display notification "{}" with title "{}"'
              """.format(text, title))

def telegram_bot_sendtext(bot_token, bot_chatID, bot_message):
    response = requests.get('https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message)
    return response.json()

def alert(str):
    # logging.warn(str)
    response = telegram_bot_sendtext(bot_token, bot_chatID, str)
    # logging.info(response)
    notify("Warning", str)

def place_order(oder_type):
	if(oder_type == "buy"):
		order = client.create_order(symbol=SYMBOL, side="buy", quantity=QTY, type="MARKET")
	else:
		order = client.create_order(symbol=SYMBOL, side="sell", quantity=QTY, type="MARKET")

	print("oder placed successfully!")
	print(order)
	return

def get_data():
	url = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}".format(SYMBOL, TIME_PERIOD,LIMIT)
	res = requests.get(url)
	return_data = []
	for each in res.json():
		return_data.append(float(each[4]))
	return np.array(return_data)

def main():
	buy = False
	sell = True
	ema_12 = None
	ema_144 = None
	ema_169 = None
	last_ema_12 = None
	last_ema_144 = None
	last_ema_169 = None

	while True:
		closing_data = get_data()
		ema_12 = talib.EMA(closing_data,12)[-1]
		ema_144 = talib.EMA(closing_data,144)[-1]
		ema_169 = talib.EMA(closing_data,169)[-1]
		print("ema_12", ema_12, "ema_144", ema_144, "ema_169", ema_169)

		if(ema_12 > ema_144 and last_ema_12):
			if(last_ema_12 < last_ema_144 and not buy):
				place_order("buy")
				print("buy logic goes here")
				alert("\nBuy: " + "ema_12: " + ema_12 + " ema_144: " + ema_144)
				buy = True
				sell = False

		if(ema_169 > ema_12 and last_ema_169):
			if (last_ema_169 < last_ema_12 and not sell):
				place_order("sell")
				print("sell logic goes here")
				alert("\nSell: " + "ema_12, " + ema_12 + ", ema_169, " + ema_169)
				sell = True
				buy = False

		last_ema_12 = ema_12
		last_ema_144 = ema_144
		last_ema_169 = ema_169

		time.sleep(1*60)

if __name__ == '__main__':
	main()