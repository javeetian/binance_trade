@echo off

:loop

call monitor.exe api_key api_secret bot_token bot_chatID monitor.ini

ping -n 120 127.0.0.1>nul

goto loop