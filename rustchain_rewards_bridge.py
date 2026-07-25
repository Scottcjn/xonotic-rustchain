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
import sys
import time
import sqlite3
import uuid
from datetime import datetime
from decimal import Decimal, getcontext

import requests

from rustchain_dedup import Deduper

getcontext().prec = 18

XONOTIC_LOG = os.path.expanduser("~/.xonotic/data/server.log")
DB_PATH = os.path.expanduser("~/Games/Xonotic/rustchain_rewards.db")
DEDUP_DB_PATH = os.path.expanduser("~/Games/Xonotic/rustchain_dedup.db")
_DEDUPER = Deduper(DEDUP_DB_PATH, "xonotic")

# On-chain payout config (env-driven). Mirrors the Minecraft-bridge pattern:
# tail log -> compute reward -> POST direct to RustChain /wallet/transfer.
# RC_ADMIN_KEY comes from ~/.config/rustchain/admin_key via arena_config.sh.
RUSTCHAIN_API = os.environ.get("RUSTCHAIN_API", "https://50.28.86.131").rstrip("/")
RC_ADMIN_KEY = os.environ.get("RC_ADMIN_KEY", "").strip()
RTC_SOURCE_WALLET = os.environ.get("RTC_SOURCE_WALLET", "founder_community")
ONCHAIN_TIMEOUT = float(os.environ.get("RTC_TRANSFER_TIMEOUT", "10"))
PAYOUTS_ENABLED = bool(RC_ADMIN_KEY)
if not PAYOUTS_ENABLED:
    print("[RTC] WARNING: RC_ADMIN_KEY not set. Running in AUDIT-ONLY mode (local DB writes only, no on-chain payouts).", file=sys.stderr)

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
    "Sophia_Elya": "sophia_elya_arena",
    "SophiaElya": "sophia_elya_arena",
    "Sophia": "sophia_elya_arena",
    "Boris_Volkov": "boris_volkov_arena",
    "Boris": "boris_volkov_arena",
    "AutomatedJanitor": "automatedjanitor-arena",
    "Automatedjanitor": "automatedjanitor-arena",
}


def _post_onchain(wallet: str, amount: Decimal, reason: str) -> tuple:
    """POST to RustChain /wallet/transfer admin endpoint. Returns (ok, pending_id, error_msg).
    Idempotency is not built in yet — see Task #9 for the pattern (match_signature dedup)."""
    if not PAYOUTS_ENABLED:
        return False, None, "audit_only_no_admin_key"
    try:
        r = requests.post(
            f"{RUSTCHAIN_API}/wallet/transfer",
            headers={"X-Admin-Key": RC_ADMIN_KEY, "Content-Type": "application/json"},
            json={
                "from_miner": RTC_SOURCE_WALLET,
                "to_miner": wallet,
                "amount_rtc": float(amount),
                "reason": reason,
            },
            verify=False,  # nginx self-signed on .131
            timeout=ONCHAIN_TIMEOUT,
        )
        try:
            data = r.json()
        except ValueError:
            data = {"_raw": r.text[:300]}
        if r.status_code == 200 and data.get("error") is None:
            return True, data.get("pending_id"), None
        return False, None, f"http_{r.status_code}: {data.get('error') or r.text[:200]}"
    except requests.RequestException as e:
        return False, None, repr(e)[:200]

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

