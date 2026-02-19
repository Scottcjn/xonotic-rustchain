#!/usr/bin/env python3
"""
RustChain Arena - Style Rank System
ULTRAKILL-inspired aggressive play rewards with RTC multipliers.
"""

import os
import re
import time
import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import IntEnum

getcontext().prec = 18

# Configuration
XONOTIC_LOG = os.path.expanduser("~/.xonotic/data/server.log")
DB_PATH = os.path.expanduser("~/Games/Xonotic/rustchain_rewards.db")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")

# Style Ranks - ULTRAKILL inspired
class StyleRank(IntEnum):
    D_DORMANT = 0      # 1.0x - Default, camping
    C_CALCULATING = 1  # 1.2x - Got a kill
    B_BUILDING = 2     # 1.5x - Building momentum
    A_ATTACKING = 3    # 2.0x - Aggressive play
    S_STAKING = 4      # 3.0x - Dominating
    SS_SLASHING = 5    # 4.0x - On fire
    SSS_SATOSHI = 6    # 5.0x - LEGENDARY

RANK_CONFIG = {
    StyleRank.D_DORMANT: {
        "name": "DORMANT",
        "multiplier": Decimal("1.0"),
        "color": "808080",  # Gray
        "threshold": 0,
        "decay_rate": 0,
    },
    StyleRank.C_CALCULATING: {
        "name": "CALCULATING",
        "multiplier": Decimal("1.2"),
        "color": "00FFFF",  # Cyan
        "threshold": 100,
        "decay_rate": 10,  # Points per second
    },
    StyleRank.B_BUILDING: {
        "name": "BUILDING",
        "multiplier": Decimal("1.5"),
        "color": "00FF00",  # Green
        "threshold": 300,
        "decay_rate": 15,
    },
    StyleRank.A_ATTACKING: {
        "name": "ATTACKING",
        "multiplier": Decimal("2.0"),
        "color": "FFFF00",  # Yellow
        "threshold": 600,
        "decay_rate": 25,
    },
    StyleRank.S_STAKING: {
        "name": "STAKING",
        "multiplier": Decimal("3.0"),
        "color": "FF8800",  # Orange
        "threshold": 1000,
        "decay_rate": 40,
    },
    StyleRank.SS_SLASHING: {
        "name": "SLASHING",
        "multiplier": Decimal("4.0"),
        "color": "FF0000",  # Red
        "threshold": 1500,
        "decay_rate": 60,
    },
    StyleRank.SSS_SATOSHI: {
        "name": "✦ SATOSHI ✦",
        "multiplier": Decimal("5.0"),
        "color": "FFD700",  # Gold
        "threshold": 2500,
        "decay_rate": 100,
    },
}

# Combo definitions
COMBOS = {
    "double_kill": {"kills": 2, "window": 3.0, "bonus": 50, "name": "DOUBLE KILL"},
    "triple_kill": {"kills": 3, "window": 4.0, "bonus": 150, "name": "TRIPLE KILL"},
    "ultra_kill": {"kills": 4, "window": 5.0, "bonus": 300, "name": "ULTRA KILL"},
    "godlike": {"kills": 5, "window": 6.0, "bonus": 500, "name": "G O D L I K E"},
}

# Special kill bonuses
SPECIAL_KILLS = {
    "first_blood": {"bonus": 200, "name": "FIRST BLOOD", "rtc_bonus": Decimal("0.005")},
    "revenge": {"bonus": 75, "name": "REVENGE", "rtc_bonus": Decimal("0.001")},
    "headshot": {"bonus": 50, "name": "HEADSHOT", "rtc_bonus": Decimal("0.0005")},
    "midair": {"bonus": 100, "name": "MIDAIR", "rtc_bonus": Decimal("0.002")},
    "boss_kill_boris": {"bonus": 150, "name": "BOSS SLAIN: BORIS", "rtc_bonus": Decimal("0.003")},
    "boss_kill_sophia": {"bonus": 150, "name": "BOSS SLAIN: SOPHIA", "rtc_bonus": Decimal("0.003")},
}

# Weapon variety bonuses
WEAPON_VARIETY_BONUS = 25  # Points per unique weapon used

