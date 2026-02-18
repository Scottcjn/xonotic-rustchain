#!/usr/bin/env python3
"""
RustChain Arena - 51% Attack Game Mode
King of the Hill variant with blockchain mechanics.

Control the network node to mine RTC.
Control >51% of the match time to execute the attack.
"""

import os
import time
import random
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from decimal import Decimal

# Configuration
MATCH_DURATION = 600  # 10 minutes
CONTROL_POINT_CAPTURE_TIME = 3.0  # Seconds to capture
RTC_MINING_RATE = Decimal("0.001")  # Per second while controlling
ATTACK_THRESHOLD = 0.51  # 51% control triggers attack
LOSER_PENALTY = 0.5  # Losing team keeps only 50% of earnings


class ControlState(Enum):
    """Control point states"""
    NEUTRAL = "neutral"
    CONTESTED = "contested"
    CONTROLLED_TEAM1 = "team1"
    CONTROLLED_TEAM2 = "team2"


class AttackPhase(Enum):
    """Match phases"""
    MINING = "mining"  # Normal play
    ATTACK_IMMINENT = "attack_imminent"  # One team at 45%+
    ATTACK_EXECUTED = "attack_executed"  # 51% reached
    DEFENSE_RALLY = "defense_rally"  # Losing team fighting back


@dataclass
class TeamState:
    """Per-team tracking"""
    name: str
    members: Set[str] = field(default_factory=set)
    control_time: float = 0.0
    rtc_mined: Decimal = field(default_factory=lambda: Decimal("0"))
    kills: int = 0
    deaths: int = 0
    captures: int = 0

    @property
    def control_percent(self) -> float:
        """Get control percentage (0-100)"""
        return self.control_time

    def add_control_time(self, seconds: float, total_match_time: float):
        """Add control time and calculate percentage"""
        self.control_time += seconds

    def mine_rtc(self, amount: Decimal):
        """Add mined RTC"""
        self.rtc_mined += amount


@dataclass
class PlayerStats:
    """Individual player stats for the mode"""
    name: str
    team: str
    control_time: float = 0.0
    rtc_earned: Decimal = field(default_factory=lambda: Decimal("0"))
    point_captures: int = 0
    point_defenses: int = 0
    kills_on_point: int = 0


