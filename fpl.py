
# FPL Class v2

# Libraries
import pickle
import requests
import pandas as pd

# Sub modules
from dashboard_data_class import dashboard_data
from model_class import model

# Main module

class fpl:

    def __init__(self):
        json = self._api_call("https://fantasy.premierleague.com/api/bootstrap-static/")
        self.elements = pd.DataFrame(json['elements']).set_index("id")
        self.elements["value_season"] = self.elements.value_season.astype(float)
        self.elements["total_points"] = self.elements.total_points.astype(int)
        self.elements["cost"] = self.elements.total_points / self.elements.value_season

        self.elements_type = pd.DataFrame(json['element_types']).set_index("id")

        self.clubs = pd.DataFrame(json['teams']).set_index("id")

        json = self._api_call("https://fantasy.premierleague.com/api/fixtures/")
        self.fixtures = pd.DataFrame(json).set_index("id")

    def _api_call(self, url):
        r = requests.get(url)
        json = r.json()
        return json

    def _get_gameweek(self):
        self._gameweek = self.fixtures.loc[~self.fixtures.finished].event.min()

    def generate_gameweek_data(self):
        self._get_gameweek()
        dashboard = dashboard_data("gameweek", self)
        dashboard.generate_gameweek_dreamteam()
        dashboard.save(self._gameweek)

    def generate_season_data(self):
        self._get_gameweek()
        dashboard = dashboard_data("season", self)
        dashboard.save(self._gameweek)

    def _read_team(self, club_name):
        import ast
        with open("teams/{}".format(club_name), "r") as file:
            team_elements = file.read()
            team_elements = ast.literal_eval(team_elements)

        self.team = pd.DataFrame()
        self.bank = team_elements["bank"]
        team_elements.pop("bank")
        for club, players in team_elements.items():
            for player in players:
                pos = (self.elements.web_name == player) & \
                    (self.elements.team == self.clubs.index[self.clubs.name == club][0])
                self.team = self.team.append(self.elements.loc[pos])

    def _predict_gameweek_scores(self, model_name):
        with open("models/{}".format(model_name)) as file:
            model = pickle.load(file)

        model.init_data(self.elements)
        self.elements["pred"] = model.predict()

    def _suggest_transfer(self):
        self.transfer = {
            "out" : None,
            "in" : None,
            "improvement" : 0
        }
        for position in self.team.position.unique():
            self.team = self.team.join(self.elements["pred"], how = "inner")
            for p_id, player in self.team.loc[team.position == position].iterrows():
                banned_teams = self._get_banned_teams(player)
                candidates = (self.elements.position == position) & \
                    (self.elements.pred >= player.pred) & \
                    (self.elements.cost <= (player.cost + self.bank)) & \
                    (~self.elements.code.isin(self.team.code)) & \
                    (~self.elements.team.isin(banned_teams))
                if sum(candidates) == 0:
                    continue
                candidates = self.elements.loc[candidates]
                candidates["cost"] *= -1
                candidates = candidates.sort_values(by = ["pred", "cost"], ascending = False).head(1)
                improvement = int(candidates.pred - player.pred)
                if improvement > self.transfer["improvement"]:
                    self.transfer = {
                        "out": player,
                        "in": candidates,
                        "improvement": improvement
                    }
        print("-----> Player Out <-----")
        print(self.transfer["out"].first_name, self.transfer["out"].second_name)
        print("-----> Player In <-----")
        print(self.transfer["in"].first_name.values[0], self.transfer["in"].second_name.values[0])
        print("-----> Improvement <-----")
        print(self.transfer["improvement"])


    def _save_transfer(self, club_name):
        self.team.drop(self.transfer["out"].name, inplace = True)
        self.team = self.team.append(self.transfer["in"])
        self.bank = self.bank + self.transfer["out"].cost - self.transfer["in"].cost
        team = {"bank" : self.bank}
        for club_id in self.team.team.iterrows():
            club = self.clubs[club_id]
            team[club] = []
            for p_id, player in self.team.loc[self.team.team == club].iterrows():
                team[club].append(player.web_name)

        with open("clubs/{}".format(club_name), "rb") as file:
            file.write(team)

    def suggest_transfer(self, club_name, model_name):
        self._read_team(club_name)
        self._predict_gameweek_scores(model_name)
        self._suggest_transfer()
        self._save_transfer()
