import pickle
import requests
import pandas as pd

url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
r = requests.get(url)
json = r.json()
elements = pd.DataFrame(json['elements'])[["element_type", "first_name", "second_name", "id", "team", "value_season", "total_points", "web_name"]].set_index("id")
elements["value_season"] = elements.value_season.astype(float)
elements["total_points"] = elements.total_points.astype(int)
elements["cost"] = elements.total_points / elements.value_season

elements_types = pd.DataFrame(json['element_types'])[["id", "singular_name"]].set_index("id")
elements["position"] = elements.element_type.map(elements_types.singular_name)
elements.drop(columns = "element_type", inplace = True)

teams = pd.DataFrame(json['teams'])[["id", "name"]].set_index("id")
elements["team"] = elements.team.map(teams.name)

team_players = ["Martínez", "Johnstone", "Mings", "Dallas", "Justin", "Stones", "Bednarek", "Grealish", "Salah", "Fernandes", "Son", "Soucek", "Bamford", "Brewster", "Kane"]

team = elements.loc[elements.web_name.isin(team_players)]
print(team.head(15))
