@echo off

if "%1"=="" (
	echo Usage: %0 [time]
	goto :end
)

set time=%1

:loop

call monitor.exe api_key api_secret bot_token bot_chatID monitor.ini

ping -n %time% 127.0.0.1>nul

goto loop

:end