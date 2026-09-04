import secrets
from datetime import datetime

from business_object.game import Game
from business_object.game_mode.game_mode import GameMode


class DiceMode(GameMode):
    def play(p1, p2):
        d1 = secrets.choice(range(1, 7))
        d2 = secrets.choice(range(1, 7))
        winner = None
        if d1 > d2:
            winner = p1
        elif d1 < d2:
            winner = p2
        return Game(p1, p2, "dice", winner, "Jeu de dé", datetime.now())