class FiftyOneAttackMode:
    """
    51% Attack Game Mode

    "Control the network. Execute the attack.
     The majority rules. The minority pays."
    """

    def __init__(self, team1_name: str = "Validators", team2_name: str = "Attackers"):
        # Teams
        self.team1 = TeamState(name=team1_name)
        self.team2 = TeamState(name=team2_name)

        # Control point
        self.control_state = ControlState.NEUTRAL
        self.controlling_team: Optional[str] = None
        self.capture_progress: Dict[str, float] = {"team1": 0.0, "team2": 0.0}
        self.players_on_point: Dict[str, Set[str]] = {"team1": set(), "team2": set()}

        # Match state
        self.match_start: float = 0.0
        self.match_duration: float = MATCH_DURATION
        self.phase = AttackPhase.MINING
        self.attack_executed_by: Optional[str] = None

        # Player tracking
        self.players: Dict[str, PlayerStats] = {}

        # Events log
        self.events: List[dict] = []

        # RTC pool
        self.match_rtc_pool = Decimal("1.0")  # Base RTC pool for match
        self.winner_bonus_pool = Decimal("0.5")  # Bonus for 51% winner

    def start_match(self):
        """Initialize a new match"""
        self.match_start = time.time()
        self.control_state = ControlState.NEUTRAL
        self.controlling_team = None
        self.capture_progress = {"team1": 0.0, "team2": 0.0}
        self.phase = AttackPhase.MINING
        self.attack_executed_by = None

        self.team1.control_time = 0.0
        self.team1.rtc_mined = Decimal("0")
        self.team2.control_time = 0.0
        self.team2.rtc_mined = Decimal("0")

        self.events = []

        self._log_event("match_start", {
            "teams": [self.team1.name, self.team2.name],
            "duration": self.match_duration,
            "attack_threshold": ATTACK_THRESHOLD,
        })

        return self.get_status()

    def add_player(self, name: str, team: str) -> Dict:
        """Add player to a team"""
        if team == "team1":
            self.team1.members.add(name)
        else:
            self.team2.members.add(name)

        self.players[name] = PlayerStats(name=name, team=team)

        return {
            "player": name,
            "team": self.team1.name if team == "team1" else self.team2.name,
            "message": f"{name} joined the network as {team}",
        }

    def player_enter_point(self, player: str) -> Dict:
        """Player enters the control point zone"""
        if player not in self.players:
            return {"error": "Player not in match"}

        team = self.players[player].team
        self.players_on_point[team].add(player)

        return {
            "player": player,
            "team": team,
            "action": "entered_point",
            "message": f"{player} approaches the network node",
        }

    def player_leave_point(self, player: str) -> Dict:
        """Player leaves the control point zone"""
        if player not in self.players:
            return {"error": "Player not in match"}

        team = self.players[player].team
        self.players_on_point[team].discard(player)

        return {
            "player": player,
            "team": team,
            "action": "left_point",
        }

    def update(self, dt: float) -> Dict:
        """
        Update game state. Call this every frame/tick.
        Returns dict of events that occurred.
        """
        result = {
            "events": [],
            "announcements": [],
        }

        match_time = time.time() - self.match_start
        if match_time >= self.match_duration:
            return self.end_match()

        # Count players on point
        team1_count = len(self.players_on_point["team1"])
        team2_count = len(self.players_on_point["team2"])

        # Determine point state
        old_state = self.control_state

        if team1_count > 0 and team2_count > 0:
            # Contested
            self.control_state = ControlState.CONTESTED
            # Capture progress decays when contested
            self.capture_progress["team1"] = max(0, self.capture_progress["team1"] - dt * 0.5)
            self.capture_progress["team2"] = max(0, self.capture_progress["team2"] - dt * 0.5)

        elif team1_count > 0:
            # Team 1 capturing/holding
            self._process_capture("team1", dt)

        elif team2_count > 0:
            # Team 2 capturing/holding
            self._process_capture("team2", dt)

        else:
            # No one on point - neutral decay
            self.capture_progress["team1"] = max(0, self.capture_progress["team1"] - dt * 0.3)
            self.capture_progress["team2"] = max(0, self.capture_progress["team2"] - dt * 0.3)

            if self.capture_progress["team1"] == 0 and self.capture_progress["team2"] == 0:
                if self.control_state != ControlState.NEUTRAL:
                    self.control_state = ControlState.NEUTRAL
                    self.controlling_team = None
                    result["events"].append({"type": "neutralized"})

        # Mine RTC if controlling
        if self.controlling_team:
            team = self.team1 if self.controlling_team == "team1" else self.team2
            rtc_gained = RTC_MINING_RATE * Decimal(str(dt))
            team.mine_rtc(rtc_gained)
            team.add_control_time(dt, match_time)

            # Distribute to players on point
            on_point = list(self.players_on_point[self.controlling_team])
            if on_point:
                per_player = rtc_gained / len(on_point)
                for player in on_point:
                    self.players[player].rtc_earned += per_player
                    self.players[player].control_time += dt

        # Check for phase transitions
        team1_percent = self._get_control_percent("team1", match_time)
        team2_percent = self._get_control_percent("team2", match_time)

        if self.phase == AttackPhase.MINING:
            if team1_percent >= 0.45 or team2_percent >= 0.45:
                self.phase = AttackPhase.ATTACK_IMMINENT
                leading = "team1" if team1_percent > team2_percent else "team2"
                result["announcements"].append({
                    "type": "attack_imminent",
                    "team": leading,
                    "percent": max(team1_percent, team2_percent) * 100,
                    "message": f"{self._get_team_name(leading)} approaching 51%! Network under threat!",
                })

        if team1_percent >= ATTACK_THRESHOLD and not self.attack_executed_by:
            self.attack_executed_by = "team1"
            self.phase = AttackPhase.ATTACK_EXECUTED
            result["announcements"].append({
                "type": "attack_executed",
                "team": "team1",
                "message": f"51% ATTACK! {self.team1.name} CONTROL THE NETWORK!",
            })

        elif team2_percent >= ATTACK_THRESHOLD and not self.attack_executed_by:
            self.attack_executed_by = "team2"
            self.phase = AttackPhase.ATTACK_EXECUTED
            result["announcements"].append({
                "type": "attack_executed",
                "team": "team2",
                "message": f"51% ATTACK! {self.team2.name} CONTROL THE NETWORK!",
            })

        result["status"] = self.get_status()
        return result

    def _process_capture(self, team: str, dt: float):
        """Process capture progress for a team"""
        other_team = "team2" if team == "team1" else "team1"

        if self.controlling_team == team:
            # Already controlling - maintain
            pass
        elif self.controlling_team == other_team:
            # Enemy controls - neutralize first
            self.capture_progress[other_team] -= dt
            if self.capture_progress[other_team] <= 0:
                self.capture_progress[other_team] = 0
                self.control_state = ControlState.NEUTRAL
                self.controlling_team = None
                self._log_event("neutralized", {"by_team": team})
        else:
            # Neutral - capture
            self.capture_progress[team] += dt

            if self.capture_progress[team] >= CONTROL_POINT_CAPTURE_TIME:
                self.controlling_team = team
                self.control_state = ControlState.CONTROLLED_TEAM1 if team == "team1" else ControlState.CONTROLLED_TEAM2
                team_obj = self.team1 if team == "team1" else self.team2
                team_obj.captures += 1

                # Award capture bonus to players on point
                for player in self.players_on_point[team]:
                    self.players[player].point_captures += 1

                self._log_event("captured", {
                    "team": team,
                    "team_name": self._get_team_name(team),
                })

    def on_kill(self, killer: str, victim: str, on_point: bool = False) -> Dict:
        """Process a kill"""
        if killer not in self.players or victim not in self.players:
            return {}

        result = {
            "killer": killer,
            "victim": victim,
            "on_point": on_point,
            "bonuses": [],
            "rtc_bonus": Decimal("0"),
        }

        killer_stats = self.players[killer]
        victim_stats = self.players[victim]

        killer_team = self.team1 if killer_stats.team == "team1" else self.team2
        victim_team = self.team1 if victim_stats.team == "team1" else self.team2

        killer_team.kills += 1
        victim_team.deaths += 1

        if on_point:
            killer_stats.kills_on_point += 1
            result["bonuses"].append("POINT DEFENSE")
            result["rtc_bonus"] += Decimal("0.001")

            # Check if victim was on point (preventing capture)
            if victim in self.players_on_point[victim_stats.team]:
                killer_stats.point_defenses += 1
                result["bonuses"].append("VALIDATOR SLAIN")
                result["rtc_bonus"] += Decimal("0.002")

        return result

    def end_match(self) -> Dict:
        """End the match and calculate final rewards"""
        match_time = time.time() - self.match_start

        team1_percent = self._get_control_percent("team1", match_time)
        team2_percent = self._get_control_percent("team2", match_time)

        # Determine winner
        if self.attack_executed_by:
            winner = self.attack_executed_by
            victory_type = "51% ATTACK"
        elif team1_percent > team2_percent:
            winner = "team1"
            victory_type = "MAJORITY CONTROL"
        elif team2_percent > team1_percent:
            winner = "team2"
            victory_type = "MAJORITY CONTROL"
        else:
            winner = None
            victory_type = "DRAW"

        loser = "team2" if winner == "team1" else "team1" if winner == "team2" else None

        # Calculate final RTC
        result = {
            "match_ended": True,
            "duration": match_time,
            "winner": self._get_team_name(winner) if winner else "None",
            "victory_type": victory_type,
            "team1": {
                "name": self.team1.name,
                "control_percent": team1_percent * 100,
                "rtc_mined": float(self.team1.rtc_mined),
                "kills": self.team1.kills,
                "captures": self.team1.captures,
            },
            "team2": {
                "name": self.team2.name,
                "control_percent": team2_percent * 100,
                "rtc_mined": float(self.team2.rtc_mined),
                "kills": self.team2.kills,
                "captures": self.team2.captures,
            },
            "player_rewards": {},
        }

        # Apply winner bonus and loser penalty
        if winner:
            winning_team = self.team1 if winner == "team1" else self.team2
            losing_team = self.team2 if winner == "team1" else self.team1

            # Winner gets bonus pool
            winning_team.rtc_mined += self.winner_bonus_pool

            # Loser penalty
            losing_team.rtc_mined *= Decimal(str(LOSER_PENALTY))

            result["team1"]["rtc_final"] = float(self.team1.rtc_mined)
            result["team2"]["rtc_final"] = float(self.team2.rtc_mined)

            # 51% attack special message
            if victory_type == "51% ATTACK":
                result["special_message"] = (
                    f"{winning_team.name} executed a 51% ATTACK!\n"
                    f"{losing_team.name}'s rewards HALVED!\n"
                    f"The network bows to the majority."
                )

        # Distribute RTC to individual players
        for team_id, team in [("team1", self.team1), ("team2", self.team2)]:
            team_players = [p for p in self.players.values() if p.team == team_id]
            if team_players:
                # Base share + performance bonus
                base_share = team.rtc_mined / len(team_players)
                total_control_time = sum(p.control_time for p in team_players)

                for player in team_players:
                    # Performance-based distribution
                    if total_control_time > 0:
                        control_share = Decimal(str(player.control_time / total_control_time))
                    else:
                        control_share = Decimal("1") / len(team_players)

                    player_rtc = (base_share * Decimal("0.5")) + (team.rtc_mined * control_share * Decimal("0.5"))
                    player.rtc_earned = player_rtc

                    result["player_rewards"][player.name] = {
                        "rtc": float(player_rtc),
                        "control_time": player.control_time,
                        "captures": player.point_captures,
                        "defenses": player.point_defenses,
                        "kills_on_point": player.kills_on_point,
                    }

        self._log_event("match_end", result)
        return result

    def _get_control_percent(self, team: str, match_time: float) -> float:
        """Get team's control percentage"""
        if match_time <= 0:
            return 0.0
        team_obj = self.team1 if team == "team1" else self.team2
        return team_obj.control_time / match_time

    def _get_team_name(self, team: Optional[str]) -> str:
        """Get team display name"""
        if team == "team1":
            return self.team1.name
        elif team == "team2":
            return self.team2.name
        return "None"

    def _log_event(self, event_type: str, data: dict):
        """Log an event"""
        self.events.append({
            "type": event_type,
            "time": time.time() - self.match_start,
            "data": data,
        })

    def get_status(self) -> Dict:
        """Get current game status"""
        match_time = time.time() - self.match_start if self.match_start else 0

        return {
            "phase": self.phase.value,
            "match_time": match_time,
            "time_remaining": max(0, self.match_duration - match_time),
            "control_state": self.control_state.value,
            "controlling_team": self._get_team_name(self.controlling_team),
            "team1": {
                "name": self.team1.name,
                "control_percent": self._get_control_percent("team1", match_time) * 100,
                "rtc_mined": float(self.team1.rtc_mined),
                "players_on_point": len(self.players_on_point["team1"]),
                "capture_progress": self.capture_progress["team1"] / CONTROL_POINT_CAPTURE_TIME * 100,
            },
            "team2": {
                "name": self.team2.name,
                "control_percent": self._get_control_percent("team2", match_time) * 100,
                "rtc_mined": float(self.team2.rtc_mined),
                "players_on_point": len(self.players_on_point["team2"]),
                "capture_progress": self.capture_progress["team2"] / CONTROL_POINT_CAPTURE_TIME * 100,
            },
            "attack_executed_by": self._get_team_name(self.attack_executed_by),
        }


