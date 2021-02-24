
import requests
import pandas as pd
import numpy as np

class fpl:

    def __init__(self):
        # get elements info
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()
        self.elements = pd.DataFrame(json['elements'])[["element_type", "first_name", "second_name", "id", "team","value_season", "chance_of_playing_next_round", "chance_of_playing_this_round"]].set_index("id")

        elements_types = pd.DataFrame(json['element_types'])[["id", "singular_name"]].set_index("id")
        self.elements["position"] = self.elements.element_type.map(elements_types.singular_name)

        teams = pd.DataFrame(json['teams'])[["id", "name"]].set_index("id")
        self.elements["team"] = self.elements.team.map(teams.name)

    def get_team(self, file):
        pass

    def suggest_transfer(self):
        pass

    def make_transfer(self, player):
        pass
