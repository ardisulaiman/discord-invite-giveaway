# -*- coding: utf-8 -*-
"""Post pengumuman ke server Discord dari file teks.

Jalanin: .venv/Scripts/python post_announcement.py [file.md]
Default file: RULES_GIVEAWAY.md. Token dibaca dari .env.
Coba post ke #inviter-giveaway, kalau nggak bisa (misal 403) fallback ke #announcement.
"""

import json
import os
import sys
import urllib.error
import urllib.request

GID = "1514855200601407600"  # ZYRON STUDIO
CHANNELS = ["1539493182797127781", "1514876196729393202"]  # inviter-giveaway, announcement


def load_token():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DISCORD_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    return ""


def post(token, channel_id, content):
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        data=json.dumps({"content": content}).encode(),
        headers={"Authorization": f"Bot {token}", "Content-Type": "application/json", "User-Agent": "InviteGiveawayBot/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        return None, e.code


def main():
    token = load_token()
    if not token:
        raise SystemExit("Token kosong - isi DISCORD_BOT_TOKEN di .env")
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "RULES_GIVEAWAY.md")
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()
    for cid in CHANNELS:
        resp, err = post(token, cid, content)
        if resp:
            print(f"TERKIRIM ke channel {cid} - id pesan {resp.get('id')}")
            return
        print(f"channel {cid}: gagal (HTTP {err})")
    raise SystemExit("Semua channel gagal - cek permission bot.")


if __name__ == "__main__":
    main()
