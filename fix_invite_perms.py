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


def effective_status(guild_perm, overwrite=None):
    """Izin efektif Create Invite buat @everyone di sebuah channel.

    guild_perm: bit permission role @everyone (level guild).
    overwrite: dict {allow, deny} dari channel, atau None kalau nggak ada.
    DENY menang atas ALLOW; UNSET ikut izin role guild.
    """
    if overwrite is not None:
        allow = int(overwrite.get("allow", 0)) & CREATE_INSTANT_INVITE
        deny = int(overwrite.get("deny", 0)) & CREATE_INSTANT_INVITE
        if deny:
            return "DENY"
        if allow:
            return "ALLOW"
    return "ALLOW" if guild_perm & CREATE_INSTANT_INVITE else "DENY"


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
        headers={"Authorization": f"Bot {token}", "User-Agent": "InviteGiveawayBot/1.0"},
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
    print(f"Bot perms -> ManageChannels: {bool(botp & 16)} | ManageRoles: {bool(botp & 32)}")

    roles, _ = api("GET", f"https://discord.com/api/v10/guilds/{GID}/roles", token=tok)
    everyone = next((r for r in roles if r["id"] == GID), None)
    ep = int(everyone["permissions"]) if everyone else 0
    guild_ok = bool(ep & CREATE_INSTANT_INVITE)
    print(f"@everyone guild-level: CreateInvite {'ALLOW' if guild_ok else 'DENY/UNSET'}")

    chans, _ = api("GET", f"https://discord.com/api/v10/guilds/{GID}/channels", token=tok)
    texts = [c for c in chans if c["type"] == 0]

    need_fix = []
    for c in texts:
        ow = next((o for o in c.get("permission_overwrites", []) if o["id"] == GID and o["type"] == 0), None)
        eff = effective_status(ep, ow)
        print(f"  #{c['name']:<24} efektif: {eff}")
        if eff != "ALLOW":
            need_fix.append((c, eff))

    print(f"\nPerlu di-fix: {len(need_fix)} channel")
    if not need_fix:
        print("Semua channel text udah bisa di-invite oleh @everyone. Beres!")
        return

    if not guild_ok and (botp & 32):
        newp = str(ep | CREATE_INSTANT_INVITE)
        _, err = api("PATCH", f"https://discord.com/api/v10/guilds/{GID}/roles/{GID}", {"permissions": newp}, token=tok)
        print(f"fix role @everyone: {'OK' if not err else 'GAGAL ' + err}")

    if not (botp & 16):
        print("Bot nggak punya ManageChannels -> channel yang di-DENY harus di-fix manual:")
        for c, _ in need_fix:
            print(f"  - #{c['name']}: Settings channel -> Permissions -> @everyone -> centang 'Create Invite'")
    else:
        for c, _ in need_fix:
            body = {"allow": str(CREATE_INSTANT_INVITE), "deny": "0", "type": 0}
            _, err = api("PUT", f"https://discord.com/api/v10/channels/{c['id']}/permissions/{GID}", body, token=tok)
            print(f"  fix #{c['name']}: {'OK' if not err else 'GAGAL ' + err}")


if __name__ == "__main__":
    main()
