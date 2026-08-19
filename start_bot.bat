@echo off
cd /d "C:\Users\User\discord-invite-giveaway"
:loop
".venv\Scripts\python.exe" bot.py
timeout /t 5 /nobreak >nul
goto loop
