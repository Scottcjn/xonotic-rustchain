#!/usr/bin/env python3
"""
RustChain Arena - Blood Economy System
ULTRAKILL-inspired healing through violence.

Shields regenerate ONLY through dealing damage.
Camping and passive play causes shield decay.
"""

import os
import time
from enum import IntEnum
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque

# Configuration
SHIELD_MAX = 100
SHIELD_DECAY_RATE = 2.0      # Per second when idle
SHIELD_DECAY_DELAY = 5.0     # Seconds before decay starts
DAMAGE_TO_SHIELD_RATIO = 0.15  # 15% of damage dealt → shield
CLOSE_RANGE_MULTIPLIER = 3.0   # 3x shield gain at close range
MELEE_KILL_SHIELD = 50         # Instant shield for melee kills
HEADSHOT_BONUS = 25            # Bonus shield for headshots
KILL_SHIELD_BONUS = 20         # Base shield for any kill

# Distance thresholds (Quake units)
CLOSE_RANGE = 300              # Very close combat
MID_RANGE = 800                # Standard engagement
LONG_RANGE = 1500              # Sniping distance


class DamageType(IntEnum):
    """Damage types affect shield regeneration"""
    MELEE = 0          # Gauntlet, kick - maximum reward
    SHOTGUN = 1        # Close range weapon
    MACHINEGUN = 2     # Mid range
    ROCKET = 3         # Splash damage
    GRENADE = 4        # Indirect fire
    ELECTRO = 5        # Combo potential
    CRYLINK = 6        # Bouncing projectiles
    VORTEX = 7         # Hitscan sniper
    HAGAR = 8          # Rapid projectiles
    DEVASTATOR = 9     # Heavy rockets
    MORTAR = 10        # Arc grenades


# Weapon close-range effectiveness multipliers
WEAPON_RANGE_BONUS = {
    DamageType.MELEE: 4.0,      # Maximum reward for melee
    DamageType.SHOTGUN: 2.5,    # Shotgun rewards close play
    DamageType.MACHINEGUN: 1.0,
    DamageType.ROCKET: 1.5,     # Rocket jumping close combat
    DamageType.GRENADE: 1.2,
    DamageType.ELECTRO: 1.3,
    DamageType.CRYLINK: 1.0,
    DamageType.VORTEX: 0.5,     # Sniping gives less shield
    DamageType.HAGAR: 1.1,
    DamageType.DEVASTATOR: 1.4,
    DamageType.MORTAR: 1.1,
}


@dataclass
class BloodState:
    """Per-player blood economy state"""
    shield: float = 0.0
    last_damage_dealt: float = 0.0
    last_damage_taken: float = 0.0
    last_action_time: float = field(default_factory=time.time)
    damage_dealt_total: float = 0.0
    shield_gained_total: float = 0.0
    decay_total: float = 0.0

    # Combat tracking
    recent_hits: deque = field(default_factory=lambda: deque(maxlen=10))
    in_combat: bool = False
    combat_start: float = 0.0

    # Streak tracking
    kills_without_damage: int = 0  # "Untouchable" bonus

    def is_decaying(self, now: float) -> bool:
        """Check if shields should be decaying"""
        return (now - self.last_action_time) > SHIELD_DECAY_DELAY