# ═══════════════════════════════════════════════════════════════════════════
# ANNOUNCER LINES
# ═══════════════════════════════════════════════════════════════════════════

ATTACK_51_ANNOUNCEMENTS = {
    "match_start": [
        "The network node is active. Control it to mine RTC.",
        "51% control executes the attack. Dominate or be dominated.",
        "Validators vs Attackers. The majority writes history.",
    ],
    "point_captured": [
        "Network control established. Mining initiated.",
        "Node secured. Hash rate climbing.",
        "Validation authority claimed.",
    ],
    "point_contested": [
        "Network under dispute. Consensus failing.",
        "Fork detected. Multiple validators claiming authority.",
        "Hashrate war in progress.",
    ],
    "attack_imminent": [
        "WARNING: 51% attack imminent! Defend the network!",
        "Critical threshold approaching. The chain is vulnerable.",
        "Majority control nearly achieved. Brace for reorganization.",
    ],
    "attack_executed": [
        "51% ATTACK EXECUTED! THE CHAIN HAS BEEN REORGANIZED!",
        "CONSENSUS OVERRIDDEN! THE MAJORITY HAS SPOKEN!",
        "DOUBLE SPEND SUCCESSFUL! HISTORY REWRITTEN!",
    ],
    "match_end_winner": [
        "Network secured. The validators are rewarded.",
        "Majority achieved. The blockchain acknowledges the victor.",
        "Transaction finalized. Rewards distributed.",
    ],
    "match_end_loser": [
        "Insufficient hashrate. Your rewards are slashed.",
        "The minority's stake has been reduced.",
        "Consensus rejected your claim.",
    ],
}


