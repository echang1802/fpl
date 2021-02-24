
import pickle
import requests
import pandas as pd

class fpl_class:

    def __init__(self):
        # get elements info
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()
        self.elements = pd.DataFrame(json['elements'])[["element_type", "first_name", "second_name", "id", "team", "value_season", "total_points"]].set_index("id")
        self.elements["value_season"] = self.elements.value_season.astype(float)
        self.elements["total_points"] = self.elements.total_points.astype(int)
        self.elements["cost"] = self.elements.total_points / self.elements.value_season

        elements_types = pd.DataFrame(json['element_types'])[["id", "singular_name"]].set_index("id")
        self.elements["position"] = self.elements.element_type.map(elements_types.singular_name)
        self.elements.drop(columns = "element_type", inplace = True)

        teams = pd.DataFrame(json['teams'])[["id", "name"]].set_index("id")
        self.elements["team"] = self.elements.team.map(teams.name)

    def get_team(self, file):
        with open(file, "rb"):
            self.team = pickle.load(file)

    def suggest_transfer(self):
        transfers = {}
        for pos in self.team.position.unique():
            transfers[pos] = {"out": None, "in": None, "improvement": 0}
            for player_out in self.team.loc[self.team.position == pos]:
                candidates = (self.elements.position == pos) & (self.elements.value_season >= player_out.value_season) & (self.elements.cost <= player_out.cost)
                if sum(candidates) == 0:
                    continue
                candidates = self.elements.loc[candidates].sort_values(by = "value_season", ascending = False).head(1)
                improvement = candidates.value_season - player_out.value_season
                if transfers[pos]["in"] is None or improvement > transfers[pos]["improvement"]:
                    transfers[pos] = {"out": player_out, "in": player_in, "improvement": improvement}
        print(transfers)




    def make_transfer(self, player):
        pass
