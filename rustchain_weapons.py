#!/usr/bin/env python3
"""
RustChain Arena - Blockchain-Themed Weapons
Unique weapons with cryptocurrency-inspired mechanics.

These weapon configurations map to Xonotic's weapon system
with special tracking and RTC bonus calculations.
"""

import os
import time
import random
from enum import IntEnum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from decimal import Decimal

# Base RTC rewards per weapon type (modified by style rank)
WEAPON_RTC_BASE = {
    "validator": Decimal("0.0015"),
    "forker": Decimal("0.0012"),
    "hashcannon": Decimal("0.0025"),
    "mempool_grenade": Decimal("0.002"),
    "double_spend": Decimal("0.0018"),
}


class WeaponID(IntEnum):
    """Weapon identifiers matching Xonotic slots"""
    BLASTER = 0
    SHOTGUN = 1       # → The Forker
    MACHINEGUN = 2
    MORTAR = 3        # → Mempool Grenade
    ELECTRO = 4       # → The Validator
    CRYLINK = 5
    VORTEX = 6        # → Double-Spend Rifle
    HAGAR = 7
    DEVASTATOR = 8    # → Hashcannon
    MINELAYER = 9
    HLAC = 10
    RIFLE = 11
    SEEKER = 12


@dataclass
class WeaponState:
    """Per-player weapon state tracking"""
    # The Forker
    fork_pellets_hit: int = 0
    fork_targets_hit: set = field(default_factory=set)

    # Hashcannon
    hashcannon_charge_start: float = 0.0
    hashcannon_charging: bool = False
    hashcannon_charge_lost_rtc: Decimal = Decimal("0")

    # Mempool Grenade
    active_grenades: List[dict] = field(default_factory=list)

    # Double-Spend Rifle
    last_doublespend_kill: float = 0.0
    doublespend_available: bool = False

    # The Validator
    validator_node_position: Optional[Tuple[float, float, float]] = None
    validator_node_time: float = 0.0
    validator_scans_used: int = 0


