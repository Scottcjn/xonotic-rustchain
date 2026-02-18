#!/usr/bin/env python3
"""Tournament System for RustChain Arena"""
from decimal import Decimal
from datetime import datetime
import sqlite3

class Tournament:
    def __init__(self, name, entry_fee=0, base_prize=1):
        self.name = name
        self.entry_fee = Decimal(str(entry_fee))
        self.base_prize = Decimal(str(base_prize))
        self.participants = []
        self.matches = []
        self.status = "registration"
    
    @property
    def prize_pool(self):
        return self.base_prize + (self.entry_fee * len(self.participants))
    
    def register(self, player_id, wallet):
        if self.status != "registration":
            raise Exception("Registration closed")
        self.participants.append({"id": player_id, "wallet": wallet})
        return True
    
    def start(self):
        if len(self.participants) < 2:
            raise Exception("Need at least 2 players")
        self.status = "active"
        # Generate bracket...
    
    def end(self, rankings):
        """rankings = {1: "player1", 2: "player2", 3: "player3"}"""
        self.status = "complete"
        
        # Prize distribution: 50/30/20
        prizes = {
            1: self.prize_pool * Decimal("0.50"),
            2: self.prize_pool * Decimal("0.30"),
            3: self.prize_pool * Decimal("0.20"),
        }
        
        results = []
        for place, player in rankings.items():
            if place in prizes:
                results.append({
                    "player": player,
                    "place": place,
                    "prize": prizes[place]
                })
        return results

# Scheduled tournaments
SCHEDULE = {
    "daily_duel": {
        "time": "20:00",
        "entry": 0,
        "prize": 1,
        "format": "1v1"
    },
    "weekly_war": {
        "day": "Saturday",
        "time": "18:00",
        "entry": 0.1,
        "prize": 5,
        "format": "ffa"
    }
}
