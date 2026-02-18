#!/usr/bin/env python3
"""
RustChain Arena - Discord Integration
Posts game events to Discord in real-time
"""

import os
import re
import time
import json
import requests
import sqlite3
from datetime import datetime
from decimal import Decimal, getcontext

getcontext().prec = 18

# Configuration
XONOTIC_LOG = os.path.expanduser("~/.xonotic/data/server.log")
DB_PATH = os.path.expanduser("~/Games/Xonotic/rustchain_rewards.db")

# Discord webhook - set this to your channel
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")

# Rewards
REWARDS = {
    "kill": Decimal("0.001"),
    "win": Decimal("0.01"),
    "kill_boris": Decimal("0.002"),
    "kill_sophia": Decimal("0.002"),
    "first_blood": Decimal("0.005"),
    "killstreak_5": Decimal("0.005"),
    "killstreak_10": Decimal("0.01"),
    "killstreak_25": Decimal("0.025"),
}

# Cooldown to avoid spam (seconds between Discord posts)
DISCORD_COOLDOWN = 3
last_discord_post = 0

def post_to_discord(embed):
    """Post embed to Discord webhook"""
    global last_discord_post
    
    if not DISCORD_WEBHOOK:
        return False
    
    # Rate limiting
    now = time.time()
    if now - last_discord_post < DISCORD_COOLDOWN:
        return False
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK,
            json={"embeds": [embed]},
            timeout=5
        )
        last_discord_post = now
        return response.status_code == 204
    except Exception as e:
        print(f"[Discord] Error: {e}")
        return False