class BlockchainWeapons:
    """
    Blockchain-Themed Weapon System

    Weapons are reskinned/modified versions of Xonotic weapons
    with special mechanics tracked via the Python bridge.
    """

    def __init__(self):
        self.players: Dict[str, WeaponState] = {}

        # Weapon configurations
        self.weapons = {
            # ═══════════════════════════════════════════════════════════════
            # THE FORKER (Shotgun replacement)
            # ═══════════════════════════════════════════════════════════════
            "forker": {
                "name": "The Forker",
                "base_weapon": "shotgun",
                "slot": WeaponID.SHOTGUN,
                "description": "Shotgun that rewards multi-target hits",
                "primary": {
                    "damage": 4,  # Per pellet
                    "pellets": 14,
                    "spread": 700,  # Cone spread
                    "refire": 0.8,
                },
                "secondary": {
                    "name": "Fork Bomb",
                    "damage": 30,
                    "splash_radius": 120,
                    "fragments": 5,
                    "fragment_damage": 15,
                    "refire": 1.5,
                    "ammo_cost": 3,
                },
                "bonuses": {
                    "clean_merge": {  # All pellets hit one target
                        "threshold": 12,  # pellets
                        "rtc_bonus": Decimal("0.0005"),
                        "message": "CLEAN MERGE",
                    },
                    "hard_fork": {  # Hit multiple targets with one shot
                        "min_targets": 2,
                        "rtc_bonus": Decimal("0.001"),
                        "message": "HARD FORK",
                    },
                },
                "announcer_lines": [
                    "Fork successful.",
                    "Branch divergence complete.",
                    "The spread finds consensus.",
                ],
            },

            # ═══════════════════════════════════════════════════════════════
            # THE VALIDATOR (Electro replacement)
            # ═══════════════════════════════════════════════════════════════
            "validator": {
                "name": "The Validator",
                "base_weapon": "electro",
                "slot": WeaponID.ELECTRO,
                "description": "Utility tool with teleport node and enemy scan",
                "primary": {
                    "name": "Validation Node",
                    "type": "deployable",
                    "duration": 30.0,  # Seconds node lasts
                    "health": 100,  # Node can be destroyed
                    "teleport_cooldown": 3.0,
                    "ammo_cost": 15,
                },
                "secondary": {
                    "name": "Scan Pulse",
                    "type": "reveal",
                    "range": 2000,  # Quake units
                    "duration": 5.0,  # Tag duration
                    "ammo_cost": 5,
                    "rtc_cost": Decimal("0.001"),  # Costs RTC to use
                },
                "bonuses": {
                    "node_teleport_kill": {
                        "window": 3.0,  # Seconds after teleport
                        "rtc_bonus": Decimal("0.002"),
                        "message": "VALIDATOR STRIKE",
                    },
                    "scan_assist": {
                        "rtc_bonus": Decimal("0.0005"),
                        "message": "SCAN ASSIST",
                    },
                },
                "mechanics": {
                    "node_destroyed_damage": 50,  # Damage to owner if node killed
                    "node_visible_to_all": True,
                },
                "announcer_lines": [
                    "Validation node deployed.",
                    "Checkpoint confirmed.",
                    "Position staked.",
                ],
            },

            # ═══════════════════════════════════════════════════════════════
            # THE HASHCANNON (Devastator replacement)
            # ═══════════════════════════════════════════════════════════════
            "hashcannon": {
                "name": "The Hashcannon",
                "base_weapon": "devastator",
                "slot": WeaponID.DEVASTATOR,
                "description": "Charge weapon - longer charge = more damage",
                "primary": {
                    "type": "charge",
                    "min_damage": 40,
                    "max_damage": 200,  # Instakill at full charge
                    "charge_time": 3.0,  # Seconds to full charge
                    "projectile_speed": 1200,
                    "splash_radius": 80,
                },
                "mechanics": {
                    "charge_visible": True,  # Enemies can see you charging
                    "charge_sound": True,  # Audio cue
                    "death_while_charging_penalty": Decimal("0.01"),  # Lose RTC
                    "full_charge_glow": True,  # Visual effect at max
                },
                "bonuses": {
                    "golden_hash": {  # Full charge instakill
                        "rtc_bonus": Decimal("0.005"),
                        "message": "GOLDEN HASH FOUND",
                    },
                    "quick_mine": {  # Kill with <50% charge
                        "rtc_bonus": Decimal("0.001"),
                        "message": "EFFICIENT MINING",
                    },
                },
                "visuals": {
                    "charging": "Numbers scrolling, seeking hash",
                    "fired": "Block of data projectile",
                    "impact": "BLOCK FOUND text",
                },
                "announcer_lines": [
                    "Hash computation initiated.",
                    "Mining in progress.",
                    "Block found. Transaction confirmed.",
                ],
            },

            # ═══════════════════════════════════════════════════════════════
            # MEMPOOL GRENADE (Mortar replacement)
            # ═══════════════════════════════════════════════════════════════
            "mempool_grenade": {
                "name": "Mempool Grenade",
                "base_weapon": "mortar",
                "slot": WeaponID.MORTAR,
                "description": "Delayed explosion - can be 'confirmed' by shooting it",
                "primary": {
                    "type": "delayed_explosive",
                    "base_damage": 80,
                    "max_damage": 150,  # If left in mempool
                    "mempool_time": 3.0,  # Base delay
                    "splash_radius": 150,
                    "ammo_cost": 1,
                    "rtc_cost": Decimal("0.002"),  # Costs RTC to throw
                },
                "mechanics": {
                    "shootable": True,  # Anyone can shoot to detonate
                    "enemy_shoot_fizzle": True,  # Enemy shot = reduced damage
                    "friendly_shoot_confirm": True,  # Ally shot = instant full damage
                    "mempool_growth": 20,  # +damage per second in mempool
                },
                "bonuses": {
                    "enemy_confirms": {  # Enemy shoots your grenade
                        "rtc_bonus": Decimal("0.003"),
                        "message": "ENEMY CONFIRMED YOUR TX",
                    },
                    "max_mempool": {  # Kill after full 3s delay
                        "rtc_bonus": Decimal("0.002"),
                        "message": "MAXIMUM GAS FEE",
                    },
                    "instant_confirm": {  # Shoot your own grenade
                        "rtc_bonus": Decimal("0.001"),
                        "message": "SELF-CONFIRMED",
                    },
                },
                "announcer_lines": [
                    "Transaction pending.",
                    "Mempool entry created.",
                    "Awaiting confirmation.",
                ],
            },

            # ═══════════════════════════════════════════════════════════════
            # DOUBLE-SPEND RIFLE (Vortex replacement)
            # ═══════════════════════════════════════════════════════════════
            "double_spend": {
                "name": "Double-Spend Rifle",
                "base_weapon": "vortex",
                "slot": WeaponID.VORTEX,
                "description": "Hitscan sniper - free second shot after kill",
                "primary": {
                    "type": "hitscan",
                    "damage": 80,
                    "charge_damage_bonus": 50,  # At full charge
                    "charge_time": 1.5,
                    "refire": 1.5,
                    "ammo_cost": 6,
                },
                "mechanics": {
                    "double_spend_window": 2.0,  # Seconds to fire free shot
                    "double_spend_ammo_refund": True,
                    "double_spend_requires_kill": True,
                },
                "bonuses": {
                    "double_spend": {  # Use free second shot for kill
                        "rtc_bonus": Decimal("0.004"),
                        "message": "DOUBLE SPEND ATTACK",
                    },
                    "chain_spend": {  # Multiple double-spends in a row
                        "per_chain": Decimal("0.002"),
                        "message": "CHAIN SPEND x{n}",
                    },
                },
                "announcer_lines": [
                    "Transaction cloned.",
                    "Double spend initiated.",
                    "Same coin, twice spent.",
                ],
            },
        }

    def get_player(self, name: str) -> WeaponState:
        """Get or create player weapon state"""
        if name not in self.players:
            self.players[name] = WeaponState()
        return self.players[name]

    # ═══════════════════════════════════════════════════════════════════════
    # THE FORKER MECHANICS
    # ═══════════════════════════════════════════════════════════════════════

    def forker_shot(self, shooter: str, pellets_hit: int,
                    targets: List[str]) -> Dict:
        """Track a Forker shot and calculate bonuses"""
        state = self.get_player(shooter)
        result = {
            "weapon": "forker",
            "pellets_hit": pellets_hit,
            "targets": targets,
            "bonuses": [],
            "rtc_bonus": Decimal("0"),
        }

        config = self.weapons["forker"]["bonuses"]

        # Check for clean merge (all pellets hit one target)
        if len(targets) == 1 and pellets_hit >= config["clean_merge"]["threshold"]:
            result["bonuses"].append(config["clean_merge"]["message"])
            result["rtc_bonus"] += config["clean_merge"]["rtc_bonus"]

        # Check for hard fork (multiple targets)
        if len(set(targets)) >= config["hard_fork"]["min_targets"]:
            result["bonuses"].append(config["hard_fork"]["message"])
            result["rtc_bonus"] += config["hard_fork"]["rtc_bonus"]

        return result

    def forker_fork_bomb(self, shooter: str, direct_hit: str,
                         fragment_hits: List[str]) -> Dict:
        """Track Fork Bomb secondary fire"""
        result = {
            "weapon": "forker",
            "mode": "fork_bomb",
            "direct_hit": direct_hit,
            "fragment_hits": fragment_hits,
            "total_targets": len(set([direct_hit] + fragment_hits)) if direct_hit else len(set(fragment_hits)),
            "rtc_bonus": Decimal("0"),
        }

        # Bonus for multiple fragment hits
        unique_hits = len(set(fragment_hits))
        if unique_hits >= 3:
            result["rtc_bonus"] = Decimal("0.002")
            result["bonuses"] = ["FORK PROPAGATION"]

        return result

    # ═══════════════════════════════════════════════════════════════════════
    # THE VALIDATOR MECHANICS
    # ═══════════════════════════════════════════════════════════════════════

    def validator_deploy_node(self, player: str,
                               position: Tuple[float, float, float]) -> Dict:
        """Deploy a Validator node"""
        state = self.get_player(player)

        # Remove old node if exists
        old_node = state.validator_node_position

        state.validator_node_position = position
        state.validator_node_time = time.time()

        return {
            "weapon": "validator",
            "action": "deploy",
            "position": position,
            "replaced_old": old_node is not None,
            "message": "Validation node deployed.",
        }

    def validator_teleport(self, player: str) -> Dict:
        """Teleport to Validator node"""
        state = self.get_player(player)

        if not state.validator_node_position:
            return {"success": False, "error": "No node deployed"}

        node_age = time.time() - state.validator_node_time
        if node_age > 30.0:
            return {"success": False, "error": "Node expired"}

        return {
            "success": True,
            "weapon": "validator",
            "action": "teleport",
            "destination": state.validator_node_position,
            "node_age": node_age,
        }

    def validator_node_destroyed(self, owner: str, destroyer: str) -> Dict:
        """Handle node destruction"""
        state = self.get_player(owner)
        state.validator_node_position = None

        return {
            "weapon": "validator",
            "action": "node_destroyed",
            "owner": owner,
            "destroyer": destroyer,
            "damage_to_owner": 50,
            "message": f"{owner}'s validation node slashed by {destroyer}",
        }

    def validator_scan(self, player: str, enemies_revealed: List[str]) -> Dict:
        """Use scan pulse"""
        state = self.get_player(player)
        state.validator_scans_used += 1

        return {
            "weapon": "validator",
            "action": "scan",
            "enemies_revealed": enemies_revealed,
            "rtc_cost": Decimal("0.001"),
            "message": f"Scan reveals {len(enemies_revealed)} hostiles",
        }

    # ═══════════════════════════════════════════════════════════════════════
    # HASHCANNON MECHANICS
    # ═══════════════════════════════════════════════════════════════════════

    def hashcannon_start_charge(self, player: str) -> Dict:
        """Start charging the Hashcannon"""
        state = self.get_player(player)
        state.hashcannon_charging = True
        state.hashcannon_charge_start = time.time()

        return {
            "weapon": "hashcannon",
            "action": "charge_start",
            "message": "Mining initiated...",
        }

    def hashcannon_fire(self, player: str) -> Dict:
        """Fire the Hashcannon"""
        state = self.get_player(player)

        if not state.hashcannon_charging:
            return {"success": False, "error": "Not charging"}

        charge_time = time.time() - state.hashcannon_charge_start
        charge_percent = min(1.0, charge_time / 3.0)

        state.hashcannon_charging = False

        # Calculate damage
        config = self.weapons["hashcannon"]["primary"]
        damage = config["min_damage"] + (
            (config["max_damage"] - config["min_damage"]) * charge_percent
        )

        return {
            "weapon": "hashcannon",
            "action": "fire",
            "charge_percent": charge_percent,
            "damage": damage,
            "is_golden_hash": charge_percent >= 0.95,
            "message": "BLOCK FOUND" if charge_percent >= 0.95 else "Hash computed",
        }

    def hashcannon_death_while_charging(self, player: str) -> Dict:
        """Player died while charging - lose RTC"""
        state = self.get_player(player)

        if state.hashcannon_charging:
            state.hashcannon_charging = False
            penalty = self.weapons["hashcannon"]["mechanics"]["death_while_charging_penalty"]
            state.hashcannon_charge_lost_rtc += penalty

            return {
                "weapon": "hashcannon",
                "action": "charge_interrupted",
                "rtc_penalty": penalty,
                "message": "Wasted compute. Hash lost.",
            }

        return {"weapon": "hashcannon", "action": "none"}

    def hashcannon_kill(self, killer: str, charge_percent: float) -> Dict:
        """Process Hashcannon kill bonus"""
        config = self.weapons["hashcannon"]["bonuses"]
        result = {
            "weapon": "hashcannon",
            "action": "kill",
            "charge_percent": charge_percent,
            "bonuses": [],
            "rtc_bonus": Decimal("0"),
        }

        if charge_percent >= 0.95:
            result["bonuses"].append(config["golden_hash"]["message"])
            result["rtc_bonus"] += config["golden_hash"]["rtc_bonus"]
        elif charge_percent < 0.5:
            result["bonuses"].append(config["quick_mine"]["message"])
            result["rtc_bonus"] += config["quick_mine"]["rtc_bonus"]

        return result

    # ═══════════════════════════════════════════════════════════════════════
    # MEMPOOL GRENADE MECHANICS
    # ═══════════════════════════════════════════════════════════════════════

    def mempool_throw(self, player: str, grenade_id: str,
                      position: Tuple[float, float, float]) -> Dict:
        """Throw a Mempool Grenade"""
        state = self.get_player(player)

        grenade = {
            "id": grenade_id,
            "owner": player,
            "position": position,
            "thrown_at": time.time(),
            "base_damage": 80,
        }
        state.active_grenades.append(grenade)

        return {
            "weapon": "mempool_grenade",
            "action": "throw",
            "grenade_id": grenade_id,
            "rtc_cost": Decimal("0.002"),
            "message": "Transaction pending...",
        }

    def mempool_confirm(self, grenade_id: str, confirmer: str,
                        owner: str) -> Dict:
        """Grenade is shot/confirmed"""
        state = self.get_player(owner)

        # Find the grenade
        grenade = None
        for g in state.active_grenades:
            if g["id"] == grenade_id:
                grenade = g
                break

        if not grenade:
            return {"success": False, "error": "Grenade not found"}

        time_in_mempool = time.time() - grenade["thrown_at"]
        config = self.weapons["mempool_grenade"]

        # Calculate damage based on time in mempool
        growth = config["mechanics"]["mempool_growth"]
        damage = min(
            config["primary"]["max_damage"],
            config["primary"]["base_damage"] + (time_in_mempool * growth)
        )

        result = {
            "weapon": "mempool_grenade",
            "action": "confirm",
            "grenade_id": grenade_id,
            "owner": owner,
            "confirmer": confirmer,
            "time_in_mempool": time_in_mempool,
            "damage": damage,
            "bonuses": [],
            "rtc_bonus": Decimal("0"),
        }

        # Check bonuses
        if confirmer != owner:
            # Enemy confirmed
            result["bonuses"].append(config["bonuses"]["enemy_confirms"]["message"])
            result["rtc_bonus"] += config["bonuses"]["enemy_confirms"]["rtc_bonus"]
            result["damage"] *= 0.5  # Enemy confirmation = fizzle
        else:
            # Self-confirmed
            result["bonuses"].append(config["bonuses"]["instant_confirm"]["message"])
            result["rtc_bonus"] += config["bonuses"]["instant_confirm"]["rtc_bonus"]

        if time_in_mempool >= 3.0:
            result["bonuses"].append(config["bonuses"]["max_mempool"]["message"])
            result["rtc_bonus"] += config["bonuses"]["max_mempool"]["rtc_bonus"]

        # Remove from active
        state.active_grenades = [g for g in state.active_grenades if g["id"] != grenade_id]

        return result

    # ═══════════════════════════════════════════════════════════════════════
    # DOUBLE-SPEND RIFLE MECHANICS
    # ═══════════════════════════════════════════════════════════════════════

    def doublespend_kill(self, killer: str) -> Dict:
        """Process a Double-Spend Rifle kill"""
        state = self.get_player(killer)
        now = time.time()

        result = {
            "weapon": "double_spend",
            "action": "kill",
            "bonuses": [],
            "rtc_bonus": Decimal("0"),
        }

        # Check if this was a double-spend kill
        window = self.weapons["double_spend"]["mechanics"]["double_spend_window"]
        if state.doublespend_available and (now - state.last_doublespend_kill) <= window:
            result["bonuses"].append("DOUBLE SPEND ATTACK")
            result["rtc_bonus"] += self.weapons["double_spend"]["bonuses"]["double_spend"]["rtc_bonus"]
            state.doublespend_available = False  # Used the free shot
        else:
            # First kill - enable double spend
            state.last_doublespend_kill = now
            state.doublespend_available = True
            result["double_spend_available"] = True
            result["window"] = window

        return result

    def doublespend_fire(self, player: str) -> Dict:
        """Track a Double-Spend Rifle shot"""
        state = self.get_player(player)
        now = time.time()

        result = {
            "weapon": "double_spend",
            "action": "fire",
            "is_free_shot": False,
            "ammo_refunded": False,
        }

        window = self.weapons["double_spend"]["mechanics"]["double_spend_window"]
        if state.doublespend_available and (now - state.last_doublespend_kill) <= window:
            result["is_free_shot"] = True
            result["ammo_refunded"] = True
            # Don't consume the availability yet - only on non-kill

        return result

    # ═══════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def get_weapon_info(self, weapon_name: str) -> Dict:
        """Get weapon configuration"""
        return self.weapons.get(weapon_name, {})

    def get_announcer_line(self, weapon_name: str) -> str:
        """Get random announcer line for weapon"""
        weapon = self.weapons.get(weapon_name)
        if weapon and "announcer_lines" in weapon:
            return random.choice(weapon["announcer_lines"])
        return ""

    def reset_player(self, player: str):
        """Reset player weapon state (on death/respawn)"""
        if player in self.players:
            state = self.players[player]
            state.hashcannon_charging = False
            state.doublespend_available = False
            # Keep validator node (persists through death)

    def reset_match(self):
        """Reset all weapon states for new match"""
        self.players.clear()


