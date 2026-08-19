' Jalankan bot Discord invite-giveaway secara hidden + auto-restart.
' Dipanggil otomatis dari Windows Startup folder.
Set ws = CreateObject("Wscript.Shell")
ws.Run """C:\Users\User\discord-invite-giveaway\start_bot.bat""", 0, False
