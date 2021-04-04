
from sys import argv
from tableau_data_class import tableau_data

if __name__ == '__main__':

    data = tableau_data(argv[1])

    data.get_gameweek_data()

    data.generate_gameweek_dreamteam()

    data.write_gameweek_data()

    # Get and write historical data
    data.get_historical_data()

    data.write_base_historical_data()