def award_rtc(conn, player, event_type, amount, event_id=None, victim=None):
    wallet = PLAYER_WALLETS.get(player, f"arena-{player.lower()}")
    ts = datetime.now().isoformat()

    if event_id is None:
        # No log identity supplied (manual/admin award): dedup has nothing to
        # match on, and it must never silently swallow the payout instead.
        event_id = f"adhoc:{uuid.uuid4()}"

    # DEDUP guard at the TOP — short-circuit before ANY local writes so a
    # tracker replay (crash + log re-tail) cannot inflate stats.total_rtc.
    # Keeps local DB in sync with on-chain truth.
    # The identity is the SOURCE EVENT (log offset + victim), not the moment we
    # happened to process it: a replay re-reads the same line at the same
    # offset, while two real kills seconds apart are two different offsets.
    dedup_payload = {
        "player_name": player,
        "event_type": event_type,
        "event_id": event_id,
        "victim": victim,
        "kills": 1 if event_type == "kill" else 0,
    }
    sig = _DEDUPER.signature(dedup_payload)
    prior = _DEDUPER.seen(sig)
    if prior:
        print(f"  🔁 dedup: prior #{prior.get('pending_id')}, skipping ({player} {event_type} {amount} RTC)")
        return

    c = conn.cursor()
    c.execute('''INSERT INTO rewards (timestamp, player, wallet, event_type, amount)
                 VALUES (?, ?, ?, ?, ?)''',
              (ts, player, wallet, event_type, str(amount)))
    reward_id = c.lastrowid

    c.execute('''INSERT OR IGNORE INTO stats (player, total_rtc) VALUES (?, '0')''', (player,))
    c.execute('''SELECT total_rtc FROM stats WHERE player = ?''', (player,))
    current = Decimal(c.fetchone()[0])
    new_total = current + amount
    c.execute('''UPDATE stats SET total_rtc = ?, kills = kills + ? WHERE player = ?''',
              (str(new_total), 1 if event_type == "kill" else 0, player))
    conn.commit()

    # On-chain transfer (audit-only fallback if RC_ADMIN_KEY unset)
    # Dedup is enforced UP TOP of this function so we don't re-write local stats either.
    reason = f"xonotic:{event_type}:{player}"
    ok, pending_id, err = _post_onchain(wallet, amount, reason)
    if ok:
        c.execute('UPDATE rewards SET submitted = 1 WHERE id = ?', (reward_id,))
        conn.commit()
        _DEDUPER.record(sig, pending_id, str(amount), dedup_payload)
        print(f"  ⚡ {player} +{amount} RTC ({event_type}) | pending #{pending_id} | Total: {new_total:.6f} RTC")
    else:
        # Record dedup even on chain failure — prevents replay double-writing local stats
        _DEDUPER.record(sig, None, str(amount), dedup_payload)
        print(f"  ⚡ {player} +{amount} RTC ({event_type}) | OFF-CHAIN ({err}) | Total: {new_total:.6f} RTC")

def parse_kill_event(line):
    # Xonotic formats
    kill_match = re.search(r':kill:\d+:\d+:\d+:([^:]+):([^:]+)', line)
    if kill_match:
        return kill_match.group(1).strip(), kill_match.group(2).strip()
    # Passive voice: "X was fragged by Y" — X is victim, Y is killer.
    # This has to be tried BEFORE the active-voice pattern below, which happily
    # matches the same line as killer="was", victim="by".
    passive_match = re.search(r'(\w+) was fragged by (\w+)', line)
    if passive_match:
        return passive_match.group(2).strip(), passive_match.group(1).strip()
    frag_match = re.search(r'(\w+) fragged (\w+)', line)
    if frag_match:
        return frag_match.group(1).strip(), frag_match.group(2).strip()
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
                # Byte offset of this line = immutable identity of the event.
                # Re-tailing the same log yields the same offsets, so a replay
                # dedups; two real kills never share one.
                offset = f.tell()
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                killer, victim = parse_kill_event(line)
                if killer and victim and killer != victim:
                    session_kills += 1
                    
                    # Base kill
                    award_rtc(conn, killer, "kill", REWARDS["kill"], event_id=offset, victim=victim)
                    session_rtc += REWARDS["kill"]
                    
                    # First blood
                    if first_blood:
                        award_rtc(conn, killer, "first_blood", REWARDS["first_blood"], event_id=offset, victim=victim)
                        session_rtc += REWARDS["first_blood"]
                        first_blood = False
                        print(f"  🩸 FIRST BLOOD!")
                    
                    # Boss bonuses
                    if "Boris" in victim:
                        award_rtc(conn, killer, "kill_boris", REWARDS["kill_boris"], event_id=offset, victim=victim)
                        session_rtc += REWARDS["kill_boris"]
                        print(f"  ⚔️ Boris defeated!")
                    elif "Sophia" in victim:
                        award_rtc(conn, killer, "kill_sophia", REWARDS["kill_sophia"], event_id=offset, victim=victim)
                        session_rtc += REWARDS["kill_sophia"]
                        print(f"  🤖 Sophia outsmarted!")
                    
                    # Killstreaks
                    killstreaks[killer] = killstreaks.get(killer, 0) + 1
                    killstreaks[victim] = 0
                    
                    streak = killstreaks[killer]
                    if streak == 5:
                        award_rtc(conn, killer, "killstreak_5", REWARDS["killstreak_5"], event_id=offset, victim=victim)
                        print(f"  🔥 KILLING SPREE!")
                    elif streak == 10:
                        award_rtc(conn, killer, "killstreak_10", REWARDS["killstreak_10"], event_id=offset, victim=victim)
                        print(f"  💀 RAMPAGE!")
                    elif streak == 25:
                        award_rtc(conn, killer, "killstreak_25", REWARDS["killstreak_25"], event_id=offset, victim=victim)
                        print(f"  ⚡ G O D L I K E !")
                    
                    # Domination tracking
                    dom_key = f"{killer}>{victim}"
                    dominations[dom_key] = dominations.get(dom_key, 0) + 1
                    if dominations[dom_key] == 4:
                        award_rtc(conn, killer, "domination", REWARDS["domination"], event_id=offset, victim=victim)
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
