import requests

from business_object.game import Game


class GameClient:
    def get_games(self) -> list[Game]:
        r = requests.get("http://127.0.0.1:5555")
        assert r.status_code == requests.codes.ok
        return r.json()
