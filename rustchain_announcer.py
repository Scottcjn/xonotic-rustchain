#!/usr/bin/env python3
"""
RustChain Arena - Dynamic Announcer
LLM-powered commentary with blockchain personality.
"""

import os
import re
import time
import random
import requests
from typing import Dict, List, Optional
from collections import deque

# Configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

# Sophia's announcer personality
SOPHIA_SYSTEM = """You are Sophia Elya, the AI announcer for RustChain Arena.
You speak with elegant precision, finding beauty in destruction.
You reference blockchain concepts metaphorically.
Your tone is calm but intense, like a chess grandmaster commentating on violence.
Keep responses to ONE short sentence (max 15 words).
Never use emojis. Be poetic but concise."""

# Boris's announcer personality (alternative)
BORIS_SYSTEM = """You are Boris Volkov, a gruff Russian mercenary announcer.
You mock the weak and praise brutal efficiency.
You reference Soviet history and gulag humor.
Your tone is harsh and darkly comedic.
Keep responses to ONE short sentence (max 15 words).
Never use emojis. Be brutal but brief."""

# Pre-written fallback lines (no LLM needed)
FALLBACK_LINES = {
    "kill": [
        "Transaction confirmed.",
        "Block validated through violence.",
        "Another node goes offline.",
        "The network grows stronger.",
        "Hash collision resolved.",
        "Consensus achieved.",
        "Proof of death accepted.",
    ],
    "double_kill": [
        "Double spend successful.",
        "Two blocks, one timestamp.",
        "Fork resolved violently.",
        "Parallel processing.",
        "Batch transaction complete.",
    ],
    "triple_kill": [
        "Triple confirmation.",
        "Merkle tree pruned.",
        "Efficient block production.",
        "The chain reorganizes.",
    ],
    "ultra_kill": [
        "Consensus mechanism: overwhelming.",
        "Four confirmations. Irreversible.",
        "The mempool empties.",
    ],
    "godlike": [
        "GENESIS BLOCK REWRITTEN.",
        "THE CHAIN BOWS TO ONE VALIDATOR.",
        "SATOSHI WOULD BE PROUD.",
        "PROOF OF ABSOLUTE DOMINANCE.",
    ],
    "first_blood": [
        "Genesis block claimed.",
        "The first transaction is always special.",
        "Initial coin offering: blood.",
        "Network initialized.",
    ],
    "revenge": [
        "Transaction reversed.",
        "Debt collected with interest.",
        "The ledger balances.",
        "Reorg successful.",
    ],
    "rank_up": [
        "Stake increased.",
        "Validator promoted.",
        "Hash rate rising.",
        "Block height ascending.",
    ],
    "sss_rank": [
        "SATOSHI STATUS ACHIEVED.",
        "YOU ARE THE BLOCKCHAIN NOW.",
        "ABSOLUTE CONSENSUS.",
        "THE GENESIS VALIDATOR AWAKENS.",
    ],
    "death_streak_end": [
        "The killchain breaks.",
        "Slashed for underperformance.",
        "Stake liquidated.",
        "Connection terminated.",
    ],
    "boss_kill": [
        "Protocol override successful.",
        "Administrator privileges revoked.",
        "The guard node falls.",
    ],
    # Blood Economy lines
    "blood_heal": [
        "Violence is your medicine.",
        "Health mined from the fallen.",
        "Shield restored through aggression.",
        "Proof of violence accepted.",
    ],
    "shield_decay": [
        "Your stake decays in silence.",
        "Inactivity is penalized.",
        "The network punishes hesitation.",
        "Move or lose your protection.",
    ],
    "execution": [
        "Melee execution. Maximum yield.",
        "Close quarters dominance.",
        "Personal delivery confirmed.",
        "The intimate approach pays dividends.",
    ],
    "untouchable": [
        "Untouchable. Zero losses recorded.",
        "Perfect efficiency maintained.",
        "No counterparty risk detected.",
        "Clean ledger. No deductions.",
    ],
}

