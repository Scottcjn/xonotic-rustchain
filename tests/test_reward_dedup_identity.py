#!/usr/bin/env python3
"""Dedup must key on the source event, not on the minute it was processed.

The dedup payload used to be (player, event_type, kills, wall-clock floored to
the minute). Every kill by the same player inside one minute therefore produced
the same signature, so only the first was paid — and a genuine replay that
landed in a later minute produced a *different* signature, so it was paid twice.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import rustchain_rewards_bridge as rb
from rustchain_dedup import Deduper


class _Stop(Exception):
    """Breaks monitor_log's tail loop once the scripted lines are consumed."""


class RewardDedupIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._saved = (rb.DB_PATH, rb._DEDUPER, rb.XONOTIC_LOG, rb.time.sleep)
        rb.DB_PATH = os.path.join(self.tmp, "rewards.db")
        rb._DEDUPER = Deduper(os.path.join(self.tmp, "dedup.db"), "xonotic-test")
        rb.XONOTIC_LOG = os.path.join(self.tmp, "server.log")
        open(rb.XONOTIC_LOG, "w").close()
        self.conn = rb.init_db()

    def tearDown(self):
        self.conn.close()
        rb.DB_PATH, rb._DEDUPER, rb.XONOTIC_LOG, rb.time.sleep = self._saved

    def _tail(self, lines):
        """Run monitor_log over `lines`, feeding one per idle tick."""
        pending = iter(lines)

        def fake_sleep(_seconds):
            try:
                nxt = next(pending)
            except StopIteration:
                raise _Stop
            with open(rb.XONOTIC_LOG, "a") as fh:
                fh.write(nxt + "\n")

        rb.time.sleep = fake_sleep
        try:
            rb.monitor_log(self.conn)
        except _Stop:
            pass

    def _rows(self):
        return self.conn.execute(
            "SELECT player, event_type FROM rewards ORDER BY id"
        ).fetchall()

    def test_every_kill_in_the_same_minute_is_paid(self):
        self._tail([
            "Scott fragged Boris_Volkov",
            "Scott fragged Miner_Node1",
            "Scott fragged Miner_Node2",
        ])

        kills = [r for r in self._rows() if r[1] == "kill"]
        self.assertEqual(kills, [("Scott", "kill")] * 3)
        self.assertEqual(
            self.conn.execute(
                "SELECT kills FROM stats WHERE player = 'Scott'"
            ).fetchone()[0],
            3,
        )

    def test_replaying_the_same_log_event_pays_once(self):
        line = "Scott fragged Boris_Volkov"
        self._tail([line])
        first = self._rows()

        # Bridge restarted and re-read the same log from the top, minutes later.
        later = rb.time.time() + 600
        with mock.patch.object(rb.time, "time", lambda: later):
            with open(rb.XONOTIC_LOG) as f:
                killer, victim = rb.parse_kill_event(f.readline())
                rb.award_rtc(self.conn, killer, "kill", rb.REWARDS["kill"],
                             event_id=0, victim=victim)

        self.assertEqual(self._rows(), first)

    def test_awards_without_an_event_id_are_never_swallowed(self):
        for _ in range(2):
            rb.award_rtc(self.conn, "Scott", "win", rb.REWARDS["win"])

        self.assertEqual(self._rows(), [("Scott", "win"), ("Scott", "win")])


if __name__ == "__main__":
    unittest.main()
