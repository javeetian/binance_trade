@echo off

:loop

call monitor.exe

ping -n 300 127.0.0.1>nul

goto loop