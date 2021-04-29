
import argparse
from fpl import fpl

# Arguments
arg_parser = argparse.ArgumentParser(description='Fantasy Premier League Tools.')
# Data for dashboards
arg_parser.add_argument('--gameweek_data', action='store_true', default=False,
    help='Generate live gameweek data for dashboards.')
arg_parser.add_argument('--season_data', action='store_true', default=False,
    help='Generate past gameweeks data for dashboards.')
# FPL suggestions
arg_parser.add_argument('--suggest_transfer', action='store_true', default=False,
    help='Suggest transfer for the specified team')
arg_parser.add_argument('-team', default=None, help='Team used for suggestions.')
arg_parser.add_argument('-model', default="basic_random_forest",
    help='Model used for predictions on transfer sugestion - Default: Basic Random Forest.')

if __name__ == "__main__":

    # Parse Arguments
    argv = arg_parser.parse_args()
    print(argv)

    # Start module
    fpl_ = fpl()

    if argv.gameweek_data:
        fpl_.generate_gameweek_data()
    if argv.season_data:
        fpl_.generate_season_data()
    if argv.suggest_transfer and not argv.team is None:
        fpl_.suggest_transfer(argv.team, argv.model)
