#!/usr/bin/env python3
"""
RustChain Arena - RTC Rewards Bridge
Community Pool: 230,000 RTC

Bumped rewards for satisfying gameplay feel:
- Kill: 0.001 RTC (1,000 kills = 1 RTC)
- Win:  0.01 RTC  (100 wins = 1 RTC)

At 100 active players, 50 kills/day each:
- Daily payout: ~5 RTC
- Pool lasts: 126+ years
"""

import os
import re
import time
import sqlite3
from datetime import datetime
from decimal import Decimal, getcontext

getcontext().prec = 18

XONOTIC_LOG = os.path.expanduser("~/.xonotic/data/server.log")
DB_PATH = os.path.expanduser("~/Games/Xonotic/rustchain_rewards.db")

# Rewards in milli-RTC (0.001 RTC units)
# Much more satisfying numbers!
REWARDS = {
    "kill": Decimal("0.001"),          # 1,000 kills = 1 RTC
    "win": Decimal("0.01"),            # 100 wins = 1 RTC
    "kill_boris": Decimal("0.002"),    # Bonus for gulag commander
    "kill_sophia": Decimal("0.002"),   # Bonus for AI
    "first_blood": Decimal("0.005"),   # First kill of match
    "killstreak_5": Decimal("0.005"),  # Killing spree
    "killstreak_10": Decimal("0.01"),  # Rampage
    "killstreak_25": Decimal("0.025"), # Godlike
    "domination": Decimal("0.003"),    # Kill same player 4x
}

