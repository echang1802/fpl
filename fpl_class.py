
import pickle
import requests
import pandas as pd

class fpl_class:

    def __init__(self):
        # get elements info
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()
        self.elements = pd.DataFrame(json['elements'])[["code", "element_type", "first_name", "second_name", "team", "value_season", "total_points"]]
        self.elements["value_season"] = self.elements.value_season.astype(float)
        self.elements["total_points"] = self.elements.total_points.astype(int)
        self.elements["cost"] = self.elements.total_points / self.elements.value_season

        elements_types = pd.DataFrame(json['element_types'])[["id", "singular_name"]].set_index("id")
        self.elements["position"] = self.elements.element_type.map(elements_types.singular_name)
        self.elements.drop(columns = "element_type", inplace = True)

        teams = pd.DataFrame(json['teams'])[["id", "name"]].set_index("id")
        self.elements["team"] = self.elements.team.map(teams.name)

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

    def suggest_transfer(self):
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
