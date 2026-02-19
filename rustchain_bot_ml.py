#!/usr/bin/env python3
"""
RustChain Arena - ML Bot Trainer
Simple neural network for bot decision making.
Learns combat patterns from game logs without external dependencies.
"""

import os
import re
import json
import time
import random
import pickle
import math
from collections import deque, defaultdict
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Configuration
XONOTIC_LOG = os.path.expanduser("~/.xonotic/data/server.log")
MODEL_PATH = os.path.expanduser("~/Games/Xonotic/bot_brain.pkl")

# Simple Neural Network (no external deps)
class SimpleNN:
    """Minimal neural network implementation for bot decisions"""

    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        # Xavier initialization
        self.W1 = [[random.gauss(0, math.sqrt(2.0/input_size))
                    for _ in range(hidden_size)]
                   for _ in range(input_size)]
        self.b1 = [0.0] * hidden_size

        self.W2 = [[random.gauss(0, math.sqrt(2.0/hidden_size))
                    for _ in range(output_size)]
                   for _ in range(hidden_size)]
        self.b2 = [0.0] * output_size

        self.learning_rate = 0.01

    def relu(self, x: float) -> float:
        return max(0, x)

    def softmax(self, x: List[float]) -> List[float]:
        exp_x = [math.exp(i - max(x)) for i in x]
        sum_exp = sum(exp_x)
        return [i / sum_exp for i in exp_x]

    def forward(self, inputs: List[float]) -> Tuple[List[float], List[float]]:
        """Forward pass through network"""
        # Hidden layer
        hidden = []
        for j in range(self.hidden_size):
            h = self.b1[j]
            for i in range(self.input_size):
                h += inputs[i] * self.W1[i][j]
            hidden.append(self.relu(h))

        # Output layer
        outputs = []
        for j in range(self.output_size):
            o = self.b2[j]
            for i in range(self.hidden_size):
                o += hidden[i] * self.W2[i][j]
            outputs.append(o)

        return self.softmax(outputs), hidden

    def train(self, inputs: List[float], target_idx: int, reward: float):
        """Simple training update with reward signal"""
        outputs, hidden = self.forward(inputs)

        # Compute error (cross-entropy gradient with reward scaling)
        errors = outputs[:]
        errors[target_idx] -= 1.0  # Target should be 1
        errors = [e * reward for e in errors]

        # Update output layer
        for j in range(self.output_size):
            self.b2[j] -= self.learning_rate * errors[j]
            for i in range(self.hidden_size):
                self.W2[i][j] -= self.learning_rate * errors[j] * hidden[i]

        # Backprop to hidden layer
        hidden_errors = [0.0] * self.hidden_size
        for i in range(self.hidden_size):
            for j in range(self.output_size):
                hidden_errors[i] += errors[j] * self.W2[i][j]
            hidden_errors[i] *= 1.0 if hidden[i] > 0 else 0.0

        # Update hidden layer
        for j in range(self.hidden_size):
            self.b1[j] -= self.learning_rate * hidden_errors[j]
            for i in range(self.input_size):
                self.W1[i][j] -= self.learning_rate * hidden_errors[j] * inputs[i]


@dataclass
class CombatState:
    """Encoded combat situation"""
    health_ratio: float           # 0-1
    armor_ratio: float            # 0-1
    ammo_ratio: float             # 0-1
    enemy_distance: float         # 0-1 (normalized)
    enemy_health_estimate: float  # 0-1
    killstreak: float             # 0-1 (normalized)
    deaths_recent: float          # 0-1
    time_since_kill: float        # 0-1
    position_height: float        # 0-1 (low/mid/high)
    team_advantage: float         # -1 to 1

    def to_vector(self) -> List[float]:
        return [
            self.health_ratio,
            self.armor_ratio,
            self.ammo_ratio,
            self.enemy_distance,
            self.enemy_health_estimate,
            self.killstreak,
            self.deaths_recent,
            self.time_since_kill,
            self.position_height,
            self.team_advantage
        ]


class Decision:
    """Bot action decisions"""
    ATTACK_AGGRESSIVE = 0
    ATTACK_CAREFUL = 1
    RETREAT = 2
    SEEK_POWERUP = 3
    SEEK_WEAPON = 4
    HOLD_POSITION = 5

    NAMES = [
        "ATTACK_AGGRESSIVE",
        "ATTACK_CAREFUL",
        "RETREAT",
        "SEEK_POWERUP",
        "SEEK_WEAPON",
        "HOLD_POSITION"
    ]


