@echo off

:loop

call monitor.exe api_key api_secret bot_token bot_chatID monitor_bnb.ini

ping -n 30 127.0.0.1>nul

call monitor.exe api_key api_secret bot_token bot_chatID monitor_btc.ini

ping -n 300 127.0.0.1>nul

goto loop