class BloodEconomy:
    """
    Blood Economy Manager

    "Your health is a resource, not a right.
     Violence is your medicine."
    """

    def __init__(self):
        self.players: Dict[str, BloodState] = {}
        self.last_update = time.time()

        # Match statistics
        self.total_shield_generated = 0.0
        self.total_shield_decayed = 0.0
        self.most_aggressive: Optional[str] = None
        self.most_aggressive_shield = 0.0

    def get_player(self, name: str) -> BloodState:
        """Get or create player blood state"""
        if name not in self.players:
            self.players[name] = BloodState()
        return self.players[name]

    def on_damage_dealt(self, attacker: str, victim: str, damage: float,
                        weapon: DamageType = DamageType.MACHINEGUN,
                        distance: float = MID_RANGE,
                        headshot: bool = False) -> Dict:
        """
        Process damage dealt - the core of blood economy.
        Returns shield gained and any bonuses.
        """
        state = self.get_player(attacker)
        now = time.time()

        # Base shield from damage
        base_shield = damage * DAMAGE_TO_SHIELD_RATIO

        # Distance multiplier - closer = more reward
        if distance <= CLOSE_RANGE:
            distance_mult = CLOSE_RANGE_MULTIPLIER
        elif distance <= MID_RANGE:
            # Linear interpolation
            t = (distance - CLOSE_RANGE) / (MID_RANGE - CLOSE_RANGE)
            distance_mult = CLOSE_RANGE_MULTIPLIER - (CLOSE_RANGE_MULTIPLIER - 1.0) * t
        else:
            # Long range penalty
            t = min(1.0, (distance - MID_RANGE) / (LONG_RANGE - MID_RANGE))
            distance_mult = 1.0 - (0.5 * t)  # Down to 0.5x at max range

        # Weapon bonus
        weapon_mult = WEAPON_RANGE_BONUS.get(weapon, 1.0)

        # Calculate total shield gain
        shield_gain = base_shield * distance_mult * weapon_mult

        # Headshot bonus
        if headshot:
            shield_gain += HEADSHOT_BONUS

        # Apply shield (capped at max)
        old_shield = state.shield
        state.shield = min(SHIELD_MAX, state.shield + shield_gain)
        actual_gain = state.shield - old_shield

        # Update tracking
        state.last_damage_dealt = damage
        state.last_action_time = now
        state.damage_dealt_total += damage
        state.shield_gained_total += actual_gain
        state.in_combat = True
        state.combat_start = now

        # Track hit for combo detection
        state.recent_hits.append({
            "time": now,
            "damage": damage,
            "weapon": weapon,
            "distance": distance
        })

        # Update match stats
        self.total_shield_generated += actual_gain
        if state.shield_gained_total > self.most_aggressive_shield:
            self.most_aggressive = attacker
            self.most_aggressive_shield = state.shield_gained_total

        return {
            "attacker": attacker,
            "shield_gained": actual_gain,
            "shield_current": state.shield,
            "distance_mult": distance_mult,
            "weapon_mult": weapon_mult,
            "headshot": headshot,
            "bonuses": self._get_bonuses(state, weapon, distance, headshot)
        }

    def on_kill(self, killer: str, victim: str,
                weapon: DamageType = DamageType.MACHINEGUN,
                distance: float = MID_RANGE) -> Dict:
        """
        Process kill - bonus shield rewards.
        """
        state = self.get_player(killer)
        now = time.time()

        bonuses = []
        shield_gain = KILL_SHIELD_BONUS

        # Melee kill = massive bonus
        if weapon == DamageType.MELEE:
            shield_gain += MELEE_KILL_SHIELD
            bonuses.append("EXECUTION")

        # Close range kill bonus
        if distance <= CLOSE_RANGE:
            shield_gain += 15
            bonuses.append("POINT BLANK")

        # Untouchable streak bonus
        if state.kills_without_damage >= 3:
            shield_gain += 10 * state.kills_without_damage
            bonuses.append(f"UNTOUCHABLE x{state.kills_without_damage}")

        state.kills_without_damage += 1

        # Apply shield
        old_shield = state.shield
        state.shield = min(SHIELD_MAX, state.shield + shield_gain)
        actual_gain = state.shield - old_shield

        state.last_action_time = now
        state.shield_gained_total += actual_gain
        self.total_shield_generated += actual_gain

        return {
            "killer": killer,
            "victim": victim,
            "shield_gained": actual_gain,
            "shield_current": state.shield,
            "bonuses": bonuses,
            "total_bonus": shield_gain
        }

    def on_damage_taken(self, player: str, damage: float,
                        attacker: str = "") -> Dict:
        """
        Process damage taken - resets untouchable streak.
        """
        state = self.get_player(player)
        state.last_damage_taken = damage
        state.kills_without_damage = 0  # Reset untouchable

        return {
            "player": player,
            "damage": damage,
            "shield_current": state.shield,
            "untouchable_lost": True if state.kills_without_damage > 0 else False
        }

    def on_death(self, player: str) -> Dict:
        """
        Process death - shield mechanics on respawn.
        """
        state = self.get_player(player)

        # Death resets shield to 0
        lost_shield = state.shield
        state.shield = 0
        state.kills_without_damage = 0
        state.in_combat = False
        state.recent_hits.clear()

        return {
            "player": player,
            "shield_lost": lost_shield,
            "message": "Shield depleted. Violence is your medicine."
        }

    def update(self, dt: float = None) -> Dict[str, float]:
        """
        Update all players - apply shield decay.
        Returns dict of players who decayed and amounts.
        """
        now = time.time()
        if dt is None:
            dt = now - self.last_update
        self.last_update = now

        decayed = {}

        for name, state in self.players.items():
            if state.shield > 0 and state.is_decaying(now):
                decay = SHIELD_DECAY_RATE * dt
                old_shield = state.shield
                state.shield = max(0, state.shield - decay)
                actual_decay = old_shield - state.shield

                if actual_decay > 0:
                    state.decay_total += actual_decay
                    self.total_shield_decayed += actual_decay
                    decayed[name] = actual_decay

            # Check if combat ended
            if state.in_combat and (now - state.last_action_time) > 3.0:
                state.in_combat = False

        return decayed

    def _get_bonuses(self, state: BloodState, weapon: DamageType,
                     distance: float, headshot: bool) -> list:
        """Get list of active bonuses"""
        bonuses = []

        if weapon == DamageType.MELEE:
            bonuses.append("BLOOD RAGE")
        elif weapon == DamageType.SHOTGUN and distance <= CLOSE_RANGE:
            bonuses.append("BUCKSHOT BAPTISM")

        if headshot:
            bonuses.append("PRECISION")

        if distance <= CLOSE_RANGE:
            bonuses.append("INTIMATE")
        elif distance >= LONG_RANGE:
            bonuses.append("SNIPER (reduced)")

        # Rapid hits
        now = time.time()
        recent = [h for h in state.recent_hits if now - h["time"] < 2.0]
        if len(recent) >= 3:
            bonuses.append(f"RAPID FIRE x{len(recent)}")

        return bonuses

    def get_status(self, player: str) -> Dict:
        """Get player's blood economy status"""
        state = self.get_player(player)
        now = time.time()

        return {
            "player": player,
            "shield": state.shield,
            "shield_max": SHIELD_MAX,
            "shield_percent": (state.shield / SHIELD_MAX) * 100,
            "is_decaying": state.is_decaying(now),
            "seconds_until_decay": max(0, SHIELD_DECAY_DELAY - (now - state.last_action_time)),
            "total_gained": state.shield_gained_total,
            "total_decayed": state.decay_total,
            "in_combat": state.in_combat,
            "untouchable_streak": state.kills_without_damage
        }

    def get_match_stats(self) -> Dict:
        """Get match-wide blood economy statistics"""
        return {
            "total_shield_generated": self.total_shield_generated,
            "total_shield_decayed": self.total_shield_decayed,
            "net_shield": self.total_shield_generated - self.total_shield_decayed,
            "most_aggressive_player": self.most_aggressive,
            "most_aggressive_shield": self.most_aggressive_shield,
            "active_players": len(self.players)
        }

    def format_shield_bar(self, player: str, width: int = 20) -> str:
        """Format shield as ASCII progress bar"""
        state = self.get_player(player)
        filled = int((state.shield / SHIELD_MAX) * width)
        empty = width - filled

        # Color based on shield level
        if state.shield >= 75:
            color = "\033[92m"  # Green
        elif state.shield >= 40:
            color = "\033[93m"  # Yellow
        elif state.shield > 0:
            color = "\033[91m"  # Red
        else:
            color = "\033[90m"  # Gray

        reset = "\033[0m"
        bar = "█" * filled + "░" * empty

        return f"{color}[{bar}]{reset} {state.shield:.0f}/{SHIELD_MAX}"

    def reset_match(self):
        """Reset for new match"""
        self.players.clear()
        self.total_shield_generated = 0.0
        self.total_shield_decayed = 0.0
        self.most_aggressive = None
        self.most_aggressive_shield = 0.0