class BotMLBrain:
    """ML-powered bot decision system"""

    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self.nn = SimpleNN(
            input_size=10,   # CombatState features
            hidden_size=16,
            output_size=6    # Decision options
        )

        # Experience replay buffer
        self.experiences: deque = deque(maxlen=1000)
        self.last_state: Optional[CombatState] = None
        self.last_action: Optional[int] = None

        # Statistics
        self.kills = 0
        self.deaths = 0
        self.decisions_made = 0

        # Personality modifiers
        self.aggression_bias = 0.5  # 0=defensive, 1=aggressive

    def set_personality(self, aggression: float):
        """Adjust personality"""
        self.aggression_bias = max(0, min(1, aggression))

    def get_state_from_context(self, context: dict) -> CombatState:
        """Convert game context to combat state"""
        return CombatState(
            health_ratio=context.get("health", 100) / 200,
            armor_ratio=context.get("armor", 0) / 200,
            ammo_ratio=context.get("ammo", 50) / 100,
            enemy_distance=min(1.0, context.get("enemy_dist", 500) / 1000),
            enemy_health_estimate=context.get("enemy_health_est", 0.5),
            killstreak=min(1.0, context.get("killstreak", 0) / 10),
            deaths_recent=min(1.0, context.get("deaths_recent", 0) / 5),
            time_since_kill=min(1.0, context.get("time_since_kill", 0) / 30),
            position_height=context.get("height_ratio", 0.5),
            team_advantage=context.get("team_advantage", 0)
        )

    def decide(self, state: CombatState) -> int:
        """Make decision based on state"""
        self.decisions_made += 1

        # Get NN output
        probs, _ = self.nn.forward(state.to_vector())

        # Apply personality bias
        if self.aggression_bias > 0.5:
            # Boost aggressive actions
            probs[Decision.ATTACK_AGGRESSIVE] *= 1 + (self.aggression_bias - 0.5)
            probs[Decision.RETREAT] *= 1 - (self.aggression_bias - 0.5) * 0.5
        else:
            # Boost defensive actions
            probs[Decision.RETREAT] *= 1 + (0.5 - self.aggression_bias)
            probs[Decision.ATTACK_AGGRESSIVE] *= 1 - (0.5 - self.aggression_bias) * 0.5

        # Renormalize
        total = sum(probs)
        probs = [p / total for p in probs]

        # Epsilon-greedy exploration (10% random)
        if random.random() < 0.1:
            action = random.randint(0, 5)
        else:
            action = probs.index(max(probs))

        self.last_state = state
        self.last_action = action

        return action

    def learn_from_outcome(self, reward: float):
        """Update NN based on outcome"""
        if self.last_state and self.last_action is not None:
            # Store experience
            self.experiences.append((
                self.last_state.to_vector(),
                self.last_action,
                reward
            ))

            # Train on recent experience
            self.nn.train(
                self.last_state.to_vector(),
                self.last_action,
                reward
            )

            # Replay some past experiences
            if len(self.experiences) > 10:
                for _ in range(3):
                    exp = random.choice(self.experiences)
                    self.nn.train(exp[0], exp[1], exp[2])

    def on_kill(self, victim: str):
        """Called when bot gets a kill"""
        self.kills += 1
        self.learn_from_outcome(1.0)  # Positive reward

    def on_death(self, killer: str):
        """Called when bot dies"""
        self.deaths += 1
        self.learn_from_outcome(-0.5)  # Negative reward

    def save(self, path: str):
        """Save brain to file"""
        data = {
            "bot_name": self.bot_name,
            "nn_W1": self.nn.W1,
            "nn_b1": self.nn.b1,
            "nn_W2": self.nn.W2,
            "nn_b2": self.nn.b2,
            "kills": self.kills,
            "deaths": self.deaths,
            "aggression_bias": self.aggression_bias
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    def load(self, path: str) -> bool:
        """Load brain from file"""
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.nn.W1 = data["nn_W1"]
            self.nn.b1 = data["nn_b1"]
            self.nn.W2 = data["nn_W2"]
            self.nn.b2 = data["nn_b2"]
            self.kills = data.get("kills", 0)
            self.deaths = data.get("deaths", 0)
            self.aggression_bias = data.get("aggression_bias", 0.5)
            return True
        except Exception:
            return False


class GameAnalyzer:
    """Analyzes game logs and trains bots"""

    def __init__(self):
        self.bots: Dict[str, BotMLBrain] = {}
        self.current_context: Dict[str, dict] = {}
        self.last_positions: Dict[str, Tuple[float, float, float]] = {}

    def add_bot(self, name: str, aggression: float = 0.5):
        """Add a bot brain"""
        brain = BotMLBrain(name)
        brain.set_personality(aggression)

        # Try to load existing brain
        save_path = MODEL_PATH.replace(".pkl", f"_{name}.pkl")
        if brain.load(save_path):
            print(f"  [ML] Loaded trained brain for {name}")
        else:
            print(f"  [ML] New brain for {name}")

        self.bots[name] = brain

    def process_line(self, line: str):
        """Process a log line"""
        # Kill event
        kill_match = re.search(r':kill:\d+:\d+:\d+:([^:]+):([^:]+)', line)
        if not kill_match:
            kill_match = re.search(r'(\w+) fragged (\w+)', line)

        if kill_match:
            killer, victim = kill_match.groups()
            killer = killer.strip()
            victim = victim.strip()

            # Update bot brains
            if killer in self.bots:
                self.bots[killer].on_kill(victim)
            if victim in self.bots:
                self.bots[victim].on_death(killer)

            return ("kill", killer, victim)

        return None

    def get_decision(self, bot_name: str) -> Optional[str]:
        """Get bot's tactical decision"""
        if bot_name not in self.bots:
            return None

        brain = self.bots[bot_name]

        # Build context (simplified - would need actual game data)
        context = self.current_context.get(bot_name, {
            "health": 100,
            "armor": 0,
            "ammo": 50,
            "enemy_dist": 500,
            "killstreak": brain.kills % 10,
            "deaths_recent": brain.deaths % 5,
            "time_since_kill": 5,
            "height_ratio": 0.5,
            "team_advantage": 0
        })

        state = brain.get_state_from_context(context)
        action = brain.decide(state)

        return Decision.NAMES[action]

    def save_all(self):
        """Save all bot brains"""
        for name, brain in self.bots.items():
            save_path = MODEL_PATH.replace(".pkl", f"_{name}.pkl")
            brain.save(save_path)
        print(f"  [ML] Saved {len(self.bots)} bot brains")

    def print_stats(self):
        """Print bot statistics"""
        print("\n  ═══════ BOT ML STATS ═══════")
        for name, brain in self.bots.items():
            kd = brain.kills / max(1, brain.deaths)
            print(f"  {name}: {brain.kills}K/{brain.deaths}D (KD: {kd:.2f}) - {brain.decisions_made} decisions")


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║     RUSTCHAIN ARENA - ML Bot Trainer v1.0                 ║
╠═══════════════════════════════════════════════════════════╣
║  Training neural network bots from game patterns          ║
║  No external dependencies required                        ║
╚═══════════════════════════════════════════════════════════╝
""")

    analyzer = GameAnalyzer()

    # Add bots with personality settings
    analyzer.add_bot("Boris_Volkov", aggression=0.9)   # Very aggressive
    analyzer.add_bot("Sophia_Elya", aggression=0.3)    # Defensive/sniper
    analyzer.add_bot("Miner_Node1", aggression=0.5)    # Balanced

    print(f"\n[ML] Monitoring: {XONOTIC_LOG}")
    print("[ML] Bots will learn from combat outcomes\n")

    last_save = time.time()
    save_interval = 300  # Save every 5 minutes

    try:
        with open(XONOTIC_LOG, 'r') as f:
            f.seek(0, 2)  # End of file

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)

                    # Periodic save
                    if time.time() - last_save > save_interval:
                        analyzer.save_all()
                        last_save = time.time()
                    continue

                event = analyzer.process_line(line)

                if event:
                    event_type, arg1, arg2 = event
                    if event_type == "kill":
                        print(f"  {arg1} -> {arg2}", end="")

                        # Show decision for killer if bot
                        if arg1 in analyzer.bots:
                            decision = analyzer.get_decision(arg1)
                            print(f" [{decision}]", end="")
                        print()

    except KeyboardInterrupt:
        print("\n\n[ML] Shutting down...")
        analyzer.print_stats()
        analyzer.save_all()
    except FileNotFoundError:
        print(f"[Error] Log file not found: {XONOTIC_LOG}")


if __name__ == "__main__":
    main()
