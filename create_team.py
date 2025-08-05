import pickle
import requests
import pandas as pd
from sys import argv

url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
r = requests.get(url)
json = r.json()
elements = pd.DataFrame(json['elements'])[["code", "element_type", "first_name", "second_name", "team", "value_season", "total_points"]]
elements["value_season"] = elements.value_season.astype(float)
elements["total_points"] = elements.total_points.astype(int)
elements["cost"] = elements.total_points / elements.value_season

elements_types = pd.DataFrame(json['element_types'])[["id", "singular_name"]].set_index("id")
elements["position"] = elements.element_type.map(elements_types.singular_name)
elements.drop(columns = "element_type", inplace = True)

teams = pd.DataFrame(json['teams'])[["id", "name"]].set_index("id")
elements["team"] = elements.team.map(teams.name)

team_players = [85633, 111234, 214590, 432830, 227444, 247348, 209036, 118748, 153133, 430871, 446008, 102057, 178186, 247412, 232185]
bank = 0.0

team = elements.loc[elements.code.isin(team_players)]
print(team)

with open("teams/{}".format(argv[1]), "wb") as file:
    pickle.dump((team, bank), file)
