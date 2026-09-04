from abc import ABC, abstractmethod

from business_object.game import Game
from business_object.player import Player


class GameMode(ABC):
    @abstractmethod
    def play(p1: Player, p2: Player) -> Game:
        pass
