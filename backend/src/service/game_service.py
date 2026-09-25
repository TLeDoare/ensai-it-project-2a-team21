from fastapi import HTTPException

from business_object.game import Game
from business_object.game_mode.game_mode_factory import GameModeFactory
from business_object.scoring_strategy import ScoringStrategy
from dao.game_dao import GameDao
from dao.player_dao import PlayerDao
from utils.log_utils import log


class GameService:
    """Service that manages games."""

    @log
    def play(self, id_player: int, id_opponent: int, game_mode: str, **kwargs):
        """Executes a single round of a coin-flip game between two players.
        Args:
            id_player (int): The unique identifier of the first player.
            id_opponent (int): The unique identifier of the opponent.
            choice (str, optional): The player's choice ('heads' or 'tails'). Defaults to "heads".
        Returns:
            dict: A dictionary containing the match details and new elo
        Raises:
            HTTPException: 400 if the two players are the same.
            HTTPException: 404 if one or both players are not found in the database.
        """
        if id_player == id_opponent:
            raise HTTPException(status_code=400, detail="Two different players required")

        p1 = PlayerDao().find_by_id(id_player)
        p2 = PlayerDao().find_by_id(id_opponent)

        if not p1 or not p2:
            raise HTTPException(status_code=404, detail="Player not found")

        mode = GameModeFactory.get_mode(game_mode)

        game = mode.play(p1, p2, **kwargs)

        ScoringStrategy.update_player_ratings(game)

        GameDao().create(game)
        PlayerDao().update(p1)
        PlayerDao().update(p2)

        return game

    @log
    def find_by_id(self, id_game: int) -> Game:
        """Find a specific game by its id.
        Args:
            id_game (int): The unique identifier of the game.
        Returns:
            Game object if found, otherwise None.
        """
        return GameDao().find_by_id(id_game)

    @log
    def get_win_loss_stat(self, id_player: int):
        games = self.find_all_by_player(id_player)
        tot = 0
        nwin = 0
        for g in games:
            tot += 1
            if g.winner is not None:
                nwin += int(g.winner.id_player == id_player)
        return None if tot == 0 else nwin / tot

    @log
    def find_all_by_player(self, id_player: int, game_mode: str = None) -> list[Game]:
        """List all games involving a specific player.
        Args:
            id_player (int): The unique identifier of the player.
        Returns:
            list[Game] containing all matches the player participated in.
        """
        games = GameDao().find_all_by_player(id_player)

        if game_mode is None:
            return games
        else:
            return [g for g in games if g.game_mode == game_mode]
