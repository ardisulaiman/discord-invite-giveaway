# -*- coding: utf-8 -*-
"""Test kanonik tracker.py - jalanin: .venv/Scripts/python test_tracker.py

Bukan pytest, script manual yang exit non-zero kalau ada yang gagal.
"""

import importlib.util
import os
import sys
import tempfile

tmpdir = tempfile.mkdtemp(prefix="invite_tracker_test_")
state_file = os.path.join(tmpdir, "invite_state.json")

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

spec = importlib.util.spec_from_file_location("tracker", os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker.py"))
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)

tr = t.InviteTracker(state_file)

FAILURES = []


def check(name, cond, detail=""):
    status = "OK  " if cond else "FAIL"
    print(f"  [{status}] {name}" + (f" -- {detail}" if detail else ""))
    if not cond:
        FAILURES.append(name)


G = "12345"
print("=" * 60)
print("1) FIND INVITER - invite lama naik uses")
print("=" * 60)
tr.snapshot_invites(G, [("abc", 111, 3), ("def", 222, 1)])
inviter, code = tr.find_inviter(G, [("abc", 111, 4), ("def", 222, 1)])
check("uses 3->4 ketemu inviter 111", inviter == "111" and code == "abc", f"{inviter}/{code}")

print()
print("=" * 60)
print("2) FIND INVITER - invite baru yang udah kepake")
print("=" * 60)
tr.snapshot_invites(G, [("abc", 111, 4), ("def", 222, 1)])  # refresh abis test 1
inviter, code = tr.find_inviter(G, [("abc", 111, 4), ("def", 222, 1), ("ghi", 333, 1)])
check("invite baru uses>=1 ketemu inviter 333", inviter == "333" and code == "ghi", f"{inviter}/{code}")

print()
print("=" * 60)
print("3) FIND INVITER - gak ada perubahan")
print("=" * 60)
tr.snapshot_invites(G, [("abc", 111, 4), ("def", 222, 1), ("ghi", 333, 1)])
inviter, code = tr.find_inviter(G, [("abc", 111, 4), ("def", 222, 1), ("ghi", 333, 1)])
check("nggak ada yang naik -> None", inviter is None and code is None)

print()
print("=" * 60)
print("4) PROGRES + PERSISTEN")
print("=" * 60)
tr.record(G, 111)
tr.record(G, 111)
tr.record(G, 222)
check("user 111 jadi 2", tr.progress(G, 111) == 2)
check("user 222 jadi 1", tr.progress(G, 222) == 1)
lb = tr.leaderboard(G, 10)
check("leaderboard urut benar", lb[0] == ("111", 2) and lb[1] == ("222", 1), str(lb))

t2 = t.InviteTracker(state_file)  # load ulang dari disk
check("state persist ke disk", t2.progress(G, 111) == 2)

print()
print("=" * 60)
print("5) IZIN EFEKTIF CREATE INVITE (fix_invite_perms.py)")
print("=" * 60)
_spec_f = importlib.util.spec_from_file_location(
    "fix_invite_perms", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_invite_perms.py")
)
fip = importlib.util.module_from_spec(_spec_f)
_spec_f.loader.exec_module(fip)
CREATE = fip.CREATE_INSTANT_INVITE
G_ALLOW, G_DENY = CREATE, 0
check("guild ALLOW + tanpa overwrite -> ALLOW", fip.effective_status(G_ALLOW) == "ALLOW")
check("guild DENY + tanpa overwrite -> DENY", fip.effective_status(G_DENY) == "DENY")
check("overwrite DENY menang atas guild ALLOW", fip.effective_status(G_ALLOW, {"allow": "0", "deny": str(CREATE)}) == "DENY")
check("overwrite ALLOW menang atas guild DENY", fip.effective_status(G_DENY, {"allow": str(CREATE), "deny": "0"}) == "ALLOW")
check("overwrite UNSET ikut guild ALLOW", fip.effective_status(G_ALLOW, {"allow": "0", "deny": "0"}) == "ALLOW")
check("overwrite UNSET ikut guild DENY", fip.effective_status(G_DENY, {"allow": "0", "deny": "0"}) == "DENY")

print()
print("=" * 60)
print("6) KONFIG DEPLOY RAILWAY (railpack.toml + requirements)")
print("=" * 60)
_rp = open(os.path.join(REPO_DIR, "railpack.toml"), encoding="utf-8").read()
check("railpack: buildCommand pip install requirements", "pip install -r requirements.txt" in _rp)
check("railpack: startCommand python bot.py", 'startCommand = "python bot.py"' in _rp)
_req = open(os.path.join(REPO_DIR, "requirements.txt"), encoding="utf-8").read()
check("requirements: discord.py + dotenv", "discord.py" in _req and "python-dotenv" in _req)

print()
print("=" * 60)
print("7) PING SERVER KEEP-ALIVE (bot.py _start_ping_server)")
print("=" * 60)
import importlib.util as _ilu

_botspec = _ilu.spec_from_file_location("bot", os.path.join(REPO_DIR, "bot.py"))
botmod = _ilu.module_from_spec(_botspec)
_botspec.loader.exec_module(botmod)
os.environ["PING_PORT"] = "8123"
botmod._start_ping_server()
import urllib.request as _ur

try:
    with _ur.urlopen("http://127.0.0.1:8123/ping", timeout=5) as r:
        body = r.read().decode()
        check("/ping jawab 200 + pong", r.status == 200 and body == "pong", f"{r.status}/{body}")
except Exception as e:
    check("/ping jawab 200 + pong", False, str(e))
os.environ.pop("PING_PORT", None)
check("PING_PORT kosong -> server nggak nyala", botmod._start_ping_server() is None)

print()
if FAILURES:
    print(f"RESULT: {len(FAILURES)} FAILURE(S): {FAILURES}")
    sys.exit(1)
print("RESULT: ALL CHECKS PASSED")