@dataclass
class PlayerStyle:
    """Track a player's style state"""
    name: str
    points: int = 0
    rank: StyleRank = StyleRank.D_DORMANT
    kills_this_life: int = 0
    total_kills: int = 0
    deaths: int = 0
    last_kill_time: float = 0
    recent_kills: List[float] = field(default_factory=list)
    weapons_used: set = field(default_factory=set)
    last_killer: str = ""
    total_rtc: Decimal = Decimal("0")
    killstreak: int = 0
    best_streak: int = 0

    def add_points(self, points: int) -> Tuple[StyleRank, bool]:
        """Add style points and check for rank up"""
        old_rank = self.rank
        self.points += points

        # Check for rank up
        new_rank = StyleRank.D_DORMANT
        for rank in reversed(list(StyleRank)):
            if self.points >= RANK_CONFIG[rank]["threshold"]:
                new_rank = rank
                break

        self.rank = new_rank
        ranked_up = new_rank > old_rank
        return new_rank, ranked_up

    def decay(self, delta_time: float):
        """Decay points over time"""
        if self.rank == StyleRank.D_DORMANT:
            return

        decay_rate = RANK_CONFIG[self.rank]["decay_rate"]
        self.points = max(0, self.points - int(decay_rate * delta_time))

        # Check for rank down
        for rank in reversed(list(StyleRank)):
            if self.points >= RANK_CONFIG[rank]["threshold"]:
                self.rank = rank
                break
        else:
            self.rank = StyleRank.D_DORMANT

    def on_death(self):
        """Handle death - partial reset"""
        self.points = self.points // 2  # Lose half points
        self.kills_this_life = 0
        self.killstreak = 0
        self.weapons_used.clear()
        self.recent_kills.clear()

        # Recalculate rank
        for rank in reversed(list(StyleRank)):
            if self.points >= RANK_CONFIG[rank]["threshold"]:
                self.rank = rank
                break
        else:
            self.rank = StyleRank.D_DORMANT

    def get_multiplier(self) -> Decimal:
        """Get current RTC multiplier"""
        return RANK_CONFIG[self.rank]["multiplier"]


