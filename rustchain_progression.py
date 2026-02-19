#!/usr/bin/env python3
"""
RustChain Arena - Progression (230k Pool)
1,000 kills = 1 RTC
"""

import sqlite3
import os
from decimal import Decimal

DB_PATH = os.path.expanduser("~/Games/Xonotic/rustchain_rewards.db")

RANKS = [
    {"name": "Unranked",       "rtc": Decimal("0"),     "kills": 0,       "color": "^7"},
    {"name": "Recruit",        "rtc": Decimal("0.01"),  "kills": 10,      "color": "^8"},
    {"name": "Miner",          "rtc": Decimal("0.1"),   "kills": 100,     "color": "^3"},
    {"name": "Node Runner",    "rtc": Decimal("1"),     "kills": 1000,    "color": "^2"},
    {"name": "Validator",      "rtc": Decimal("10"),    "kills": 10000,   "color": "^4"},
    {"name": "Block Producer", "rtc": Decimal("100"),   "kills": 100000,  "color": "^6"},
    {"name": "Chain Master",   "rtc": Decimal("1000"),  "kills": 1000000, "color": "^1"},
    {"name": "Genesis Elite",  "rtc": Decimal("10000"), "kills": 10000000,"color": "^5"},
]

def get_stats(player):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT kills, deaths, wins, total_rtc FROM stats WHERE player = ?', (player,))
        row = c.fetchone()
        conn.close()
        if row:
            return {"kills": row[0], "deaths": row[1], "wins": row[2], "rtc": Decimal(row[3] or "0")}
    except Exception:
        pass
    return {"kills": 0, "deaths": 0, "wins": 0, "rtc": Decimal("0")}

def get_rank(rtc):
    current = RANKS[0]
    for r in RANKS:
        if rtc >= r["rtc"]:
            current = r
    return current

def print_profile(player):
    stats = get_stats(player)
    rank = get_rank(stats["rtc"])
    kd = stats["kills"] / max(stats["deaths"], 1)
    
    # Find next rank
    next_rank = None
    for r in RANKS:
        if stats["rtc"] < r["rtc"]:
            next_rank = r
            break
    
    print()
    print("╔═══════════════════════════════════════════════════╗")
    print(f"║  {rank['color']}{player}^7 - {rank['name']}".ljust(60) + "║")
    print("╠═══════════════════════════════════════════════════╣")
    print(f"║  RTC Balance: {stats['rtc']:.6f}".ljust(52) + "║")
    print(f"║  Kills: {stats['kills']:,}  |  K/D: {kd:.2f}".ljust(52) + "║")
    print(f"║  Wins: {stats['wins']:,}".ljust(52) + "║")
    
    if next_rank:
        needed = next_rank["rtc"] - stats["rtc"]
        kills_needed = int(needed * 1000)
        progress = float(stats["rtc"] / next_rank["rtc"] * 100)
        bar = "█" * int(progress/5) + "░" * (20 - int(progress/5))
        print("╠═══════════════════════════════════════════════════╣")
        print(f"║  Next: {next_rank['color']}{next_rank['name']}^7 ({needed:.3f} RTC / ~{kills_needed:,} kills)".ljust(60) + "║")
        print(f"║  [{bar}] {progress:.1f}%".ljust(52) + "║")
    
    print("╚═══════════════════════════════════════════════════╝")

if __name__ == "__main__":
    import sys
    player = sys.argv[1] if len(sys.argv) > 1 else "Scott"
    print_profile(player)
    print("\n  Rank Ladder:")
    for r in RANKS:
        print(f"  {r['color']}{r['name']:15}^7  {r['rtc']:>8} RTC  (~{r['kills']:,} kills)")
