@echo off
cd /d "C:\Users\User\discord-invite-giveaway"
set PYTHONPATH=
set VIRTUAL_ENV=
:loop
".venv\Scripts\python.exe" bot.py >> bot_console.log 2>&1
timeout /t 5 /nobreak >nul
goto loop