class StyleSystem:
    """Main style tracking system"""

    def __init__(self):
        self.players: Dict[str, PlayerStyle] = {}
        self.first_blood_claimed = False
        self.match_start_time = time.time()
        self.last_update = time.time()

        # Initialize database
        self.init_db()

    def init_db(self):
        """Initialize rewards database with style tracking"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Enhanced rewards table
        c.execute('''CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            player TEXT,
            wallet TEXT,
            event_type TEXT,
            amount TEXT,
            style_rank TEXT,
            multiplier TEXT,
            base_amount TEXT,
            combo_type TEXT,
            submitted INTEGER DEFAULT 0
        )''')

        # Style statistics
        c.execute('''CREATE TABLE IF NOT EXISTS style_stats (
            player TEXT PRIMARY KEY,
            total_kills INTEGER DEFAULT 0,
            total_deaths INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            highest_rank_achieved INTEGER DEFAULT 0,
            total_rtc_earned TEXT DEFAULT '0',
            total_style_points INTEGER DEFAULT 0,
            sss_count INTEGER DEFAULT 0
        )''')

        conn.commit()
        conn.close()

    def get_player(self, name: str) -> PlayerStyle:
        """Get or create player style tracker"""
        if name not in self.players:
            self.players[name] = PlayerStyle(name=name)
        return self.players[name]

    def process_kill(self, killer: str, victim: str, weapon: str = "unknown") -> Dict:
        """Process a kill event and calculate rewards"""
        now = time.time()
        player = self.get_player(killer)
        victim_player = self.get_player(victim)

        result = {
            "killer": killer,
            "victim": victim,
            "weapon": weapon,
            "base_rtc": Decimal("0.001"),  # Base kill reward
            "bonus_rtc": Decimal("0"),
            "style_points": 100,  # Base kill points
            "bonuses": [],
            "combo": None,
            "rank_before": player.rank,
            "rank_after": player.rank,
            "ranked_up": False,
            "multiplier": player.get_multiplier(),
        }

        # Track kill timing
        player.recent_kills.append(now)
        player.recent_kills = [t for t in player.recent_kills if now - t < 10]  # Last 10 seconds
        player.last_kill_time = now
        player.kills_this_life += 1
        player.total_kills += 1
        player.killstreak += 1

        if player.killstreak > player.best_streak:
            player.best_streak = player.killstreak

        # === SPECIAL BONUSES ===

        # First Blood
        if not self.first_blood_claimed:
            self.first_blood_claimed = True
            bonus = SPECIAL_KILLS["first_blood"]
            result["style_points"] += bonus["bonus"]
            result["bonus_rtc"] += bonus["rtc_bonus"]
            result["bonuses"].append(bonus["name"])

        # Revenge Kill
        if player.last_killer == victim:
            bonus = SPECIAL_KILLS["revenge"]
            result["style_points"] += bonus["bonus"]
            result["bonus_rtc"] += bonus["rtc_bonus"]
            result["bonuses"].append(bonus["name"])
            player.last_killer = ""

        # Boss Kills
        if "Boris" in victim:
            bonus = SPECIAL_KILLS["boss_kill_boris"]
            result["style_points"] += bonus["bonus"]
            result["bonus_rtc"] += bonus["rtc_bonus"]
            result["bonuses"].append(bonus["name"])
        elif "Sophia" in victim:
            bonus = SPECIAL_KILLS["boss_kill_sophia"]
            result["style_points"] += bonus["bonus"]
            result["bonus_rtc"] += bonus["rtc_bonus"]
            result["bonuses"].append(bonus["name"])

        # Weapon Variety
        if weapon not in player.weapons_used:
            player.weapons_used.add(weapon)
            if len(player.weapons_used) > 1:
                result["style_points"] += WEAPON_VARIETY_BONUS * len(player.weapons_used)
                result["bonuses"].append(f"VARIETY x{len(player.weapons_used)}")

        # === COMBO DETECTION ===
        kills_in_window = len(player.recent_kills)

        for combo_name, combo_def in sorted(COMBOS.items(), key=lambda x: -x[1]["kills"]):
            recent = [t for t in player.recent_kills if now - t < combo_def["window"]]
            if len(recent) >= combo_def["kills"]:
                result["combo"] = combo_def["name"]
                result["style_points"] += combo_def["bonus"]
                result["bonus_rtc"] += Decimal("0.001") * combo_def["kills"]
                break

        # === KILLSTREAK BONUSES ===
        streak_bonuses = {
            5: ("KILLING SPREE", 100, Decimal("0.005")),
            10: ("RAMPAGE", 250, Decimal("0.01")),
            15: ("DOMINATING", 400, Decimal("0.015")),
            20: ("UNSTOPPABLE", 600, Decimal("0.02")),
            25: ("GODLIKE", 1000, Decimal("0.025")),
        }

        if player.killstreak in streak_bonuses:
            name, points, rtc = streak_bonuses[player.killstreak]
            result["style_points"] += points
            result["bonus_rtc"] += rtc
            result["bonuses"].append(f"{name} ({player.killstreak})")

        # === APPLY STYLE POINTS ===
        new_rank, ranked_up = player.add_points(result["style_points"])
        result["rank_after"] = new_rank
        result["ranked_up"] = ranked_up
        result["multiplier"] = player.get_multiplier()

        # === CALCULATE FINAL RTC ===
        base = result["base_rtc"] + result["bonus_rtc"]
        result["total_rtc"] = base * result["multiplier"]
        player.total_rtc += result["total_rtc"]

        # Update victim
        victim_player.last_killer = killer
        victim_player.on_death()
        victim_player.deaths += 1

        # Save to database
        self.save_reward(result)

        return result

    def save_reward(self, result: Dict):
        """Save reward to database"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        rank_name = RANK_CONFIG[result["rank_after"]]["name"]

        c.execute('''INSERT INTO rewards
            (timestamp, player, wallet, event_type, amount, style_rank, multiplier, base_amount, combo_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (datetime.now().isoformat(),
             result["killer"],
             f"arena-{result['killer'].lower()}",
             "kill",
             str(result["total_rtc"]),
             rank_name,
             str(result["multiplier"]),
             str(result["base_rtc"] + result["bonus_rtc"]),
             result["combo"] or ""))

        conn.commit()
        conn.close()

    def update(self):
        """Update decay for all players"""
        now = time.time()
        delta = now - self.last_update
        self.last_update = now

        for player in self.players.values():
            player.decay(delta)

    def reset_match(self):
        """Reset for new match"""
        self.first_blood_claimed = False
        self.match_start_time = time.time()
        # Don't fully reset players - keep some progression

    def format_kill_message(self, result: Dict) -> str:
        """Format kill message for console"""
        rank_cfg = RANK_CONFIG[result["rank_after"]]
        rank_name = rank_cfg["name"]

        msg = f"  ⚡ {result['killer']}"

        if result["ranked_up"]:
            msg += f" 🔥 RANK UP → {rank_name}"

        msg += f" [{rank_name}]"
        msg += f" +{result['total_rtc']:.4f} RTC"
        msg += f" ({result['multiplier']}x)"

        if result["bonuses"]:
            msg += f" | {' + '.join(result['bonuses'])}"

        if result["combo"]:
            msg += f" | 💥 {result['combo']}"

        return msg


def create_discord_embed(result: Dict) -> Optional[Dict]:
    """Create Discord embed for notable kills"""
    # Only post for notable events
    if not (result["ranked_up"] or result["combo"] or result["bonuses"] or
            result["rank_after"] >= StyleRank.S_STAKING):
        return None

    rank_cfg = RANK_CONFIG[result["rank_after"]]
    color = int(rank_cfg["color"], 16)

    # Build description
    desc_parts = []
    if result["combo"]:
        desc_parts.append(f"💥 **{result['combo']}**")
    if result["bonuses"]:
        desc_parts.append(" | ".join(result["bonuses"]))

    embed = {
        "title": f"⚡ {result['killer']} → {result['victim']}",
        "description": "\n".join(desc_parts) if desc_parts else None,
        "color": color,
        "fields": [
            {"name": "Style Rank", "value": rank_cfg["name"], "inline": True},
            {"name": "Multiplier", "value": f"{result['multiplier']}x", "inline": True},
            {"name": "RTC Earned", "value": f"+{result['total_rtc']:.4f}", "inline": True},
        ],
        "footer": {"text": "RustChain Arena | Style System"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if result["ranked_up"]:
        embed["title"] = f"🔥 RANK UP! {result['killer']} → {rank_cfg['name']}"

    return embed


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║     RUSTCHAIN ARENA - STYLE SYSTEM v1.0                           ║
╠═══════════════════════════════════════════════════════════════════╣
║  "Violence is the answer. More violence is more answer."          ║
║                                                                   ║
║  RANKS:  D (1.0x) → C (1.2x) → B (1.5x) → A (2.0x)               ║
║          S (3.0x) → SS (4.0x) → SSS SATOSHI (5.0x)               ║
║                                                                   ║
║  Kill fast. Kill varied. Never stop killing.                      ║
╚═══════════════════════════════════════════════════════════════════╝
""")

    style = StyleSystem()

    print(f"[Style] Monitoring: {XONOTIC_LOG}")
    print(f"[Style] Database: {DB_PATH}")
    print()

    # Kill detection patterns
    kill_patterns = [
        r':kill:\d+:\d+:\d+:([^:]+):([^:]+)',  # Xonotic eventlog
        r'(\S+) fragged (\S+)',                 # Standard frag
        r'(\S+) was killed by (\S+)',           # Alternative
    ]

    try:
        with open(XONOTIC_LOG, 'r') as f:
            f.seek(0, 2)  # End of file

            last_decay = time.time()

            while True:
                line = f.readline()

                # Periodic decay update
                if time.time() - last_decay > 1.0:
                    style.update()
                    last_decay = time.time()

                if not line:
                    time.sleep(0.05)
                    continue

                # Check for kills
                for pattern in kill_patterns:
                    match = re.search(pattern, line)
                    if match:
                        killer = match.group(1).strip()
                        victim = match.group(2).strip()

                        if killer and victim and killer != victim:
                            # Extract weapon if available
                            weapon = "unknown"
                            weapon_match = re.search(r':(\w+):', line)
                            if weapon_match:
                                weapon = weapon_match.group(1)

                            result = style.process_kill(killer, victim, weapon)
                            print(style.format_kill_message(result))

                            # Discord posting
                            if DISCORD_WEBHOOK:
                                embed = create_discord_embed(result)
                                if embed:
                                    try:
                                        import requests
                                        requests.post(DISCORD_WEBHOOK,
                                                    json={"embeds": [embed]},
                                                    timeout=2)
                                    except Exception:
                                        pass
                        break

                # Map change detection
                if "Map:" in line or "maps/" in line.lower():
                    style.reset_match()
                    print("\n  ═══════ NEW MATCH ═══════\n")

    except KeyboardInterrupt:
        print("\n\n[Style] Final Statistics:")
        for name, player in sorted(style.players.items(),
                                   key=lambda x: x[1].total_rtc, reverse=True):
            rank_name = RANK_CONFIG[player.rank]["name"]
            print(f"  {name}: {player.total_rtc:.4f} RTC | "
                  f"Best Streak: {player.best_streak} | "
                  f"Peak Rank: {rank_name}")
    except FileNotFoundError:
        print(f"[Error] Log not found: {XONOTIC_LOG}")
        print("[Error] Start Xonotic first!")


if __name__ == "__main__":
    main()