def announce_kill(killer, victim, rtc_total, streak=0, bonus_type=None):
    """Announce a kill to Discord"""
    
    # Color based on streak
    if streak >= 10:
        color = 0xFF0000  # Red - Rampage
        streak_text = f"🔥 **{streak} KILL STREAK!**"
    elif streak >= 5:
        color = 0xFF6600  # Orange - Killing spree
        streak_text = f"🔥 {streak} streak"
    else:
        color = 0x00AAFF  # Blue - Normal
        streak_text = ""
    
    # Bonus text
    bonus_text = ""
    if bonus_type == "boris":
        bonus_text = "\n⚔️ *Boris defeated!*"
        color = 0xCC0000
    elif bonus_type == "sophia":
        bonus_text = "\n🤖 *Sophia outsmarted!*"
        color = 0x00CCFF
    
    description = f"**{killer}** fragged **{victim}**{bonus_text}"
    if streak_text:
        description += f"\n{streak_text}"
    
    embed = {
        "title": "⚔️ Arena Kill",
        "description": description,
        "color": color,
        "fields": [
            {"name": "💰 RTC Earned", "value": f"+{rtc_total:.4f}", "inline": True}
        ],
        "footer": {"text": "RustChain Arena"},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Only post notable kills to avoid spam
    if streak >= 5 or bonus_type or rtc_total >= Decimal("0.005"):
        post_to_discord(embed)

def announce_first_blood(killer, victim):
    """Announce first blood"""
    embed = {
        "title": "🩸 FIRST BLOOD!",
        "description": f"**{killer}** drew first blood on **{victim}**",
        "color": 0x8B0000,
        "fields": [
            {"name": "💰 Bonus", "value": "+0.005 RTC", "inline": True}
        ],
        "footer": {"text": "RustChain Arena"},
        "timestamp": datetime.utcnow().isoformat()
    }
    post_to_discord(embed)

def announce_godlike(player, streak):
    """Announce godlike streak"""
    embed = {
        "title": "⚡ G O D L I K E !",
        "description": f"**{player}** is UNSTOPPABLE with **{streak} kills!**",
        "color": 0xFFD700,
        "fields": [
            {"name": "💰 Streak Bonus", "value": "+0.025 RTC", "inline": True}
        ],
        "footer": {"text": "RustChain Arena"},
        "timestamp": datetime.utcnow().isoformat()
    }
    post_to_discord(embed)

def announce_match_start(map_name):
    """Announce match starting"""
    embed = {
        "title": "🎮 Match Starting!",
        "description": f"**Map:** {map_name}\n**Mode:** Deathmatch\n\nJoin now and earn RTC!",
        "color": 0x00FF00,
        "footer": {"text": "RustChain Arena"},
        "timestamp": datetime.utcnow().isoformat()
    }
    post_to_discord(embed)

def announce_match_end(stats):
    """Announce match results"""
    # Build leaderboard
    leaderboard = ""
    medals = ["🥇", "🥈", "🥉"]
    for i, (player, data) in enumerate(sorted(stats.items(), key=lambda x: x[1]["kills"], reverse=True)[:3]):
        medal = medals[i] if i < 3 else "  "
        leaderboard += f"{medal} **{player}**: {data['kills']} kills ({data['rtc']:.4f} RTC)\n"
    
    total_rtc = sum(p["rtc"] for p in stats.values())
    total_kills = sum(p["kills"] for p in stats.values())
    
    embed = {
        "title": "🏆 Match Complete!",
        "description": leaderboard,
        "color": 0xFFD700,
        "fields": [
            {"name": "💀 Total Kills", "value": str(total_kills), "inline": True},
            {"name": "💰 RTC Distributed", "value": f"{total_rtc:.4f}", "inline": True}
        ],
        "footer": {"text": "RustChain Arena | Play to Earn"},
        "timestamp": datetime.utcnow().isoformat()
    }
    post_to_discord(embed)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY, timestamp TEXT, player TEXT, wallet TEXT,
        event_type TEXT, amount TEXT, submitted INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        player TEXT PRIMARY KEY, kills INTEGER DEFAULT 0, deaths INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0, total_rtc TEXT DEFAULT '0'
    )''')
    conn.commit()
    return conn

def award_rtc(conn, player, event_type, amount):
    wallet = f"arena-{player.lower()}"
    c = conn.cursor()
    c.execute('INSERT INTO rewards (timestamp, player, wallet, event_type, amount) VALUES (?, ?, ?, ?, ?)',
              (datetime.now().isoformat(), player, wallet, event_type, str(amount)))
    c.execute('INSERT OR IGNORE INTO stats (player, total_rtc) VALUES (?, "0")', (player,))
    c.execute('SELECT total_rtc FROM stats WHERE player = ?', (player,))
    current = Decimal(c.fetchone()[0])
    new_total = current + amount
    c.execute('UPDATE stats SET total_rtc = ?, kills = kills + ? WHERE player = ?',
              (str(new_total), 1 if event_type == "kill" else 0, player))
    conn.commit()
    return new_total

def parse_kill_event(line):
    patterns = [
        r':kill:\d+:\d+:\d+:([^:]+):([^:]+)',
        r'(\w+) fragged (\w+)',
        r'(\w+) was fragged by (\w+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    return None, None

def monitor_log(conn):
    print(f"[Arena] Monitoring: {XONOTIC_LOG}")
    print(f"[Discord] Webhook: {'Connected' if DISCORD_WEBHOOK else 'Not configured'}")
    
    killstreaks = {}
    match_stats = {}
    first_blood = True
    
    try:
        with open(XONOTIC_LOG, 'r') as f:
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                # Map change detection
                if "Map:" in line or "Loading map" in line.lower():
                    map_match = re.search(r'maps/(\w+)', line)
                    if map_match:
                        announce_match_start(map_match.group(1))
                        killstreaks.clear()
                        match_stats.clear()
                        first_blood = True
                
                killer, victim = parse_kill_event(line)
                if killer and victim and killer != victim:
                    rtc_total = Decimal("0")
                    bonus_type = None
                    
                    # Base kill
                    rtc_total += REWARDS["kill"]
                    award_rtc(conn, killer, "kill", REWARDS["kill"])
                    
                    # First blood
                    if first_blood:
                        rtc_total += REWARDS["first_blood"]
                        award_rtc(conn, killer, "first_blood", REWARDS["first_blood"])
                        announce_first_blood(killer, victim)
                        first_blood = False
                    
                    # Boss bonuses
                    if "Boris" in victim:
                        rtc_total += REWARDS["kill_boris"]
                        award_rtc(conn, killer, "kill_boris", REWARDS["kill_boris"])
                        bonus_type = "boris"
                    elif "Sophia" in victim:
                        rtc_total += REWARDS["kill_sophia"]
                        award_rtc(conn, killer, "kill_sophia", REWARDS["kill_sophia"])
                        bonus_type = "sophia"
                    
                    # Killstreaks
                    killstreaks[killer] = killstreaks.get(killer, 0) + 1
                    killstreaks[victim] = 0
                    streak = killstreaks[killer]
                    
                    if streak == 5:
                        rtc_total += REWARDS["killstreak_5"]
                        award_rtc(conn, killer, "killstreak_5", REWARDS["killstreak_5"])
                    elif streak == 10:
                        rtc_total += REWARDS["killstreak_10"]
                        award_rtc(conn, killer, "killstreak_10", REWARDS["killstreak_10"])
                    elif streak == 25:
                        rtc_total += REWARDS["killstreak_25"]
                        award_rtc(conn, killer, "killstreak_25", REWARDS["killstreak_25"])
                        announce_godlike(killer, streak)
                    
                    # Track match stats
                    if killer not in match_stats:
                        match_stats[killer] = {"kills": 0, "rtc": Decimal("0")}
                    match_stats[killer]["kills"] += 1
                    match_stats[killer]["rtc"] += rtc_total
                    
                    # Console output
                    print(f"  ⚡ {killer} +{rtc_total:.4f} RTC (killed {victim})")
                    
                    # Discord announcement (for notable kills)
                    announce_kill(killer, victim, rtc_total, streak, bonus_type)
                
                # Match end
                if ":end:" in line or "Match ended" in line.lower() or "match over" in line.lower():
                    if match_stats:
                        announce_match_end(match_stats)
                        print("\n  ═══════ MATCH COMPLETE ═══════")
                        for player, data in sorted(match_stats.items(), key=lambda x: x[1]["kills"], reverse=True):
                            print(f"  {player}: {data['kills']} kills, {data['rtc']:.4f} RTC")
                        print("  ═══════════════════════════════\n")
                    
                    killstreaks.clear()
                    match_stats.clear()
                    first_blood = True
                    
    except FileNotFoundError:
        print(f"[!] Log not found: {XONOTIC_LOG}")
        print("[!] Start Xonotic with: +log_file server.log")

if __name__ == "__main__":
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║      RUSTCHAIN ARENA - Discord Integration Active         ║")
    print("╠═══════════════════════════════════════════════════════════╣")
    print("║  Events posted to Discord:                                ║")
    print("║  • First Blood                                            ║")
    print("║  • Killing Sprees (5+)                                    ║")
    print("║  • Boss Kills (Boris/Sophia)                              ║")
    print("║  • Godlike Streaks (25+)                                  ║")
    print("║  • Match Results                                          ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    
    if not DISCORD_WEBHOOK:
        print("[!] Set DISCORD_WEBHOOK environment variable to enable Discord posts")
        print("[!] Example: export DISCORD_WEBHOOK='https://discord.com/api/webhooks/...'")
        print()
    
    conn = init_db()
    try:
        monitor_log(conn)
    except KeyboardInterrupt:
        print("\n[Arena] Shutting down...")
