
import requests
import pandas as pd

from datetime import datetime


url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
r = requests.get(url)
json = r.json()

elements = pd.DataFrame(json['elements'])
elements["value_season"] = elements.value_season.astype(float)
elements["total_points"] = elements.total_points.astype(int)
elements["cost"] = elements.total_points / elements.value_season

elements_types = pd.DataFrame(json['element_types'])[["id", "singular_name"]].set_index("id")
elements["position"] = elements.element_type.map(elements_types.singular_name)
elements.drop(columns = "element_type", inplace = True)

teams = pd.DataFrame(json['teams'])[["id", "name"]].set_index("id")
elements["team"] = elements.team.map(teams.name)

elements.to_csv("data/tableau_{}.csv".format(datetime.now().strftime("%Y%m%d")), index = False, sep = ";")
