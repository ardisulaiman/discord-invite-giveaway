# -*- coding: utf-8 -*-
"""Kunci akses #asset-level: cuma rank 5/10/20 yang bisa lihat.

Role:
  Level 5  -> kuning (0xFFFF00)
  Level 10 -> biru   (0x3498DB)
  Level 20 -> putih  (0xFFFFFF)

Semua role rank dapet izin lihat #asset-level (5 ke atas).
Jalanin: .venv/Scripts/python fix_asset_access.py
Bot butuh Manage Roles (role) + Manage Channels (permission channel).
"""

import json
import os
import urllib.error
import urllib.request

GID = "1514855200601407600"
BOT_ID = "1539484072605126729"
VIEW = 1024
SEND = 2048
RANK_ROLES = [
    ("Level 5", 0xFFFF00),   # kuning
    ("Level 10", 0x3498DB),  # biru
    ("Level 20", 0xFFFFFF),  # putih
]
ASSET_CHANNEL = "asset-level"
ASSET_CHANNEL_ID = "1540204070097264660"  # 🗞asset-level (nama pakai emoji, lookup by id lebih aman)


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

    # 1) role rank 5/10/20 + warna
    roles, err = api("GET", f"https://discord.com/api/v10/guilds/{GID}/roles", token=tok)
    if err:
        raise SystemExit(f"Gagal baca roles: {err}")
    existing = {r["name"]: r for r in roles}
    role_ids = {}
    for name, color in RANK_ROLES:
        if name in existing:
            cur = int(existing[name].get("color", 0))
            if cur != color:
                r, e = api("PATCH", f"https://discord.com/api/v10/guilds/{GID}/roles/{existing[name]['id']}",
                           {"color": color}, token=tok)
                print(f"Role '{name}': warna di-update ke {hex(color)} {'OK' if not e else 'GAGAL ' + e}")
            else:
                print(f"Role '{name}': sudah ada, warna {hex(color)} udah bener")
            role_ids[name] = existing[name]["id"]
        else:
            r, e = api("POST", f"https://discord.com/api/v10/guilds/{GID}/roles",
                       {"name": name, "color": color}, token=tok)
            print(f"Role '{name}': {'dibuat ' + r['id'] if r else 'GAGAL ' + e}")
            if r:
                role_ids[name] = r["id"]

    # 2) channel #asset-level (cari by id dulu, fallback by nama)
    chans, err = api("GET", f"https://discord.com/api/v10/guilds/{GID}/channels", token=tok)
    ch = next((c for c in chans if c["type"] == 0 and c["id"] == ASSET_CHANNEL_ID), None)
    if ch is None:
        ch = next((c for c in chans if c["type"] == 0 and c["name"] == ASSET_CHANNEL), None)
    if ch is None:
        print(f"\nChannel #{ASSET_CHANNEL} BELUM ADA - bikin dulu manual di Discord,")
        print("terus jalankan tool ini lagi.")
        return

    # 3) overwrite: @everyone deny lihat; role rank allow lihat; bot allow lihat+kirim
    overwrites = [{"id": GID, "type": 0, "allow": "0", "deny": str(VIEW)}]
    for name, _ in RANK_ROLES:
        if name in role_ids:
            overwrites.append({"id": role_ids[name], "type": 0, "allow": str(VIEW), "deny": "0"})
    overwrites.append({"id": BOT_ID, "type": 1, "allow": str(VIEW | SEND), "deny": "0"})

    _, e = api("PUT", f"https://discord.com/api/v10/channels/{ch['id']}/permissions/{GID}",
               {"allow": "0", "deny": str(VIEW), "type": 0}, token=tok)
    print(f"#{ASSET_CHANNEL}: @everyone deny lihat -> {'OK' if not e else 'GAGAL ' + e}")
    for name, _ in RANK_ROLES:
        if name in role_ids:
            _, e = api("PUT", f"https://discord.com/api/v10/channels/{ch['id']}/permissions/{role_ids[name]}",
                       {"allow": str(VIEW), "deny": "0", "type": 0}, token=tok)
            print(f"#{ASSET_CHANNEL}: role {name} allow lihat -> {'OK' if not e else 'GAGAL ' + e}")
    _, e = api("PUT", f"https://discord.com/api/v10/channels/{ch['id']}/permissions/{BOT_ID}",
               {"allow": str(VIEW | SEND), "deny": "0", "type": 1}, token=tok)
    print(f"#{ASSET_CHANNEL}: bot allow lihat+kirim -> {'OK' if not e else 'GAGAL ' + e}")


if __name__ == "__main__":
    main()
