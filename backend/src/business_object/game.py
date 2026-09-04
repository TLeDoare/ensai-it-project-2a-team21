from datetime import datetime

from business_object.player import Player


class Game:
    def __init__(
        self,
        player1: Player,
        player2: Player,
        game_mode: str,
        winner: Player,
        description: str,
        timestamp: datetime,
    ):
        self.id = None
        self.player1 = player1
        self.player2 = player2
        self.game_mode = game_mode
        self.winner = winner
        self.description = description
        self.timestamp = datetime

    def __str__(self):
        return f"{self.game_mode} between {self.player1.username} and {self.player2.username}. Winner: {self.winner.username}"
