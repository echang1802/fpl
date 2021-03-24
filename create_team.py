import pickle
import requests
import pandas as pd

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

team_players = [98980, 218023, 177815, 153366, 87873, 118748, 59859, 97299, 171314, 141746, 195473, 78830, 85971, 101982, 55459]
bank = 0.1

team = elements.loc[elements.code.isin(team_players)]
print(team)

with open("data/mokaFC", "wb") as file:
    pickle.dump((team, bank), file)
