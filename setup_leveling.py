# -*- coding: utf-8 -*-
"""Setup server leveling: role Level 5, channel #asset-level (hidden), #level
(slash-only), sistem channel welcome-brodi.

Bot butuh: Manage Roles (role Level 5) + Manage Guild (system channel).
Channel bikin butuh Manage Channels - kalau bot belum punya, script ini
nunjukin persis yang harus lu buat manual.

Jalanin: .venv/Scripts/python setup_leveling.py
"""

import json
import os
import urllib.error
import urllib.request

GID = "1514855200601407600"  # ZYRON STUDIO
WELCOME_CHANNEL_ID = "1514855201092145194"  # welcome-brodi
LEVEL5_ROLE = "Level 5"
ASSET_CHANNEL = "asset-level"
LEVEL_CHANNEL = "level"
VIEW = 1024
SEND = 2048


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
        return None, f"HTTP {e.code}: {e.read()[:200].decode(errors='replace')}"


def main():
    tok = load_token()
    if not tok:
        raise SystemExit("Token kosong - isi DISCORD_BOT_TOKEN di .env")

    guilds, err = api("GET", "https://discord.com/api/v10/users/@me/guilds", token=tok)
    botp = int(guilds[0]["permissions"]) if guilds else 0
    bot_id = guilds[0]["id"] if guilds else ""
    print(f"Bot perms -> ManageChannels: {bool(botp & 16)} | ManageRoles: {bool(botp & 32)} | ManageGuild: {bool(botp & 32)}")

    g, err = api("GET", f"https://discord.com/api/v10/guilds/{GID}", token=tok)
    print("Fitur guild:", ", ".join(g.get("features", [])) if g else err)

    # 1) role Level 5
    roles, _ = api("GET", f"https://discord.com/api/v10/guilds/{GID}/roles", token=tok)
    role = next((r for r in roles if r["name"] == LEVEL5_ROLE), None)
    if role:
        print(f"Role '{LEVEL5_ROLE}' sudah ada: {role['id']}")
    elif botp & 32:
        role, err = api("POST", f"https://discord.com/api/v10/guilds/{GID}/roles",
                        {"name": LEVEL5_ROLE, "mentionable": False}, token=tok)
        print(f"Role '{LEVEL5_ROLE}' dibuat: {role['id'] if role else err}")
    else:
        print("Bot nggak punya ManageRoles -> bikin role manual: Settings -> Roles -> New Role 'Level 5'")

    # 2) channel #asset-level + #level (butuh ManageChannels)
    chans, _ = api("GET", f"https://discord.com/api/v10/guilds/{GID}/channels", token=tok)
    names = {c["name"]: c for c in chans if c["type"] == 0}
    if not (botp & 16):
        for name in (ASSET_CHANNEL, LEVEL_CHANNEL):
            print(f"Channel #{name}: BELUM ADA & bot nggak bisa bikin (butuh ManageChannels)")
            print(f"  -> Lu bikin manual: New Channel -> '{name}'. Nanti gw set permission-nya.")
    else:
        role_id = role["id"] if role else ""
        for name, overwrites in (
            (ASSET_CHANNEL, [
                {"id": GID, "type": 0, "allow": "0", "deny": str(VIEW)},
                {"id": role_id, "type": 0, "allow": str(VIEW), "deny": "0"},
                {"id": bot_id, "type": 1, "allow": str(VIEW | SEND), "deny": "0"},
            ]),
            (LEVEL_CHANNEL, [
                {"id": GID, "type": 0, "allow": "0", "deny": str(SEND)},
                {"id": bot_id, "type": 1, "allow": str(SEND), "deny": "0"},
            ]),
        ):
            ch = names.get(name)
            if ch:
                _, err = api("PUT", f"https://discord.com/api/v10/channels/{ch['id']}/permissions/{GID}",
                             {"allow": overwrites[0]["allow"], "deny": overwrites[0]["deny"], "type": 0}, token=tok)
                print(f"#{name}: overwrite @everyone {'OK' if not err else 'GAGAL ' + err}")
            else:
                ch, err = api("POST", f"https://discord.com/api/v10/guilds/{GID}/channels",
                              {"name": name, "type": 0, "permission_overwrites": overwrites}, token=tok)
                print(f"#{name}: dibuat {'OK (' + str(ch['id']) + ')' if ch else 'GAGAL ' + err}")

    # 3) system channel welcome-brodi (pesan join bawaan Discord)
    _, err = api("PATCH", f"https://discord.com/api/v10/guilds/{GID}",
                 {"system_channel_id": WELCOME_CHANNEL_ID, "system_channel_flags": 0}, token=tok)
    print(f"System channel -> #welcome-brodi: {'OK (pesan join muncul di sana)' if not err else 'GAGAL ' + err}")


if __name__ == "__main__":
    main()
