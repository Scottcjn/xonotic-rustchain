#!/usr/bin/env python3
"""Discord Integration for RustChain Arena"""
import requests
import json

DISCORD_WEBHOOK = "YOUR_WEBHOOK_URL_HERE"

def post_embed(embed):
    requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})

def announce_kill(killer, victim, rtc, streak=0):
    streak_text = f" 🔥 {streak} STREAK!" if streak >= 3 else ""
    embed = {
        "title": "⚔️ Arena Kill",
        "description": f"**{killer}** fragged **{victim}**{streak_text}",
        "color": 0xFF6600 if streak < 5 else 0xFF0000,
        "fields": [{"name": "RTC Earned", "value": f"+{rtc} RTC", "inline": True}],
        "footer": {"text": "RustChain Arena"}
    }
    post_embed(embed)

def announce_match_end(winner, stats):
    embed = {
        "title": "🏆 Match Complete!",
        "color": 0x00FF00,
        "fields": [
            {"name": "🥇 Winner", "value": winner, "inline": True},
            {"name": "💀 Total Kills", "value": str(stats["kills"]), "inline": True},
            {"name": "💰 RTC Distributed", "value": f"{stats['rtc']:.4f} RTC", "inline": True}
        ],
        "footer": {"text": "RustChain Arena | Play to Earn"}
    }
    post_embed(embed)

def announce_tournament(name, prize_pool, participants):
    embed = {
        "title": f"🎮 {name} Starting!",
        "color": 0xFFD700,
        "fields": [
            {"name": "Prize Pool", "value": f"{prize_pool} RTC", "inline": True},
            {"name": "Players", "value": str(participants), "inline": True}
        ]
    }
    post_embed(embed)
