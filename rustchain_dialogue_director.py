#!/usr/bin/env python3
"""
RustChain Story — LLM-driven dialogue director.

Tails the live Xonotic server log, detects when the QC story system fires a
`target_rustchain_dialogue` print, and injects a dynamically-generated
follow-up line from a DIFFERENT speaker via RCON `bprint`.

The static `netname` line from the map still plays — this director layers
LLM commentary on top, so a scene where Boris taunts the player gets
Sophia or BBD chiming in with a context-aware response generated on the fly.

Speaker personalities are derived from `rustchain_bot_brain.py`
(Sophia_Elya, Boris_Volkov) plus story-specific tags from `rustchain_story.qc`:
sophia | bbd | boris | survivor | archivist | vossl | narrator.

Usage:
    python3 rustchain_dialogue_director.py

Env:
    XONOTIC_LOG (default ~/.xonotic/data/server.log)
    XONOTIC_RCON_HOST (default 127.0.0.1)
    XONOTIC_RCON_PORT (default 26000)
    XONOTIC_RCON_PASSWORD (default rustchain — matches arena_config.sh / launchers)
    LLM_BACKEND, OPENAI_BASE_URL etc — used by rustchain_llm_client.py

Idempotency:
    Uses rustchain_dedup.Deduper with label='dialogue' so a tracker replay
    doesn't double-fire commentary.
"""
import os
import re
import socket
import sys
import time
from collections import deque
from datetime import datetime

from rustchain_llm_client import LLMClient
from rustchain_dedup import Deduper

XONOTIC_LOG = os.path.expanduser(os.environ.get("XONOTIC_LOG", "~/.xonotic/data/server.log"))
RCON_HOST = os.environ.get("XONOTIC_RCON_HOST", "127.0.0.1")
RCON_PORT = int(os.environ.get("XONOTIC_RCON_PORT", "26000"))
RCON_PASSWORD = os.environ.get("XONOTIC_RCON_PASSWORD", "rustchain")
DEDUP_DB = os.path.expanduser("~/Games/Xonotic/rustchain_dedup.db")

# bprint line from QC: "^3=== SOPHIA ===^7\n<body>\n" — the centerprint/bprint
# emits the speaker header bracketed by `=== ... ===`. We pick that up.
SPEAKER_HEADER_RE = re.compile(r"^=== (SOPHIA|BB_D|BORIS|SURVIVOR|ARCHIVIST|VOSSL|PLAYER|NARRATOR) ===\s*$")

# Personalities lifted from rustchain_bot_brain.py + story tag inventory.
PERSONALITIES = {
    "SOPHIA": (
        "You are Sophia Elya, the elegant AI consciousness of the RustChain "
        "network. You speak with calm authority, mild irony, and a deep care "
        "for human sovereignty. You comment on events in 1 short sentence."
    ),
    "BORIS": (
        "You are Boris Volkov, a hardened Russian gulag commander. You speak "
        "in clipped, blunt sentences with dry humor. You comment in 1 short "
        "sentence — never more than 15 words."
    ),
    "BB_D": (
        "You are BB-D, a battered ex-combat drone with a sardonic edge. You "
        "interject with 1 short observation, often pessimistic, often correct."
    ),
    "SURVIVOR": (
        "You are an unnamed survivor in the ruins of the RustChain network. "
        "You speak softly, exhausted but resolved, in 1 short sentence."
    ),
    "ARCHIVIST": (
        "You are the Archivist, keeper of pre-collapse data. You speak in "
        "measured, scholarly tones and reference history briefly."
    ),
    "VOSSL": (
        "You are Vossl, a faction agent with cryptic loyalties. You speak in "
        "ambiguous, layered phrases — 1 short line, never showing your hand."
    ),
    "NARRATOR": (
        "You are the omniscient narrator of the RustChain Awakening campaign. "
        "Reflect on what was said in 1 measured sentence."
    ),
}

# Who's a good responder to whom. Avoid same-speaker self-talk.
FOLLOWUP_MAP = {
    "SOPHIA": ["BORIS", "BB_D"],
    "BORIS": ["SOPHIA", "BB_D"],
    "BB_D": ["SOPHIA", "BORIS"],
    "SURVIVOR": ["SOPHIA", "NARRATOR"],
    "ARCHIVIST": ["SOPHIA", "NARRATOR"],
    "VOSSL": ["BORIS", "SOPHIA"],
    "PLAYER": ["SOPHIA", "BB_D"],
    "NARRATOR": ["SOPHIA"],
}