def format_status_bar(status: Dict, width: int = 60) -> str:
    """Format status as ASCII display"""
    t1 = status["team1"]
    t2 = status["team2"]

    # Control bar
    t1_width = int((t1["control_percent"] / 100) * (width - 10))
    t2_width = int((t2["control_percent"] / 100) * (width - 10))
    neutral_width = width - 10 - t1_width - t2_width

    bar = (
        f"\033[92m{'█' * t1_width}\033[0m"
        f"\033[90m{'░' * neutral_width}\033[0m"
        f"\033[91m{'█' * t2_width}\033[0m"
    )

    lines = [
        f"╔{'═' * (width-2)}╗",
        f"║ 51% ATTACK MODE - {status['phase'].upper():^{width-22}} ║",
        f"╠{'═' * (width-2)}╣",
        f"║ {t1['name']:^{(width-4)//2}} vs {t2['name']:^{(width-4)//2}} ║",
        f"║ [{bar}] ║",
        f"║ {t1['control_percent']:.1f}%{' ' * (width-20)}{t2['control_percent']:.1f}% ║",
        f"║ RTC: {t1['rtc_mined']:.4f}{' ' * (width-26)}RTC: {t2['rtc_mined']:.4f} ║",
        f"╚{'═' * (width-2)}╝",
    ]

    if status["attack_executed_by"] != "None":
        lines.insert(-1, f"║ {'★ 51% ATTACK EXECUTED ★':^{width-4}} ║")

    return "\n".join(lines)


