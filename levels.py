# -*- coding: utf-8 -*-
"""LevelTracker - XP & level dari aktivitas chat. State di levels.json (permanen).

Formula XP menuju level berikutnya: 50*L*L + 50
  1->2: 100, 2->3: 250, 3->4: 500 (makin tinggi makin susah - sesuai minta user)
"""

import json
import os


class LevelTracker:
    def __init__(self, state_file="levels.json"):
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

    def xp_needed(self, level):
        """XP yang dibutuhin buat naik dari level ini ke level berikutnya."""
        return 50 * level * level + 50

    def add_xp(self, user_id, amount=10):
        """Tambah XP. Return (record, leveled) - leveled True kalau naik level."""
        uid = str(user_id)
        rec = self.state.setdefault(uid, {"xp": 0, "level": 1})
        rec["xp"] += amount
        leveled = False
        while rec["xp"] >= self.xp_needed(rec["level"]):
            rec["xp"] -= self.xp_needed(rec["level"])
            rec["level"] += 1
            leveled = True
        self.save()
        return rec, leveled

    def progress(self, user_id):
        """Return (level, xp_sekarang, xp_yang_dibutuhkan)."""
        uid = str(user_id)
        rec = self.state.get(uid, {"xp": 0, "level": 1})
        return rec["level"], rec["xp"], self.xp_needed(rec["level"])

    def leaderboard(self, top=10):
        rows = sorted(self.state.items(), key=lambda kv: (-kv[1]["level"], -kv[1]["xp"]))
        return rows[:top]
