# -*- coding: utf-8 -*-
"""Restriksi @everyone: cuma role ADMIN & OWNER yang bisa mention @everyone.

- @everyone role: MENTION_EVERYONE di-CABUT
- ADMIN / OWNER: MENTION_EVERYONE di-KASIH
- Role bot non-admin (Koya, Sound Downloader): di-cabut juga
- Bot admin (Arcane, Ticket Tool) punya ADMINISTRATOR -> otomatis termasuk

Jalanin: .venv/Scripts/python fix_mention_everyone.py
"""

import json
import os
import urllib.error
import urllib.request

GID = "1514855200601407600"
MENTION_EVERYONE = 131072
REMOVE = ["1514855200601407600",  # @everyone
          "1540207534151831683",  # Koya
          "1523594810160840804",  # Sound Downloader
          ]
ADD = ["1514882669282857050",     # ADMIN
       "1538421664612622416",     # OWNER
       ]


def load_token():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DISCORD_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    return ""


def api(method, url, body=None, token=""):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bot {token}", "Content-Type": "application/json",
                 "User-Agent": "InviteGiveawayBot/1.0"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read()[:150].decode(errors='replace')}"


def main():
    tok = load_token()
    if not tok:
        raise SystemExit("Token kosong - isi DISCORD_BOT_TOKEN di .env")
    roles, err = api("GET", f"https://discord.com/api/v10/guilds/{GID}/roles", token=tok)
    if err:
        raise SystemExit(f"Gagal baca roles: {err}")
    by_id = {r["id"]: r for r in roles}

    for rid in REMOVE:
        r = by_id.get(rid)
        if not r:
            print(f"role {rid}: nggak ketemu, skip")
            continue
        newp = int(r["permissions"]) & ~MENTION_EVERYONE
        _, e = api("PATCH", f"https://discord.com/api/v10/guilds/{GID}/roles/{rid}",
                   {"permissions": str(newp)}, token=tok)
        print(f"{r['name']:<16} MENTION_EVERYONE DI-CABUT -> {'OK' if not e else 'GAGAL ' + e}")
    for rid in ADD:
        r = by_id.get(rid)
        if not r:
            print(f"role {rid}: nggak ketemu, skip")
            continue
        newp = int(r["permissions"]) | MENTION_EVERYONE
        _, e = api("PATCH", f"https://discord.com/api/v10/guilds/{GID}/roles/{rid}",
                   {"permissions": str(newp)}, token=tok)
        print(f"{r['name']:<16} MENTION_EVERYONE DI-KASIH -> {'OK' if not e else 'GAGAL ' + e}")


if __name__ == "__main__":
    main()