# Console display helpers
def format_blood_event(event: Dict, event_type: str) -> str:
    """Format blood economy event for console"""
    if event_type == "damage":
        bonuses = " + ".join(event.get("bonuses", []))
        bonus_str = f" | {bonuses}" if bonuses else ""
        return (f"  ⚡ {event['attacker']} +{event['shield_gained']:.1f} shield "
                f"({event['distance_mult']:.1f}x dist, {event['weapon_mult']:.1f}x wpn){bonus_str}")

    elif event_type == "kill":
        bonuses = " + ".join(event.get("bonuses", []))
        bonus_str = f" | {bonuses}" if bonuses else ""
        return (f"  💀 {event['killer']} → {event['victim']} "
                f"+{event['shield_gained']:.1f} shield{bonus_str}")

    elif event_type == "death":
        return f"  ☠ {event['player']} lost {event['shield_lost']:.1f} shield"

    elif event_type == "decay":
        return f"  ⏳ {event} shield decaying..."

    return str(event)


# MOTD / Tutorial text
BLOOD_ECONOMY_TIPS = [
    "💉 BLOOD ECONOMY: Shields regenerate ONLY through violence",
    "🔪 Close range combat = 3x shield gain",
    "⚔️ Melee kills grant +50 instant shield",
    "⏳ Hiding? Your shields DECAY after 5 seconds",
    "🎯 Headshots grant +25 bonus shield",
    "👊 Stay aggressive or watch your protection fade",
]


