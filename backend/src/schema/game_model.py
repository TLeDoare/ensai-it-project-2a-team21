from datetime import datetime

from pydantic import BaseModel

from schema.player_model import PlayerReadModel


class GamePlayModel(BaseModel):
    id_opponent: int
    game_mode: str
    params: dict = {}


class GameResponse(BaseModel):
    username1: str
    username2: str
    description: str
    winner: str | None
    new_elo1: int
    new_elo2: int


class GameReadModel(BaseModel):
    id_game: int
    game_mode: str | None
    description: str
    timestamp: datetime
    player1: PlayerReadModel
    player2: PlayerReadModel
    winner: PlayerReadModel
