from business_object.game_mode.coin_flip_mode import CoinFlipMode
from business_object.game_mode.dice_mode import DiceMode
from business_object.game_mode.game_mode import GameMode


class GameModeFactory:
    @classmethod
    def get_mode(cls, game_mode: str) -> GameMode:
        """
        Returns the corresponding GameMode object
        Args:
            game_mode (str): The indentifier of the game mode (e.g., 'coinflip')
        Returns:
            GameMode: An instance of a class implementing GameMode
        Raises:
            ValueError: If the resquested game_mode is not supported
        """
        if game_mode == "dice":
            return DiceMode
        elif game_mode == "coinflip":
            return CoinFlipMode
        else:
            raise ValueError("Error: game_mode must identify a game mode (e.g. 'coinflip', 'dice', ...)")