# Test/demo
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  51% ATTACK MODE - SIMULATION")
    print("="*60 + "\n")

    mode = FiftyOneAttackMode("Validators", "Attackers")
    mode.start_match()

    # Add players
    mode.add_player("Boris", "team1")
    mode.add_player("Sophia", "team1")
    mode.add_player("Player1", "team2")
    mode.add_player("Player2", "team2")

    print("Match started!\n")
    print(random.choice(ATTACK_51_ANNOUNCEMENTS["match_start"]))
    print()

    # Simulate some gameplay
    mode.player_enter_point("Boris")
    mode.player_enter_point("Sophia")

    # Simulate 5 seconds of control
    for _ in range(50):
        result = mode.update(0.1)
        if result.get("announcements"):
            for ann in result["announcements"]:
                print(f"\n\033[93m>>> {ann['message']}\033[0m\n")

    status = mode.get_status()
    print(format_status_bar(status))

    # Contest the point
    print("\n--- Attackers approach! ---\n")
    mode.player_enter_point("Player1")

    for _ in range(30):
        result = mode.update(0.1)

    status = mode.get_status()
    print(format_status_bar(status))

    # Kill on point
    print("\n--- Combat! ---\n")
    kill_result = mode.on_kill("Boris", "Player1", on_point=True)
    print(f"Boris killed Player1: {kill_result}")
    mode.player_leave_point("Player1")

    # More control time
    for _ in range(200):
        result = mode.update(0.1)
        if result.get("announcements"):
            for ann in result["announcements"]:
                print(f"\n\033[93m>>> {ann['message']}\033[0m\n")

    status = mode.get_status()
    print("\n" + format_status_bar(status))

    # Simulate match end
    print("\n--- Match End ---\n")
    # Fast forward the time
    mode.match_start -= 550  # Make it near end

    end_result = mode.end_match()
    print(f"\n\033[92mWinner: {end_result['winner']}\033[0m")
    print(f"Victory Type: {end_result['victory_type']}")
    print(f"\n{end_result.get('special_message', '')}")

    print("\n\033[36mFinal Standings:\033[0m")
    print(f"  {end_result['team1']['name']}: {end_result['team1']['control_percent']:.1f}% control, "
          f"{end_result['team1'].get('rtc_final', end_result['team1']['rtc_mined']):.4f} RTC")
    print(f"  {end_result['team2']['name']}: {end_result['team2']['control_percent']:.1f}% control, "
          f"{end_result['team2'].get('rtc_final', end_result['team2']['rtc_mined']):.4f} RTC")

    print("\n\033[36mPlayer Rewards:\033[0m")
    for player, rewards in end_result["player_rewards"].items():
        print(f"  {player}: {rewards['rtc']:.4f} RTC "
              f"(control: {rewards['control_time']:.1f}s, captures: {rewards['captures']})")

    print()
