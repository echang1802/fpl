
from sys import argv
from fpl_class import fpl_class

if __name__ == "__main__":

    fpl = fpl_class()

    fpl.get_team("data/{}".format(argv[1]))

    fpl.suggest_transfer()

    #fpl.choose_transfer()

    fpl.make_transfer(input("\nMake transfer?\n"))
