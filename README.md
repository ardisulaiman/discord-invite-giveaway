# Discord Invite Giveaway Bot

Bot Discord yang ngitung undangan per member. 1 undangan = 1 poin. Pas nyampe
INVITE_GOAL (default 20), bot ngasih tau hadiahnya.

## Jalan lokal

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
# isi .env (contoh: .env.example)
.venv\Scripts\python bot.py
```

## Deploy 24/7 ke Railway (cloud gratis, bot tetap jalan walau laptop mati)

1. Push repo ini ke GitHub (sudah).
2. Login https://railway.app (akun yang sama kayak bot Telegram lu).
3. **New Project** -> **Deploy from GitHub repo** -> pilih `ardisulaiman/discord-invite-giveaway`.
4. Tab **Variables** -> tambah:
   - `DISCORD_BOT_TOKEN` = token bot lu
   - `INVITE_GOAL` = `20`
   - `REWARD_TEXT` = teks hadiah
   - `REWARD_CHANNEL_ID` = id channel hadiah
   - `STATE_FILE` = `invite_state.json`
5. **Deploy**. Bot langsung online 24/7.

Catatan: Railway free tier punya filesystem ephemeral — kalau service di-rebuild,
file `invite_state.json` (progres undangan) bisa ter-reset. Kalau mau progres aman
abadi, pasang **Volume** di tab Settings (mount ke `/app`) dan set `STATE_FILE=/app/invite_state.json`.

## Perintah bot

- `/invite` - cek progres undangan lu (contoh: 12/20)
- `/invite_top` - papan peringkat pengundang

## Tools

- `fix_invite_perms.py` - cek/fix izin Create Invite @everyone di semua channel text
- `post_announcement.py` - post pengumuman dari file markdown ke channel
- `start_bot.bat` + `start_bot_hidden.vbs` - auto-start lokal (Startup folder, hidden, auto-restart)

## Test

```
.venv\Scripts\python test_tracker.py
```
