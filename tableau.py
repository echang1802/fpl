
from sys import argv
from tableau_data_class import tableau_data

data = tableau_data(argv[1])

data.generate_gameweek_dreamteam()

data.write_data()