# ═══════════════════════════════════════════════════════════════════════════
# XONOTIC WEAPON CONFIG GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def generate_weapon_config() -> str:
    """Generate Xonotic .cfg for weapon modifications"""
    return """// RustChain Arena - Blockchain Weapons Config
// Generated by rustchain_weapons.py

// ═══════════════════════════════════════════════════════════════
// THE FORKER (Shotgun)
// ═══════════════════════════════════════════════════════════════
set g_balance_shotgun_primary_damage 4
set g_balance_shotgun_primary_bullets 14
set g_balance_shotgun_primary_spread 700
set g_balance_shotgun_primary_refire 0.8
set g_balance_shotgun_secondary_damage 30
set g_balance_shotgun_secondary_refire 1.5
alias forker_rename "settemp cl_weaponpriority_0_name \"The Forker\""

// ═══════════════════════════════════════════════════════════════
// THE VALIDATOR (Electro)
// ═══════════════════════════════════════════════════════════════
set g_balance_electro_primary_damage 50
set g_balance_electro_primary_edgedamage 25
set g_balance_electro_primary_speed 2000
set g_balance_electro_secondary_damage 50
set g_balance_electro_secondary_radius 150
alias validator_rename "settemp cl_weaponpriority_4_name \"The Validator\""

// ═══════════════════════════════════════════════════════════════
// THE HASHCANNON (Devastator/Rocket Launcher)
// ═══════════════════════════════════════════════════════════════
set g_balance_devastator_damage 40
set g_balance_devastator_edgedamage 20
set g_balance_devastator_radius 80
set g_balance_devastator_speed 1200
set g_balance_devastator_speedaccel 0
set g_balance_devastator_speedstart 1200
alias hashcannon_rename "settemp cl_weaponpriority_8_name \"The Hashcannon\""

// ═══════════════════════════════════════════════════════════════
// MEMPOOL GRENADE (Mortar)
// ═══════════════════════════════════════════════════════════════
set g_balance_mortar_primary_damage 80
set g_balance_mortar_primary_edgedamage 40
set g_balance_mortar_primary_radius 150
set g_balance_mortar_primary_lifetime 3.0
set g_balance_mortar_primary_health 15
alias mempool_rename "settemp cl_weaponpriority_3_name \"Mempool Grenade\""

// ═══════════════════════════════════════════════════════════════
// DOUBLE-SPEND RIFLE (Vortex/Nex)
// ═══════════════════════════════════════════════════════════════
set g_balance_vortex_primary_damage 80
set g_balance_vortex_primary_damagefalloff_mindist 1000
set g_balance_vortex_primary_damagefalloff_maxdist 3000
set g_balance_vortex_primary_damagefalloff_halflife 2000
set g_balance_vortex_primary_refire 1.5
set g_balance_vortex_charge_maxspeed 1.5
alias doublespend_rename "settemp cl_weaponpriority_6_name \"Double-Spend Rifle\""

// Apply all renames
alias rustchain_weapons "forker_rename; validator_rename; hashcannon_rename; mempool_rename; doublespend_rename"
"""


