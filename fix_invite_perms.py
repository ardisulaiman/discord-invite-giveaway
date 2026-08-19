# -*- coding: utf-8 -*-
"""Pastiin @everyone bisa Create Invite di semua channel text.

Jalanin: .venv/Scripts/python fix_invite_perms.py
Bisa dipake ulang kapan aja (misal habis nambah channel baru).
Token dibaca dari .env (file ini gak nyimpen rahasia apa pun).
"""

import json
import os
import urllib.error
import urllib.request

GID = "1514855200601407600"  # ZYRON STUDIO
CREATE_INSTANT_INVITE = 1


def load_token():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DISCORD_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    return ""


def api(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bot {TOK}", "User-Agent": "InviteGiveawayBot/1.0"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read()[:200].decode(errors='replace')}"


TOK = load_token()
if not TOK:
    raise SystemExit("Token kosong - isi DISCORD_BOT_TOKEN di .env")

# bot punya permission yang dibutuhin?
guilds, err = api("GET", "https://discord.com/api/v10/users/@me/guilds")
botp = int(guilds[0]["permissions"]) if guilds else 0
can_edit = bool(botp & 16) and bool(botp & 32)  # ManageChannels + ManageRoles
print(f"Bot perms -> ManageChannels: {bool(botp & 16)} | ManageRoles: {bool(botp & 32)}")

# @everyone guild-level
roles, _ = api("GET", f"https://discord.com/api/v10/guilds/{GID}/roles")
everyone = next((r for r in roles if r["id"] == GID), None)
ep = int(everyone["permissions"]) if everyone else 0
print(f"@everyone guild-level: CreateInvite {'ALLOW' if ep & CREATE_INSTANT_INVITE else 'DENY/UNSET'}")

# channel text + overwrite @everyone
chans, _ = api("GET", f"https://discord.com/api/v10/guilds/{GID}/channels")
texts = [c for c in chans if c["type"] == 0]
need_fix = []
for c in texts:
    ow = next((o for o in c.get("permission_overwrites", []) if o["id"] == GID and o["type"] == 0), None)
    if ow is None:
        status = "UNSET (ikut role guild)"
    else:
        allow, deny = int(ow.get("allow", 0)), int(ow.get("deny", 0))
        status = "ALLOW" if allow & CREATE_INSTANT_INVITE else ("DENY" if deny & CREATE_INSTANT_INVITE else "UNSET")
    print(f"  #{c['name']:<24} {status}")
    if status != "ALLOW":
        need_fix.append(c)

print(f"\nPerlu di-fix: {len(need_fix)} channel")
if not need_fix:
    print("Semua channel text udah bisa di-invite oleh @everyone. Beres!")
elif not can_edit:
    print("Bot nggak punya ManageChannels + ManageRoles -> fix manual dari lu:")
    print("  Server Settings -> Roles -> @everyone -> centang 'Create Invite', Save")
else:
    for c in need_fix:
        body = {"allow": str(CREATE_INSTANT_INVITE), "deny": "0", "type": 0}
        _, err = api("PUT", f"https://discord.com/api/v10/channels/{c['id']}/permissions/{GID}", body)
        print(f"  fix #{c['name']}: {'OK' if not err else 'GAGAL ' + err}")
