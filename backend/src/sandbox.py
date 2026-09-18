# uv run --project backend python backend/src/sandbox.py

from dao.game_dao import GameDao
from utils.env_variables import load_environment_variables

load_environment_variables()  # Required to load the variables needed (env) to connect to the database

# p1 = PlayerService().find_by_id(3)
# p2 = PlayerService().find_by_id(5)
# game = Game(
#     player1=p1, player2=p2, game_mode="dice", winner=p1, description="aaa", timestamp=datetime.now()
# )

# GameDao().create(game)
# print(game.id_game)
# game2 = GameDao().find_by_id(game.id_game)
# print(game)
# print(game2)

for g in GameDao().find_all_by_player(4):
    print(g)
