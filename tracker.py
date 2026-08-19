"""Inti logika invite tracker - pure Python tanpa discord.py, biar gampang di-test.

State disimpan di JSON: per guild -> snapshot invite (code, inviter, uses)
+ progres per user. Dipisah dari bot.py biar logikanya bisa diuji offline.
"""

import json
import os


class InviteTracker:
    def __init__(self, state_file="invite_state.json"):
        self.state_file = state_file
        self.state = self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def guild_state(self, guild_id):
        g = self.state.setdefault("guilds", {}).setdefault(str(guild_id), {})
        g.setdefault("invites", {})
        g.setdefault("progress", {})
        return g

    def snapshot_invites(self, guild_id, invite_list):
        """invite_list: iterable of (code, inviter_id, uses). Simpan snapshot terbaru."""
        g = self.guild_state(guild_id)
        g["invites"] = {
            code: {"inviter": str(inviter_id) if inviter_id else None, "uses": int(uses)}
            for code, inviter_id, uses in invite_list
        }
        self.save()

    def find_inviter(self, guild_id, fresh_list):
        """Bandingkan snapshot lama vs daftar invite terbaru.

        Cari invite yang uses-nya naik -> itu sumber join-nya.
        Return (inviter_id, code) atau (None, None).
        """
        g = self.guild_state(guild_id)
        old = g["invites"]
        new = {
            code: {"inviter": str(inviter_id) if inviter_id else None, "uses": int(uses)}
            for code, inviter_id, uses in fresh_list
        }
        # 1) invite yang udah ada, uses naik
        for code, info in new.items():
            if code in old and info["uses"] > old[code]["uses"]:
                return info["inviter"], code
        # 2) invite BARU yang udah kepake (dibuat setelah snapshot terakhir)
        for code, info in new.items():
            if code not in old and info["uses"] >= 1:
                return info["inviter"], code
        return None, None

    def record(self, guild_id, inviter_id, amount=1):
        g = self.guild_state(guild_id)
        key = str(inviter_id)
        g["progress"][key] = g["progress"].get(key, 0) + amount
        self.save()
        return g["progress"][key]

    def progress(self, guild_id, user_id):
        return self.guild_state(guild_id)["progress"].get(str(user_id), 0)

    def leaderboard(self, guild_id, top=10):
        prog = self.guild_state(guild_id)["progress"]
        return sorted(prog.items(), key=lambda kv: -kv[1])[:top]