PLAYER_WALLETS = {
    "Scott": "scott-victus-arena",
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        player TEXT,
        wallet TEXT,
        event_type TEXT,
        amount TEXT,
        submitted INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        player TEXT PRIMARY KEY,
        kills INTEGER DEFAULT 0,
        deaths INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        total_rtc TEXT DEFAULT '0'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS session (
        id INTEGER PRIMARY KEY,
        start_time TEXT,
        kills INTEGER DEFAULT 0,
        rtc_earned TEXT DEFAULT '0'
    )''')
    conn.commit()
    return conn

def award_rtc(conn, player, event_type, amount):
    wallet = PLAYER_WALLETS.get(player, f"arena-{player.lower()}")
    
    c = conn.cursor()
    c.execute('''INSERT INTO rewards (timestamp, player, wallet, event_type, amount)
                 VALUES (?, ?, ?, ?, ?)''',
              (datetime.now().isoformat(), player, wallet, event_type, str(amount)))
    
    c.execute('''INSERT OR IGNORE INTO stats (player, total_rtc) VALUES (?, '0')''', (player,))
    c.execute('''SELECT total_rtc FROM stats WHERE player = ?''', (player,))
    current = Decimal(c.fetchone()[0])
    new_total = current + amount
    c.execute('''UPDATE stats SET total_rtc = ?, kills = kills + ? WHERE player = ?''',
              (str(new_total), 1 if event_type == "kill" else 0, player))
    
    conn.commit()
    print(f"  ⚡ {player} +{amount} RTC ({event_type}) | Total: {new_total:.6f} RTC")

def parse_kill_event(line):
    # Xonotic formats
    kill_match = re.search(r':kill:\d+:\d+:\d+:([^:]+):([^:]+)', line)
    if kill_match:
        return kill_match.group(1).strip(), kill_match.group(2).strip()
    frag_match = re.search(r'(\w+) fragged (\w+)', line)
    if frag_match:
        return frag_match.group(1), frag_match.group(2)
    return None, None

def monitor_log(conn):
    print(f"[RTC] Monitoring: {XONOTIC_LOG}")
    
    killstreaks = {}
    dominations = {}  # Track kills against specific players
    first_blood = True
    session_kills = 0
    session_rtc = Decimal("0")
    
    try:
        with open(XONOTIC_LOG, 'r') as f:
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                killer, victim = parse_kill_event(line)
                if killer and victim and killer != victim:
                    session_kills += 1
                    
                    # Base kill
                    award_rtc(conn, killer, "kill", REWARDS["kill"])
                    session_rtc += REWARDS["kill"]
                    
                    # First blood
                    if first_blood:
                        award_rtc(conn, killer, "first_blood", REWARDS["first_blood"])
                        session_rtc += REWARDS["first_blood"]
                        first_blood = False
                        print(f"  🩸 FIRST BLOOD!")
                    
                    # Boss bonuses
                    if "Boris" in victim:
                        award_rtc(conn, killer, "kill_boris", REWARDS["kill_boris"])
                        session_rtc += REWARDS["kill_boris"]
                        print(f"  ⚔️ Boris defeated!")
                    elif "Sophia" in victim:
                        award_rtc(conn, killer, "kill_sophia", REWARDS["kill_sophia"])
                        session_rtc += REWARDS["kill_sophia"]
                        print(f"  🤖 Sophia outsmarted!")
                    
                    # Killstreaks
                    killstreaks[killer] = killstreaks.get(killer, 0) + 1
                    killstreaks[victim] = 0
                    
                    streak = killstreaks[killer]
                    if streak == 5:
                        award_rtc(conn, killer, "killstreak_5", REWARDS["killstreak_5"])
                        print(f"  🔥 KILLING SPREE!")
                    elif streak == 10:
                        award_rtc(conn, killer, "killstreak_10", REWARDS["killstreak_10"])
                        print(f"  💀 RAMPAGE!")
                    elif streak == 25:
                        award_rtc(conn, killer, "killstreak_25", REWARDS["killstreak_25"])
                        print(f"  ⚡ G O D L I K E !")
                    
                    # Domination tracking
                    dom_key = f"{killer}>{victim}"
                    dominations[dom_key] = dominations.get(dom_key, 0) + 1
                    if dominations[dom_key] == 4:
                        award_rtc(conn, killer, "domination", REWARDS["domination"])
                        print(f"  👑 {killer} is DOMINATING {victim}!")
                
                # Match end
                if ":end:" in line or "Match ended" in line or "match ended" in line.lower():
                    print(f"\n  ════════════════════════════════")
                    print(f"  Match Complete!")
                    print(f"  Kills: {session_kills} | RTC Earned: {session_rtc:.6f}")
                    print(f"  ════════════════════════════════\n")
                    
                    killstreaks.clear()
                    dominations.clear()
                    first_blood = True
                    session_kills = 0
                    session_rtc = Decimal("0")
                    
    except FileNotFoundError:
        print(f"[!] Log not found. Start Xonotic with logging:")
        print(f'    ./xonotic-linux64-sdl +log_file "server.log" +map rustcore')

if __name__ == "__main__":
    conn = init_db()
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║         RUSTCHAIN ARENA - RTC REWARDS ACTIVE              ║")
    print("╠═══════════════════════════════════════════════════════════╣")
    print("║  Community Pool: 230,000 RTC                              ║")
    print("╠═══════════════════════════════════════════════════════════╣")
    print(f"║  Kill:           {REWARDS['kill']} RTC                              ║")
    print(f"║  Win Match:      {REWARDS['win']} RTC                               ║")
    print(f"║  Kill Boris:     +{REWARDS['kill_boris']} RTC                             ║")
    print(f"║  Kill Sophia:    +{REWARDS['kill_sophia']} RTC                             ║")
    print(f"║  First Blood:    +{REWARDS['first_blood']} RTC                             ║")
    print(f"║  Killing Spree:  +{REWARDS['killstreak_5']} RTC                             ║")
    print(f"║  Rampage:        +{REWARDS['killstreak_10']} RTC                              ║")
    print(f"║  Godlike:        +{REWARDS['killstreak_25']} RTC                             ║")
    print("╠═══════════════════════════════════════════════════════════╣")
    print("║  1,000 kills = 1 RTC  |  100 wins = 1 RTC                 ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    
    try:
        monitor_log(conn)
    except KeyboardInterrupt:
        print("\n[RTC] Session ended")
