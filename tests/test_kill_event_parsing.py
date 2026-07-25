#!/usr/bin/env python3
"""Kill-line parsing must not pay RTC to a player called "was".

"X was fragged by Y" is matched by the active-voice pattern `(\\w+) fragged
(\\w+)` as killer="was", victim="by". rustchain_discord_bridge has a passive
branch for it, but it sits after the active one and is therefore unreachable;
rustchain_rewards_bridge — the canonical writer for the local DB and for
on-chain transfers — had no passive branch at all.
"""
import os
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import rustchain_discord_bridge
import rustchain_rewards_bridge
from rustchain_dedup import Deduper

PASSIVE = "Boris_Volkov was fragged by Scott"
ACTIVE = "Scott fragged Boris_Volkov"
STRUCTURED = ":kill:1:2:3:Scott:Boris_Volkov"


class KillEventParsingTests(unittest.TestCase):
    def test_rewards_bridge_reads_passive_voice_lines(self):
        self.assertEqual(
            rustchain_rewards_bridge.parse_kill_event(PASSIVE),
            ("Scott", "Boris_Volkov"),
        )

    def test_discord_bridge_reads_passive_voice_lines(self):
        self.assertEqual(
            rustchain_discord_bridge.parse_kill_event(PASSIVE),
            ("Scott", "Boris_Volkov"),
        )

    def test_active_and_structured_lines_are_unchanged(self):
        for parse in (rustchain_rewards_bridge.parse_kill_event,
                      rustchain_discord_bridge.parse_kill_event):
            self.assertEqual(parse(ACTIVE), ("Scott", "Boris_Volkov"))
            self.assertEqual(parse(STRUCTURED), ("Scott", "Boris_Volkov"))
            self.assertEqual(parse("Match ended"), (None, None))

    def test_passive_kill_credits_the_killer_not_a_phantom_player(self):
        tmp = tempfile.mkdtemp()
        rb = rustchain_rewards_bridge
        db_path, dedup_path = rb.DB_PATH, rb._DEDUPER
        rb.DB_PATH = os.path.join(tmp, "rewards.db")
        rb._DEDUPER = Deduper(os.path.join(tmp, "dedup.db"), "xonotic-test")
        try:
            conn = rb.init_db()
            killer, victim = rb.parse_kill_event(PASSIVE)
            rb.award_rtc(conn, killer, "kill", rb.REWARDS["kill"])

            rows = conn.execute(
                "SELECT player, wallet, amount FROM rewards"
            ).fetchall()
            self.assertEqual(
                rows, [("Scott", "scott-victus-arena", str(Decimal("0.001")))]
            )
            self.assertEqual(
                conn.execute("SELECT player, kills FROM stats").fetchall(),
                [("Scott", 1)],
            )
            conn.close()
        finally:
            rb.DB_PATH, rb._DEDUPER = db_path, dedup_path


if __name__ == "__main__":
    unittest.main()