# Test/demo
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  BLOOD ECONOMY SYSTEM TEST")
    print("="*60 + "\n")

    economy = BloodEconomy()

    # Simulate combat
    print("Scenario: Boris vs Player1\n")

    # Boris deals damage at close range with shotgun
    result = economy.on_damage_dealt(
        "Boris_Volkov", "Player1",
        damage=45,
        weapon=DamageType.SHOTGUN,
        distance=250
    )
    print(format_blood_event(result, "damage"))
    print(f"    {economy.format_shield_bar('Boris_Volkov')}")

    # Boris gets a kill
    result = economy.on_kill(
        "Boris_Volkov", "Player1",
        weapon=DamageType.SHOTGUN,
        distance=250
    )
    print(format_blood_event(result, "kill"))
    print(f"    {economy.format_shield_bar('Boris_Volkov')}")

    # Simulate idle time
    print("\n--- 6 seconds pass (idle) ---\n")
    economy.players["Boris_Volkov"].last_action_time -= 6

    decayed = economy.update(dt=1.0)
    for player, amount in decayed.items():
        print(f"  ⏳ {player} shield decaying... -{amount:.1f}")
    print(f"    {economy.format_shield_bar('Boris_Volkov')}")

    # Long range sniper shot
    print("\n--- Sophia snipes from distance ---\n")
    result = economy.on_damage_dealt(
        "Sophia_Elya", "Player2",
        damage=100,
        weapon=DamageType.VORTEX,
        distance=1800,
        headshot=True
    )
    print(format_blood_event(result, "damage"))
    print(f"    {economy.format_shield_bar('Sophia_Elya')}")
    print("    Note: Long range + sniper = reduced shield gain")

    # Melee execution
    print("\n--- Boris melee execution ---\n")
    result = economy.on_damage_dealt(
        "Boris_Volkov", "Player3",
        damage=80,
        weapon=DamageType.MELEE,
        distance=50
    )
    print(format_blood_event(result, "damage"))

    result = economy.on_kill(
        "Boris_Volkov", "Player3",
        weapon=DamageType.MELEE,
        distance=50
    )
    print(format_blood_event(result, "kill"))
    print(f"    {economy.format_shield_bar('Boris_Volkov')}")

    # Match stats
    print("\n" + "="*60)
    print("  MATCH STATISTICS")
    print("="*60)
    stats = economy.get_match_stats()
    print(f"  Total Shield Generated: {stats['total_shield_generated']:.1f}")
    print(f"  Total Shield Decayed:   {stats['total_shield_decayed']:.1f}")
    print(f"  Most Aggressive:        {stats['most_aggressive_player']}")
    print()
