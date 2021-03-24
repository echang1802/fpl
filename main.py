
from fpl_class import fpl_class

fpl = fpl_class()

fpl.get_team("data/mokaFC")

fpl.suggest_transfer()

#fpl.choose_transfer()

fpl.make_transfer(input("\nMake transfer?\n"))
