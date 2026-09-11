from client.game_client import GameClient
from utils.env_variables import display_values, load_environment_variables
from utils.log_utils import initialize_logs

# Initialization
initialize_logs("Webservice")

load_environment_variables()
display_values()

games = (GameClient()).get_games()
print(f"{len(games)} games loaded:")
for g in games:
    print(f"- {g}")
