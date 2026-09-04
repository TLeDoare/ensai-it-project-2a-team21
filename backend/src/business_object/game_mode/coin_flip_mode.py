import secrets

from business_object.game_mode.game_mode import GameMode


class CoinFlipMode(GameMode):
    def play(p1, p2, choice: str):
        result = secrets.choice(["heads", "tails"])
        return p1 if result == choice else p2
