import secrets
from datetime import datetime

from business_object.game import Game
from business_object.game_mode.game_mode import GameMode


class CoinFlipMode(GameMode):
    def play(p1, p2, choice: str):
        result = secrets.choice(["heads", "tails"])
        winner = p1 if result == choice else p2
        return Game(p1, p2, "coinflip", winner, "Jeu de la pièce", datetime.now())