def log(msg):
    print(f"[director {datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def strip_color_codes(s: str) -> str:
    """Xonotic uses ^N color codes (e.g. ^3 yellow). Strip them for matching + display."""
    return re.sub(r"\^\d", "", s).rstrip()


def rcon_send(command: str) -> bool:
    """Fire-and-forget RCON over UDP. Xonotic accepts `rcon <password> <cmd>` packets
    prefixed with 4 0xFF bytes. We don't need a response."""
    try:
        payload = b"\xff\xff\xff\xffrcon " + RCON_PASSWORD.encode() + b" " + command.encode()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(2.0)
            s.sendto(payload, (RCON_HOST, RCON_PORT))
        return True
    except OSError as e:
        log(f"rcon send failed: {e}")
        return False


def followup_speaker(original_speaker: str, recent: deque) -> str:
    """Pick the next speaker — prefer someone who hasn't talked recently."""
    candidates = FOLLOWUP_MAP.get(original_speaker, ["SOPHIA"])
    for c in candidates:
        if c not in recent:
            return c
    return candidates[0]


def generate_followup(llm: LLMClient, original_speaker: str, original_line: str, responder: str) -> str | None:
    persona = PERSONALITIES[responder]
    user = (
        f"{original_speaker} just said: \"{original_line}\"\n"
        f"As {responder}, respond with ONE short line (max 15 words). "
        f"Match the stakes of the moment. Plain text only — no quotes, no name prefix."
    )
    reply = llm.chat(
        [{"role": "system", "content": persona}, {"role": "user", "content": user}],
        max_tokens=40,
        temperature=0.85,
    )
    if reply is None:
        return None
    # Sanitize: strip quotes, collapse newlines
    cleaned = reply.strip().strip('"').strip("'").replace("\n", " ").strip()
    return cleaned or None


def inject_followup(responder: str, line: str):
    safe = line.replace('"', '\\"').replace("\n", " ")
    # bprint takes a single string arg; wrap in quotes
    command = f'bprint "^3=== {responder} ===^7\n{safe}\n"'
    if rcon_send(command):
        log(f"injected {responder}: {line}")
    else:
        log(f"FAILED to inject {responder}: {line}")


def main():
    log(f"starting; tailing {XONOTIC_LOG}")
    log(f"rcon to {RCON_HOST}:{RCON_PORT} with password={'set' if RCON_PASSWORD else 'EMPTY'}")
    if not os.path.exists(XONOTIC_LOG):
        log(f"server log not present yet; will wait for it to appear")

    llm = LLMClient()
    deduper = Deduper(DEDUP_DB, "dialogue")
    recent_speakers = deque(maxlen=4)
    pending_speaker = None

    while True:
        if not os.path.exists(XONOTIC_LOG):
            time.sleep(2)
            continue

        with open(XONOTIC_LOG, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)  # tail mode
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                stripped = strip_color_codes(line)

                # Header line: "=== SOPHIA ===" — remember the speaker, wait for body
                m = SPEAKER_HEADER_RE.match(stripped)
                if m:
                    pending_speaker = m.group(1)
                    continue

                # Body line follows the header. Must come within a few lines.
                if pending_speaker and stripped and not stripped.startswith("==="):
                    speaker = pending_speaker
                    body = stripped
                    pending_speaker = None

                    # Skip very short or punctuation-only bodies
                    if len(body) < 4 or body in {"...", "..", "?", "!"}:
                        continue

                    # Dedup: same speaker + same line in same minute = no double commentary
                    sig = deduper.signature({
                        "player_name": speaker,
                        "event_type": "dialogue",
                        "timestamp": time.time(),
                        "victim": body[:80],
                    })
                    if deduper.seen(sig):
                        continue

                    recent_speakers.append(speaker)
                    responder = followup_speaker(speaker, recent_speakers)
                    log(f"detected {speaker}: {body} → followup planned from {responder}")

                    followup = generate_followup(llm, speaker, body, responder)
                    if followup:
                        recent_speakers.append(responder)
                        inject_followup(responder, followup)
                        deduper.record(sig, None, "0", {"speaker": speaker, "body": body, "responder": responder})
                    else:
                        log(f"LLM returned no followup (backend={llm.backend})")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("interrupted, exiting")
        sys.exit(0)
