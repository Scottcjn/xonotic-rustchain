#!/usr/bin/env python3
"""
RustChain Arena - Game Master v2.0
Integrates all systems: Style, Rewards, Announcer, Blood Economy, Discord, ML Bots
"""

import os
import re
import sys
import time
import json
import sqlite3
import threading
import requests
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from typing import Dict, Optional
from collections import deque

# Import our modules
from rustchain_style_system import StyleSystem, StyleRank, RANK_CONFIG, create_discord_embed
from rustchain_announcer import DynamicAnnouncer, format_announcement, SOPHIA_SPECIAL
from rustchain_blood_economy import BloodEconomy, DamageType, format_blood_event, BLOOD_ECONOMY_TIPS

getcontext().prec = 18

# Configuration
XONOTIC_LOG = os.path.expanduser("~/.xonotic/data/server.log")
DB_PATH = os.path.expanduser("~/Games/Xonotic/rustchain_rewards.db")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
RUSTCHAIN_API = os.environ.get("RUSTCHAIN_API", "https://50.28.86.131")


class GameMaster:
    """Master controller for RustChain Arena"""

    def __init__(self):
        # Core systems
        self.style = StyleSystem()
        self.announcer = DynamicAnnouncer("sophia")
        self.blood = BloodEconomy()

        # Match state
        self.match_active = False
        self.match_start_time = 0
        self.current_map = "unknown"

        # Player tracking
        self.active_players: Dict[str, dict] = {}
        self.spectators: set = set()

        # Event queue for async processing
        self.event_queue: deque = deque(maxlen=100)

        # Statistics
        self.total_kills = 0
        self.total_rtc_distributed = Decimal("0")

        # Discord rate limiting
        self.last_discord_post = 0
        self.discord_cooldown = 2.0

        print(self.get_banner())

    def get_banner(self) -> str:
        return """
\033[36m╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   ██████╗ ██╗   ██╗███████╗████████╗ ██████╗██╗  ██╗ █████╗ ██╗███╗   ██║
║   ██╔══██╗██║   ██║██╔════╝╚══██╔══╝██╔════╝██║  ██║██╔══██╗██║████╗  ██║
║   ██████╔╝██║   ██║███████╗   ██║   ██║     ███████║███████║██║██╔██╗ ██║
║   ██╔══██╗██║   ██║╚════██║   ██║   ██║     ██╔══██║██╔══██║██║██║╚██╗██║
║   ██║  ██║╚██████╔╝███████║   ██║   ╚██████╗██║  ██║██║  ██║██║██║ ╚████║
║   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
║                                                                       ║
║                    ★ GAME MASTER v2.0 ★                               ║
║                                                                       ║
║   Systems Online:                                                     ║
║   ✓ Style Rank System (D → SSS SATOSHI)                              ║
║   ✓ Blood Economy (Heal through Violence)                            ║
║   ✓ Dynamic Announcer (Sophia AI)                                     ║
║   ✓ RTC Rewards Engine                                                ║
║   ✓ Combo & Killstreak Tracking                                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝\033[0m
"""

    def post_discord(self, embed: dict, force: bool = False):
        """Post to Discord with rate limiting"""
        if not DISCORD_WEBHOOK:
            return

        now = time.time()
        if not force and now - self.last_discord_post < self.discord_cooldown:
            return

        try:
            requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=3)
            self.last_discord_post = now
        except Exception:
            pass

    def on_match_start(self, map_name: str):
        """Handle match start"""
        self.match_active = True
        self.match_start_time = time.time()
        self.current_map = map_name
        self.style.reset_match()
        self.blood.reset_match()

        print(f"\n\033[32m{'═' * 60}\033[0m")
        print(f"\033[32m  MATCH START: {map_name}\033[0m")
        print(f"\033[32m{'═' * 60}\033[0m\n")

        # Show Blood Economy tips
        import random
        tip = random.choice(BLOOD_ECONOMY_TIPS)
        print(f"  \033[95m{tip}\033[0m\n")

        # Announcer
        line = self.announcer.get_fallback_line("match_start") if not self.announcer.llm_available \
            else self.announcer.get_llm_line(f"Match starting on {map_name}")
        if line:
            print(format_announcement(line or "The arena awakens.", "important"))

        # Discord
        if DISCORD_WEBHOOK:
            embed = {
                "title": "🎮 Match Starting!",
                "description": f"**Map:** {map_name}\n**Mode:** RustChain Arena\n\nStyle ranks enabled. Earn RTC through aggression!",
                "color": 0x00FF00,
                "fields": [
                    {"name": "Ranks", "value": "D → C → B → A → S → SS → SSS", "inline": True},
                    {"name": "Multipliers", "value": "1x → 1.2x → 1.5x → 2x → 3x → 4x → 5x", "inline": True},
                ],
                "footer": {"text": "RustChain Arena | Play to Earn"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.post_discord(embed, force=True)

    def on_match_end(self):
        """Handle match end"""
        self.match_active = False
        duration = time.time() - self.match_start_time

        print(f"\n\033[33m{'═' * 60}\033[0m")
        print(f"\033[33m  MATCH COMPLETE\033[0m")
        print(f"\033[33m{'═' * 60}\033[0m")

        # Build leaderboard
        players = sorted(self.style.players.items(),
                        key=lambda x: x[1].total_rtc, reverse=True)

        print("\n  \033[36mLEADERBOARD:\033[0m")
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, player) in enumerate(players[:5]):
            medal = medals[i] if i < 3 else "  "
            rank_name = RANK_CONFIG[player.rank]["name"]
            print(f"  {medal} {name}: {player.total_rtc:.4f} RTC | "
                  f"K:{player.total_kills} D:{player.deaths} | "
                  f"Best: {player.best_streak} streak")

        print(f"\n  Total RTC Distributed: {self.total_rtc_distributed:.4f}")
        print(f"  Match Duration: {int(duration // 60)}m {int(duration % 60)}s")

        # Blood Economy stats
        blood_stats = self.blood.get_match_stats()
        print(f"\n  \033[96mBLOOD ECONOMY:\033[0m")
        print(f"    Shield Generated: {blood_stats['total_shield_generated']:.0f}")
        print(f"    Shield Decayed:   {blood_stats['total_shield_decayed']:.0f}")
        if blood_stats['most_aggressive_player']:
            print(f"    Most Aggressive:  {blood_stats['most_aggressive_player']} ({blood_stats['most_aggressive_shield']:.0f} shield earned)")
        print()

        # Announcer
        line = self.announcer.get_fallback_line("match_end") if not self.announcer.llm_available \
            else self.announcer.get_llm_line("Match ending, final results")
        if line:
            print(format_announcement(line or "The chain closes.", "important"))

        # Discord leaderboard
        if DISCORD_WEBHOOK and players:
            leaderboard = ""
            for i, (name, player) in enumerate(players[:3]):
                medal = medals[i] if i < 3 else ""
                leaderboard += f"{medal} **{name}**: {player.total_rtc:.4f} RTC\n"

            embed = {
                "title": "🏆 Match Complete!",
                "description": leaderboard,
                "color": 0xFFD700,
                "fields": [
                    {"name": "Total Kills", "value": str(self.total_kills), "inline": True},
                    {"name": "RTC Distributed", "value": f"{self.total_rtc_distributed:.4f}", "inline": True},
                    {"name": "Duration", "value": f"{int(duration // 60)}m {int(duration % 60)}s", "inline": True},
                ],
                "footer": {"text": "RustChain Arena"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.post_discord(embed, force=True)

    def on_kill(self, killer: str, victim: str, weapon: str = "unknown"):
        """Handle kill event"""
        result = self.style.process_kill(killer, victim, weapon)

        self.total_kills += 1
        self.total_rtc_distributed += result["total_rtc"]

        # Map weapon string to DamageType
        weapon_map = {
            "shotgun": DamageType.SHOTGUN,
            "uzi": DamageType.MACHINEGUN,
            "machinegun": DamageType.MACHINEGUN,
            "grenadelauncher": DamageType.GRENADE,
            "mortar": DamageType.MORTAR,
            "electro": DamageType.ELECTRO,
            "crylink": DamageType.CRYLINK,
            "vortex": DamageType.VORTEX,
            "nex": DamageType.VORTEX,
            "hagar": DamageType.HAGAR,
            "rocketlauncher": DamageType.ROCKET,
            "devastator": DamageType.DEVASTATOR,
            "melee": DamageType.MELEE,
            "blaster": DamageType.MACHINEGUN,
        }
        dmg_type = weapon_map.get(weapon.lower(), DamageType.MACHINEGUN)

        # Blood Economy - killer gains shield from kill
        blood_result = self.blood.on_kill(killer, victim, dmg_type)
        victim_death = self.blood.on_death(victim)

        # Console output
        self.print_kill(result, blood_result)

        # Announcements for notable events
        if result["ranked_up"]:
            if result["rank_after"] == StyleRank.SSS_SATOSHI:
                line = self.announcer.announce("sss_rank",
                    {"killer": killer, "rank": "SATOSHI"})
                if line:
                    print(format_announcement(line, "epic"))
            else:
                line = self.announcer.announce("rank_up",
                    {"killer": killer, "rank": RANK_CONFIG[result["rank_after"]]["name"]})
                if line:
                    print(format_announcement(line, "important"))

        if result["combo"]:
            combo_type = result["combo"].lower().replace(" ", "_")
            line = self.announcer.announce(combo_type, {"killer": killer})
            if line:
                style = "epic" if "GODLIKE" in result["combo"] else "important"
                print(format_announcement(line, style))

        if "FIRST BLOOD" in result.get("bonuses", []):
            line = self.announcer.announce("first_blood",
                {"killer": killer, "victim": victim})
            if line:
                print(format_announcement(line, "important"))

        if "REVENGE" in result.get("bonuses", []):
            line = self.announcer.announce("revenge",
                {"killer": killer, "victim": victim})
            if line:
                print(format_announcement(line))

        # Discord for notable kills
        embed = create_discord_embed(result)
        if embed:
            self.post_discord(embed)

    def print_kill(self, result: Dict, blood_result: Dict = None):
        """Print formatted kill info with Blood Economy"""
        rank_cfg = RANK_CONFIG[result["rank_after"]]
        rank_color = rank_cfg["color"]

        # ANSI color approximation
        colors = {
            "808080": "\033[90m",   # Gray
            "00FFFF": "\033[96m",   # Cyan
            "00FF00": "\033[92m",   # Green
            "FFFF00": "\033[93m",   # Yellow
            "FF8800": "\033[33m",   # Orange
            "FF0000": "\033[91m",   # Red
            "FFD700": "\033[93m",   # Gold
        }
        color = colors.get(rank_color, "\033[0m")
        reset = "\033[0m"

        # Build kill line
        line = f"  ⚡ {result['killer']} → {result['victim']}"

        if result["ranked_up"]:
            line += f" \033[93m⬆ RANK UP!\033[0m"

        line += f" {color}[{rank_cfg['name']}]{reset}"
        line += f" +{result['total_rtc']:.4f} RTC"
        line += f" ({result['multiplier']}x)"

        # Bonuses
        if result["bonuses"]:
            line += f" \033[95m| {' + '.join(result['bonuses'])}\033[0m"

        # Combo
        if result["combo"]:
            line += f" \033[91m★ {result['combo']}\033[0m"

        print(line)

        # Blood Economy shield info
        if blood_result and blood_result.get("shield_gained", 0) > 0:
            shield_line = f"    \033[96m💉 +{blood_result['shield_gained']:.0f} shield"
            shield_line += f" [{blood_result['shield_current']:.0f}/100]\033[0m"
            if blood_result.get("bonuses"):
                shield_line += f" \033[95m{' + '.join(blood_result['bonuses'])}\033[0m"
            print(shield_line)

    def on_player_connect(self, name: str):
        """Handle player connection"""
        self.active_players[name] = {"joined": time.time()}
        print(f"  \033[32m+ {name} connected\033[0m")

    def on_player_disconnect(self, name: str):
        """Handle player disconnection"""
        if name in self.active_players:
            del self.active_players[name]
        print(f"  \033[31m- {name} disconnected\033[0m")

    def run(self):
        """Main game loop"""
        print(f"\n[GameMaster] Monitoring: {XONOTIC_LOG}")
        print(f"[GameMaster] Discord: {'Connected' if DISCORD_WEBHOOK else 'Not configured'}")
        print(f"[GameMaster] Announcer: {'LLM' if self.announcer.llm_available else 'Fallback'}")
        print()

        # Pattern matching
        patterns = {
            "kill": [
                r':kill:\d+:\d+:\d+:([^:]+):([^:]+)',
                r'(\S+) fragged (\S+)',
            ],
            "map": r'maps/(\w+)',
            "connect": r'\^3\^7([^\^]+)\^4 connected',
            "disconnect": r'([^\^]+) disconnected',
            "end": r':end:|match over|Match ended',
        }

        try:
            with open(XONOTIC_LOG, 'r') as f:
                f.seek(0, 2)

                last_update = time.time()

                while True:
                    line = f.readline()

                    # Periodic update
                    now = time.time()
                    if now - last_update > 1.0:
                        self.style.update()
                        # Blood Economy decay
                        decayed = self.blood.update(1.0)
                        for player, amount in decayed.items():
                            if amount > 0.5:  # Only show significant decay
                                print(f"  \033[90m⏳ {player} shield decaying... -{amount:.1f}\033[0m")
                        last_update = now

                    if not line:
                        time.sleep(0.03)
                        continue

                    # Kill detection
                    for pattern in patterns["kill"]:
                        match = re.search(pattern, line)
                        if match:
                            killer = match.group(1).strip()
                            victim = match.group(2).strip()
                            if killer and victim and killer != victim:
                                weapon = "unknown"
                                weapon_match = re.search(r':(\w+):', line)
                                if weapon_match:
                                    weapon = weapon_match.group(1)
                                self.on_kill(killer, victim, weapon)
                            break

                    # Map change
                    if "Map:" in line or "SpawnServer:" in line:
                        match = re.search(patterns["map"], line)
                        if match:
                            self.on_match_start(match.group(1))

                    # Match end
                    if re.search(patterns["end"], line, re.IGNORECASE):
                        self.on_match_end()

                    # Player connect
                    match = re.search(patterns["connect"], line)
                    if match:
                        self.on_player_connect(match.group(1).strip())

                    # Player disconnect
                    if "disconnected" in line.lower() or "dropped" in line.lower():
                        match = re.search(r'"([^"]+)" (?:disconnected|dropped)', line)
                        if match:
                            self.on_player_disconnect(match.group(1))

        except KeyboardInterrupt:
            print("\n\n\033[33m[GameMaster] Shutting down...\033[0m")
            self.on_match_end()
        except FileNotFoundError:
            print(f"\033[91m[Error] Log not found: {XONOTIC_LOG}\033[0m")
            print("[Error] Start Xonotic first!")
            sys.exit(1)


def main():
    master = GameMaster()
    master.run()


if __name__ == "__main__":
    main()
