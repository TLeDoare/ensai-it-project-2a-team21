from datetime import datetime

from business_object.game import Game
from business_object.player import Player

p1 = Player("bonjour", 1200, "a@e;?Fr")
p2 = Player("bonjour2", 12000, "a@e;?Fr")
g = Game(p1, p2, "dice", p1, "partie de l'année", datetime.now())
print(g)
