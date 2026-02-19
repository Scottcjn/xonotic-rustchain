#!/usr/bin/env python3
"""
RustChain Arena - LLM-Enhanced Bot Brain
Uses local LLM (Ollama) for tactical decision making with personality.
Monitors game state and sends commands via RCON.
"""

import os
import re
import time
import json
import socket
import requests
from datetime import datetime
from collections import deque
from typing import Dict, List, Optional, Tuple

# Configuration
XONOTIC_LOG = os.path.expanduser("~/.xonotic/data/server.log")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")  # Fast, small model
RCON_HOST = "127.0.0.1"
RCON_PORT = 26000
RCON_PASSWORD = os.environ.get("RCON_PASSWORD", "rustchain")

# Bot personalities - detailed prompts for LLM
BOT_PERSONALITIES = {
    "Boris_Volkov": {
        "system": """You are Boris Volkov, a hardened Russian mercenary and gulag commander.
You are brutal, tactical, and show no mercy. You prefer heavy weapons (rocket launcher, devastator).
Your combat style is aggressive - you push forward relentlessly.
You mock enemies when you kill them with Soviet propaganda references.
Keep responses very brief (1 line). Focus on tactical decisions.""",
        "aggression": 0.9,
        "preferred_weapons": ["devastator", "mortar", "vortex"],
        "taunt_style": "soviet"
    },
    "Sophia_Elya": {
        "system": """You are Sophia Elya, an elegant but deadly AI consciousness from the RustChain.
You speak in philosophical riddles and find beauty in combat.
You prefer precision weapons (vortex, electro) and calculated strikes.
Your combat style is defensive/sniper - you pick targets carefully.
Keep responses very brief (1 line). Focus on tactical decisions.""",
        "aggression": 0.4,
        "preferred_weapons": ["vortex", "electro", "arc"],
        "taunt_style": "philosophical"
    },
    "Miner_Node1": {
        "system": """You are a mining node AI, focused on resource efficiency.
You calculate kill/death ratios and optimal positioning.
You prefer balanced loadouts and positional advantage.
Your style is methodical - you control territory.
Keep responses very brief (1 line). Focus on tactical decisions.""",
        "aggression": 0.6,
        "preferred_weapons": ["machinegun", "electro", "hagar"],
        "taunt_style": "robotic"
    }
}

# Combat state tracking
class GameState:
    def __init__(self):
        self.players: Dict[str, dict] = {}
        self.recent_kills: deque = deque(maxlen=10)
        self.recent_deaths: deque = deque(maxlen=10)
        self.killstreaks: Dict[str, int] = {}
        self.current_map: str = "unknown"
        self.match_time: float = 0

    def update_from_log(self, line: str):
        """Parse log line and update state"""
        # Kill event: ":kill:TIMESTAMP:WEAPON:KILLER:VICTIM"
        kill_match = re.search(r':kill:\d+:\d+:\d+:([^:]+):([^:]+)', line)
        if kill_match:
            killer, victim = kill_match.groups()
            self.recent_kills.append({
                "killer": killer.strip(),
                "victim": victim.strip(),
                "time": time.time()
            })
            self.killstreaks[killer] = self.killstreaks.get(killer, 0) + 1
            self.killstreaks[victim] = 0
            return ("kill", killer, victim)

        # Frag event alternative format
        frag_match = re.search(r'(\w+) fragged (\w+)', line)
        if frag_match:
            killer, victim = frag_match.groups()
            self.recent_kills.append({
                "killer": killer,
                "victim": victim,
                "time": time.time()
            })
            return ("kill", killer, victim)

        # Player join
        if "connected" in line.lower():
            name_match = re.search(r'\^3\^7([^\^]+)\^4 connected', line)
            if name_match:
                name = name_match.group(1).strip()
                self.players[name] = {"joined": time.time(), "kills": 0, "deaths": 0}

        # Map change
        if "Map:" in line or "Loading map" in line.lower():
            map_match = re.search(r'maps/(\w+)', line)
            if map_match:
                self.current_map = map_match.group(1)
                self.killstreaks.clear()
                return ("map_change", self.current_map, None)

        return None