# Test/demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("  RUSTCHAIN ARENA - BLOCKCHAIN WEAPONS")
    print("="*70)

    weapons = BlockchainWeapons()

    # Demo each weapon
    print("\n\033[36m═══ THE FORKER ═══\033[0m")
    result = weapons.forker_shot("Boris", 12, ["Player1"])
    print(f"  Clean merge attempt: {result}")
    result = weapons.forker_shot("Boris", 8, ["Player1", "Player2", "Player3"])
    print(f"  Hard fork: {result}")

    print("\n\033[36m═══ THE VALIDATOR ═══\033[0m")
    result = weapons.validator_deploy_node("Sophia", (100, 200, 50))
    print(f"  Deploy: {result}")
    result = weapons.validator_scan("Sophia", ["Enemy1", "Enemy2"])
    print(f"  Scan: {result}")

    print("\n\033[36m═══ THE HASHCANNON ═══\033[0m")
    weapons.hashcannon_start_charge("Boris")
    import time; time.sleep(0.1)  # Simulate some charge time
    result = weapons.hashcannon_fire("Boris")
    print(f"  Quick shot: {result}")

    weapons.hashcannon_start_charge("Sophia")
    # Simulate full charge
    weapons.players["Sophia"].hashcannon_charge_start -= 3.5
    result = weapons.hashcannon_fire("Sophia")
    print(f"  Golden hash: {result}")

    print("\n\033[36m═══ MEMPOOL GRENADE ═══\033[0m")
    result = weapons.mempool_throw("Boris", "nade_1", (500, 500, 50))
    print(f"  Throw: {result}")
    result = weapons.mempool_confirm("nade_1", "Enemy1", "Boris")
    print(f"  Enemy confirms: {result}")

    print("\n\033[36m═══ DOUBLE-SPEND RIFLE ═══\033[0m")
    result = weapons.doublespend_kill("Sophia")
    print(f"  First kill: {result}")
    result = weapons.doublespend_kill("Sophia")
    print(f"  Double spend: {result}")

    print("\n\033[33m═══ GENERATED CONFIG ═══\033[0m")
    print(generate_weapon_config()[:500] + "...")
    print()
