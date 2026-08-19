@echo off
schtasks /create /tn InviteGiveawayBot /tr "wscript.exe C:\Users\User\discord-invite-giveaway\start_bot_hidden.vbs" /sc onlogon /f