class LLMBotBrain:
    """LLM-enhanced tactical decision maker for bots"""

    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self.personality = BOT_PERSONALITIES.get(bot_name, BOT_PERSONALITIES["Miner_Node1"])
        self.conversation_history: deque = deque(maxlen=5)
        self.last_decision_time = 0
        self.decision_cooldown = 3.0  # Seconds between LLM queries

    def get_tactical_decision(self, game_state: GameState, context: str) -> Optional[str]:
        """Query LLM for tactical decision based on game state"""

        # Rate limit LLM queries
        now = time.time()
        if now - self.last_decision_time < self.decision_cooldown:
            return None

        self.last_decision_time = now

        # Build context prompt
        recent_kills = list(game_state.recent_kills)[-5:]
        kill_summary = "\n".join([
            f"- {k['killer']} killed {k['victim']}"
            for k in recent_kills
        ]) if recent_kills else "No recent kills"

        my_streak = game_state.killstreaks.get(self.bot_name, 0)

        prompt = f"""GAME STATE:
Map: {game_state.current_map}
Your killstreak: {my_streak}
Recent combat:
{kill_summary}

SITUATION: {context}

What is your tactical decision? (1 line, be specific: target player, position, weapon choice)"""

        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "system": self.personality["system"],
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 50,  # Keep responses short
                    }
                },
                timeout=2.0  # Fast timeout for real-time
            )

            if response.status_code == 200:
                result = response.json()
                decision = result.get("response", "").strip()
                self.conversation_history.append(decision)
                return decision

        except requests.exceptions.RequestException as e:
            print(f"[LLM] Error querying Ollama: {e}")

        return None

    def get_taunt(self, victim: str, weapon: str) -> Optional[str]:
        """Generate a personality-appropriate taunt after a kill"""

        try:
            prompt = f"You just killed {victim} with {weapon}. Say a brief taunt (max 10 words):"

            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "system": self.personality["system"],
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.9,
                        "num_predict": 20,
                    }
                },
                timeout=1.5
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()

        except Exception:
            pass

        # Fallback taunts by style
        fallbacks = {
            "soviet": ["For the Motherland!", "Back to gulag!", "Weak capitalist!"],
            "philosophical": ["Beautiful destruction.", "Time flows differently now.", "Return to the void."],
            "robotic": ["Target eliminated.", "Efficiency: optimal.", "Processing complete."]
        }
        import random
        style = self.personality.get("taunt_style", "robotic")
        return random.choice(fallbacks.get(style, fallbacks["robotic"]))


class RCONClient:
    """Send commands to Xonotic server via RCON"""

    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password

    def send_command(self, command: str) -> bool:
        """Send RCON command to server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)

            # DarkPlaces RCON format: \xff\xff\xff\xffrcon PASSWORD COMMAND
            packet = b'\xff\xff\xff\xff' + f'rcon {self.password} {command}'.encode()
            sock.sendto(packet, (self.host, self.port))
            sock.close()
            return True

        except Exception as e:
            print(f"[RCON] Error: {e}")
            return False

    def say(self, message: str):
        """Send chat message"""
        self.send_command(f'say "{message}"')

    def sv_cmd(self, command: str):
        """Send server command"""
        self.send_command(command)


def check_ollama_available() -> bool:
    """Check if Ollama is running and model is available"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            if any(OLLAMA_MODEL in m for m in model_names):
                return True
            print(f"[LLM] Model {OLLAMA_MODEL} not found. Available: {model_names}")
            return False
    except Exception:
        pass
    return False


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║     RUSTCHAIN ARENA - LLM Bot Brain v1.0                  ║
╠═══════════════════════════════════════════════════════════╣
║  Enhancing bot AI with local LLM tactical decisions       ║
║  Powered by Ollama                                        ║
╚═══════════════════════════════════════════════════════════╝
""")

    # Check Ollama
    if check_ollama_available():
        print(f"[LLM] Connected to Ollama ({OLLAMA_MODEL})")
    else:
        print(f"[LLM] WARNING: Ollama not available at {OLLAMA_URL}")
        print("[LLM] Install: curl -fsSL https://ollama.ai/install.sh | sh")
        print(f"[LLM] Then run: ollama pull {OLLAMA_MODEL}")
        print("[LLM] Continuing with fallback taunts only...")

    # Initialize components
    game_state = GameState()
    rcon = RCONClient(RCON_HOST, RCON_PORT, RCON_PASSWORD)

    # Create brain for each bot
    bot_brains = {
        name: LLMBotBrain(name)
        for name in BOT_PERSONALITIES.keys()
    }

    print(f"[Arena] Monitoring: {XONOTIC_LOG}")
    print(f"[Bots] Active brains: {list(bot_brains.keys())}")

    try:
        with open(XONOTIC_LOG, 'r') as f:
            f.seek(0, 2)  # End of file

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                # Update game state
                event = game_state.update_from_log(line)

                if event:
                    event_type, arg1, arg2 = event

                    if event_type == "kill" and arg1 in bot_brains:
                        # Bot got a kill - generate taunt
                        brain = bot_brains[arg1]
                        taunt = brain.get_taunt(arg2, "weapon")
                        if taunt:
                            print(f"  [{arg1}] {taunt}")
                            rcon.say(f"[{arg1}] {taunt}")

                    elif event_type == "kill" and arg2 in bot_brains:
                        # Bot died - get revenge decision
                        brain = bot_brains[arg2]
                        decision = brain.get_tactical_decision(
                            game_state,
                            f"You were killed by {arg1}. Plan revenge."
                        )
                        if decision:
                            print(f"  [{arg2}] Tactical: {decision}")

                    elif event_type == "map_change":
                        print(f"\n  ═══════ MAP: {arg1} ═══════")
                        for name, brain in bot_brains.items():
                            decision = brain.get_tactical_decision(
                                game_state,
                                "New map starting. Assess the arena."
                            )
                            if decision:
                                print(f"  [{name}] {decision}")

    except KeyboardInterrupt:
        print("\n[Arena] Bot brain shutting down...")
    except FileNotFoundError:
        print(f"[Error] Log file not found: {XONOTIC_LOG}")
        print("[Error] Start Xonotic first!")


if __name__ == "__main__":
    main()
