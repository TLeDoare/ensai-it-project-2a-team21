from business_object.game import Game
from dao.db_connection import DBConnection
from dao.player_dao import PlayerDao
from utils.singleton import Singleton


class GameDao(metaclass=Singleton):
    def create(self, game: Game) -> bool:
        res = None

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO game(id_player1, id_player2, game_mode, id_winner, detail) VALUES "
                    "(%(id_player1)s, %(id_player2)s, %(game_mode)s, %(id_winner)s, %(detail)s) "
                    "RETURNING id_game;",
                    {
                        "id_player1": game.player1.id_player,
                        "id_player2": game.player2.id_player,
                        "game_mode": game.game_mode,
                        "id_winner": game.winner.id_player,
                        "detail": game.description,
                    },
                )
                res = cursor.fetchone()

        created = False
        if res:
            game.id_game = res["id_game"]
            created = True

        return created

    def find_by_id(self, id_game: int):
        res = None

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT *                            "
                    "  FROM game                         "
                    " WHERE id_game = %(id_game)s;       ",
                    {"id_game": id_game},
                )
                res = cursor.fetchone()

        if res:
            p1 = PlayerDao().find_by_id(res["id_player1"])
            p2 = PlayerDao().find_by_id(res["id_player2"])
            winner = PlayerDao().find_by_id(res["id_winner"])

            return Game(
                id_game=res["id_game"],
                game_mode=res["game_mode"],
                player1=p1,
                player2=p2,
                winner=winner,
                description=res["detail"],
                timestamp=res["timestamp"],
            )

    def find_all_by_player(self, id_player: int):
        res = None

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT *                            "
                    "  FROM game                         "
                    "  LEFT JOIN player                  "
                    "  ON id_player1 = id_player         "
                    "  OR id_player2 = id_player         "
                    "  WHERE id_player1 = %(id_player)s  "
                    "  OR id_player2 = %(id_player)s;    ",
                    {"id_player": id_player},
                )
                res = cursor.fetchall()

        if res:
            games = []
            for g in res:
                p1 = PlayerDao().find_by_id(g["id_player1"])
                p2 = PlayerDao().find_by_id(g["id_player2"])
                winner = PlayerDao().find_by_id(g["id_winner"])

                games.append(
                    Game(
                        id_game=g["id_game"],
                        game_mode=g["game_mode"],
                        player1=p1,
                        player2=p2,
                        winner=winner,
                        description=g["detail"],
                        timestamp=g["timestamp"],
                    )
                )
            return games
