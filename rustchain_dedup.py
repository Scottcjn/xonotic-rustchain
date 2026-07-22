#!/usr/bin/env python3
"""
RustChain shared idempotency module for game-bridge fleet.

Wraps award_rtc()-style functions so a bridge crash + log re-tail does NOT
double-pay real on-chain RTC. Pattern lifted from ut99_rtc_receiver.py on .131:
hash the immutable identity of the event, store sig->pending_id in local SQLite,
short-circuit on replay.

Stdlib only. WAL-mode SQLite. 12h retention.
"""

import os
import json
import time
import hashlib
import sqlite3
from functools import wraps

RETENTION_SECONDS = 12 * 3600  # 12h prune window

# Fields that form the dedup identity. Missing fields are silently dropped.
# `event_id` is the immutable identity of the source event (e.g. the byte offset
# of the log line) — prefer it over `timestamp`, which is only a coarse fallback
# and is floored to the minute to absorb tracker clock noise.
_SIG_FIELDS = ("player_name", "event_type", "event_id", "timestamp", "kills", "victim")


class Deduper:
    def __init__(self, db_path: str, label: str):
        self.db_path = db_path
        self.label = label
        self._init_db()

    def _conn(self):
        c = sqlite3.connect(self.db_path, timeout=5.0)
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        return c

    def _init_db(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)) or ".", exist_ok=True)
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS dedup_events (
                sig TEXT PRIMARY KEY,
                label TEXT,
                pending_id TEXT,
                rtc_amount TEXT,
                payload_json TEXT,
                ts INTEGER
            )""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_dedup_ts ON dedup_events(ts)")

    def signature(self, payload: dict) -> str:
        """Deterministic 16-hex SHA256 over present sig-fields + label."""
        parts = {"_label": self.label}
        for f in _SIG_FIELDS:
            if f in payload and payload[f] is not None:
                v = payload[f]
                if f == "timestamp":
                    try:
                        v = int(float(v) // 60) * 60  # floor to minute
                    except (TypeError, ValueError):
                        pass
                parts[f] = v
        blob = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def seen(self, sig: str):
        """Return prior {pending_id, rtc_amount, timestamp} or None."""
        self._prune()
        with self._conn() as c:
            row = c.execute(
                "SELECT pending_id, rtc_amount, ts FROM dedup_events WHERE sig=? AND label=?",
                (sig, self.label),
            ).fetchone()
        if not row:
            return None
        return {"pending_id": row[0], "rtc_amount": row[1], "timestamp": row[2]}

    def record(self, sig: str, pending_id, rtc_amount, payload: dict):
        """Persist sig -> (pending_id, amount, payload, ts)."""
        with self._conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO dedup_events (sig, label, pending_id, rtc_amount, payload_json, ts) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (sig, self.label, str(pending_id) if pending_id is not None else None,
                 str(rtc_amount), json.dumps(payload, default=str, sort_keys=True), int(time.time())),
            )

    def _prune(self):
        cutoff = int(time.time()) - RETENTION_SECONDS
        with self._conn() as c:
            c.execute("DELETE FROM dedup_events WHERE ts < ?", (cutoff,))

    def wrap_award(self, award_func):
        """Decorator: if payload sig already seen, return prior {deduped: True, ...}
        instead of invoking the underlying award func."""
        @wraps(award_func)
        def wrapper(*args, payload: dict, **kwargs):
            sig = self.signature(payload)
            prior = self.seen(sig)
            if prior:
                return {"deduped": True, "sig": sig, **prior}
            result = award_func(*args, payload=payload, **kwargs)
            pid = result.get("pending_id") if isinstance(result, dict) else None
            amt = result.get("rtc_amount") if isinstance(result, dict) else None
            self.record(sig, pid, amt, payload)
            return result if isinstance(result, dict) else {"deduped": False, "sig": sig, "result": result}
        return wrapper


if __name__ == "__main__":
    # Smoke test: same payload twice -> second call MUST short-circuit.
    test_db = "/tmp/rustchain_dedup_smoke.db"
    if os.path.exists(test_db):
        os.unlink(test_db)
    d = Deduper(test_db, "xonotic")

    payload = {
        "player_name": "Scott",
        "event_type": "kill",
        "timestamp": time.time(),
        "kills": 1,
        "victim": "Boris_Volkov",
    }

    calls = {"n": 0}

    @d.wrap_award
    def fake_award(*, payload):
        calls["n"] += 1
        return {"pending_id": 4242, "rtc_amount": "0.001", "deduped": False}

    r1 = fake_award(payload=payload)
    r2 = fake_award(payload=payload)

    print(f"call 1: {r1}")
    print(f"call 2: {r2}")
    print(f"underlying fake_award invocations: {calls['n']} (expect 1)")
    assert calls["n"] == 1, "DEDUP FAILED — underlying func called twice"
    assert r2.get("deduped") is True, "DEDUP FAILED — second call not flagged"
    assert r2.get("pending_id") == "4242", "DEDUP FAILED — pending_id not preserved"
    print("OK: dedup short-circuit verified")
