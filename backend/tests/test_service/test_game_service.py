from datetime import date
from unittest.mock import MagicMock

from business_object.game import Game
from business_object.player import Player
from dao.game_dao import GameDao
from service.game_service import GameService

p1 = Player(15, "salut", "qsdg", 1500, "ff@ff.fff", True, "")
p2 = Player(14, "salut3", "qsdg", 1200, "ff@ff.fff", False, "")
p3 = Player(100, "hjqsdfjhl", "qsdg", 1200, "ff@ff.fff", False, "")

game_list = [
    Game(p1, p2, "dice", p2, "test", date(2025, 12, 31), 20),
    Game(p2, p3, "dice", p2, "test", date(2025, 12, 30), 21),
    Game(p3, p1, "dice", p3, "test", date(2025, 12, 29), 22),
]


def test_list_all():
    GameDao().find_all_by_player = MagicMock(return_value=game_list)

    res = GameService().find_all_by_player(15)

    assert len(res) == 3