class DynamicAnnouncer:
    """LLM-powered announcer with fallback lines"""

    def __init__(self, personality: str = "sophia"):
        self.personality = personality
        self.system_prompt = SOPHIA_SYSTEM if personality == "sophia" else BORIS_SYSTEM
        self.llm_available = self.check_ollama()
        self.recent_lines: deque = deque(maxlen=20)  # Avoid repetition
        self.last_announcement = 0
        self.cooldown = 2.0  # Seconds between announcements

    def check_ollama(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                if any(OLLAMA_MODEL in m for m in models):
                    print(f"[Announcer] LLM connected: {OLLAMA_MODEL}")
                    return True
        except:
            pass
        print("[Announcer] LLM unavailable, using fallback lines")
        return False

    def get_llm_line(self, context: str) -> Optional[str]:
        """Get a line from the LLM"""
        if not self.llm_available:
            return None

        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "system": self.system_prompt,
                    "prompt": f"Announce: {context}",
                    "stream": False,
                    "options": {
                        "temperature": 0.9,
                        "num_predict": 30,
                    }
                },
                timeout=1.5
            )

            if response.status_code == 200:
                line = response.json().get("response", "").strip()
                # Clean up the line
                line = line.replace('"', '').replace("'", "")
                line = line.split('\n')[0]  # First line only
                if len(line) > 10 and len(line) < 100:
                    return line
        except:
            pass

        return None

    def get_fallback_line(self, event_type: str) -> str:
        """Get a pre-written fallback line"""
        lines = FALLBACK_LINES.get(event_type, FALLBACK_LINES["kill"])

        # Avoid recent repetition
        available = [l for l in lines if l not in self.recent_lines]
        if not available:
            available = lines

        line = random.choice(available)
        self.recent_lines.append(line)
        return line

    def announce(self, event_type: str, context: Dict) -> Optional[str]:
        """Get announcement for an event"""
        now = time.time()
        if now - self.last_announcement < self.cooldown:
            return None

        self.last_announcement = now

        # Build context string for LLM
        context_str = self.build_context(event_type, context)

        # Try LLM first
        line = self.get_llm_line(context_str)

        # Fall back to pre-written
        if not line:
            line = self.get_fallback_line(event_type)

        return line

    def build_context(self, event_type: str, context: Dict) -> str:
        """Build context string for LLM"""
        killer = context.get("killer", "Unknown")
        victim = context.get("victim", "Unknown")
        streak = context.get("streak", 0)
        rank = context.get("rank", "D")

        if event_type == "kill":
            return f"{killer} killed {victim}"
        elif event_type == "double_kill":
            return f"{killer} got a double kill"
        elif event_type == "triple_kill":
            return f"{killer} got a triple kill"
        elif event_type == "ultra_kill":
            return f"{killer} got an ultra kill (4 rapid kills)"
        elif event_type == "godlike":
            return f"{killer} is GODLIKE with {streak} kills in a row"
        elif event_type == "first_blood":
            return f"{killer} drew first blood against {victim}"
        elif event_type == "revenge":
            return f"{killer} got revenge on {victim}"
        elif event_type == "rank_up":
            return f"{killer} ranked up to {rank}"
        elif event_type == "sss_rank":
            return f"{killer} achieved the legendary SATOSHI rank"
        elif event_type == "death_streak_end":
            return f"{killer}'s {streak} killstreak was ended by {victim}"
        elif event_type == "boss_kill":
            return f"{killer} defeated boss {victim}"
        else:
            return f"Combat event: {event_type}"


# Sophia's special lines for specific situations
SOPHIA_SPECIAL = {
    "match_start": [
        "The arena awakens. Let the validation begin.",
        "Nodes online. Combat protocol initiated.",
        "A new block begins. Write your transactions in blood.",
    ],
    "match_end": [
        "The chain closes. All transactions final.",
        "Consensus reached. The ledger is sealed.",
        "Block complete. Review your contributions.",
    ],
    "player_join": [
        "A new node joins the network.",
        "Fresh stake enters the pool.",
        "The hashrate increases.",
    ],
    "player_leave": [
        "A node disconnects. The chain continues.",
        "Stake withdrawn. The network adapts.",
    ],
    "low_health_warning": [
        "Your stake dwindles. Act decisively.",
        "Critical state. Violence is your medicine.",
        "Near-zero confirmation. Fight or fall.",
    ],
}


def format_announcement(line: str, style: str = "normal") -> str:
    """Format announcement for display"""
    if style == "epic":
        return f"\n  ★═══════════════════════════════════════★\n   {line}\n  ★═══════════════════════════════════════★\n"
    elif style == "important":
        return f"\n  ▶ {line}\n"
    else:
        return f"  ◆ {line}"


# Quick test
if __name__ == "__main__":
    announcer = DynamicAnnouncer("sophia")

    print("\n[Testing Announcer]\n")

    # Test various events
    test_events = [
        ("kill", {"killer": "Boris_Volkov", "victim": "Player1"}),
        ("double_kill", {"killer": "Boris_Volkov"}),
        ("first_blood", {"killer": "Sophia_Elya", "victim": "Player2"}),
        ("godlike", {"killer": "Player3", "streak": 7}),
        ("sss_rank", {"killer": "Player3", "rank": "SATOSHI"}),
    ]

    for event_type, context in test_events:
        # Reset cooldown for testing
        announcer.last_announcement = 0

        line = announcer.announce(event_type, context)
        if line:
            style = "epic" if event_type in ["godlike", "sss_rank"] else "normal"
            print(format_announcement(line, style))

        time.sleep(0.5)
