
import pickle
import requests
import pandas as pd
from model_class import model

class fpl_class:

    def __init__(self):
        # get elements info
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()

        self.elements = pd.DataFrame(json['elements'])
        self.elements["value_season"] = self.elements.value_season.astype(float)
        self.elements["total_points"] = self.elements.total_points.astype(int)
        self.elements["cost"] = self.elements.total_points / self.elements.value_season

        elements_types = pd.DataFrame(json['element_types'])[["id", "singular_name"]].set_index("id")
        self.elements["position"] = self.elements.element_type.map(elements_types.singular_name)
        self.elements.drop(columns = "element_type", inplace = True)

        self._teams = pd.DataFrame(json['teams'])[["id", "name"]].set_index("id")
        self.elements["team"] = self.elements.team.map(self._teams.name)

    def _get_gameweek_fixtures(self, gameweek):
        url = "https://fantasy.premierleague.com/api/fixtures/"
        r = requests.get(url.format(id))
        json = r.json()

        self.fixtures = pd.DataFrame(json)[["id", "event", "team_a",  "team_h", "team_h_difficulty", "team_a_difficulty"]].set_index("id")
        self.fixtures["team_a_name"] = self.fixtures.team_a.map(self._teams.name)
        self.fixtures["team_h_name"] = self.fixtures.team_h.map(self._teams.name)

    def _fix_model_df(self, gameweek, delete_match):
        self._elements_for_model = sel.elements.copy()
        self._elements_for_model = self._elements_for_model[["chance_of_playing_next_round","event_points", "minutes", "total_points", "points_per_game", "transfers_in", "transfers_out", "goals_scored", "assists", "clean_sheets", "goals_conceded", "own_goals", "penalties_saved", "penalties_missed", "yellow_cards", "red_cards", "saves", "bonus", "next_match_difficult", "next_match_home"]]
        columns = ["total_points", "transfers_in", "transfers_out", "minutes", "goals_scored", "assists", "goals_conceded", "own_goals", "yellow_cards", "red_cards", "saves", "bonus", "penalties_saved", "penalties_missed", "fixture"]
        url = "https://fantasy.premierleague.com/api/element-summary/{}/"
        #self.elements["team_pos"] = self.elements.team.map(self._teams.position)
        #self.elements["next_match_team_pos"] = 0
        self._elements_for_model["next_match_difficult"] = 0
        self._elements_for_model["next_match_home"] = 0
        fixtures = self.fixtures.loc[self.fixtures.event == gameweek]
        print(fixtures)
        for id, player in self._elements_for_model.iterrows():
            if delete_match:
                r = requests.get(url.format(id))
                json = r.json()

                if type(json) != dict or not "history" in json.keys():
                    continue
                player_info = pd.DataFrame(json['history'])[columns]
                player_info = player_info.loc[player_info.fixture.isin(list(self.fixtures.index[self.fixtures.event == gameweek-1]))]
                for col in columns:
                    if col in player.index:
                        self._elements_for_model.at[id, col] -= player_info[col].sum()
            if player.team in fixtures.team_h.to_list():
                self._elements_for_model.at[id, "next_match_home"] = 1
                local = "h"
            else:
                local = "a"
            fixture = fixtures.loc[fixtures["team_{}".format(local)] == player.team]
            #self.elements[id]["next_match_team_pos"] = fixture["team_{}".format(local)].map(self._teams.position)
            if fixture.shape[0] == 0:
                continue
            self._elements_for_model.at[id, "next_match_difficult"] = fixture["team_{}_difficulty".format(local)]


    def _generate_basic_model_dataset(self, gameweek, delete_match = False):
        self._get_gameweek_fixtures(gameweek)
        self._fix_model_df(gameweek, delete_match)
        # add teams and next match facts
        # Save dataframe
        #self.elements.to_csv("data/elements.csv", index = False, sep = ";")

    def get_team(self, file):
        self.teamFile = file
        with open(self.teamFile, "rb") as file:
            self.team, self.bank = pickle.load(file)

    def _get_banned_teams(self, player):
        teams = self.team.team.value_counts()
        teams[player.team] -= 1
        self.banned_teams = teams.index[teams == 3]

    def _choose_best_transfer(self, transfers):
        if len(transfers) == 0:
            self.transfer = {}
            print("No transfer is suggested")
            return
        improvement = 0
        for transfer in transfers.values():
            if transfer["improvement"] > improvement:
                improvement = transfer["improvement"]
                self.transfer = transfer
        print("-----> Player Out <-----")
        print(self.transfer["out"].first_name, self.transfer["out"].second_name)
        print("-----> Player In <-----")
        print(self.transfer["in"].first_name.values[0], self.transfer["in"].second_name.values[0])
        print("-----> Improvement <-----")
        print(self.transfer["improvement"])

    def _naive_model(self):
        transfers = {}
        for pos in self.team.position.unique():
            transfers[pos] = {"out": None, "in": None, "improvement": 0}
            for _, player_out in self.team.loc[self.team.position == pos].iterrows():
                self._get_banned_teams(player_out)
                candidates = (self.elements.position == pos) & (self.elements.value_season >= player_out.value_season) & (self.elements.cost <= (player_out.cost + self.bank)) & (~self.elements.code.isin(self.team.code)) & (~self.elements.team.isin(self.banned_teams))
                if sum(candidates) == 0:
                    continue
                candidates = self.elements.loc[candidates]
                candidates["cost"] *= -1
                candidates = candidates.sort_values(by = ["value_season", "cost"], ascending = False).head(1)
                improvement = int(candidates.value_season - player_out.value_season)
                if transfers[pos]["in"] is None or improvement > transfers[pos]["improvement"]:
                    transfers[pos] = {"out": player_out, "in": candidates, "improvement": int(improvement)}
        self._choose_best_transfer(transfers)

    def _load_model(self, model, gameweek):
        with open("models/", "rb") as file:
            model = pickle.load(file)
        self._generate_basic_model_dataset(gameweek)
        model.init_data(self._elements_for_model)
        model.predict()
        self._elements_For_model = self._elements_For_model.join(model.get_predictions())

    def suggest_transfer(self, model, parameters):
        if model == "naive":
            self._naive_model()
        elif model == "basic":
            self._basic_ml(parameters["gameweek"])


    def choose_transfer(self):
        change_transfer = input("\nChoose other transfer?\n")
        if change_transfer.lower() != "yes":
            return

        ready = False
        while not ready:
            search_by = input("\nSearch player by:\n")
            value = input("\nSearch by {}:\n".format(search_by))
            print(self.elements.loc[self.elements[search_by] == value])
            code = input("\nPlayer code:\n")
            if not (code in self.elements.code):
                continue
            print("\nYour team is:")
            print(self.team)
            player_out = int(input("\nPlayer out code:\n"))
            try:
                ready = self.elements.loc[self.elements.code == code].cost.values[0] >= (self.team.loc[self.team.code == player_out].cost.values[0] + self.bank)
            except:
                ready = False

        self.transfer = {
            "out" : self.team.loc[self.team.code == player_out],
            "in" : self.elements.loc[self.elements.code == code],
            "improvement" : self.team.loc[self.team.code == player_out].value_season.values[0] - self.elements.loc[self.elements.code == code].value_season.values[0]
        }
        print(self.transfer)

    def make_transfer(self, proceed):
        if proceed.lower() != "yes":
            return

        self.bank += (self.transfer["out"].cost + self.transfer["in"].cost).values[0]
        self.team = self.team.loc[self.team.code != self.transfer["out"].code].append(self.transfer["in"])
        with open(self.teamFile, "wb") as file:
            pickle.dump((self.team, self.bank), file)

        print("Transfer made")
        print("Money left in bank: ", self.bank)
        print("Improvement: ", self.transfer["improvement"])
