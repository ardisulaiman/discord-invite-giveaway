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
if FAILURES:
    print(f"RESULT: {len(FAILURES)} FAILURE(S): {FAILURES}")
    sys.exit(1)
print("RESULT: ALL CHECKS PASSED")
