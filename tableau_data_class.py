
import requests
import pandas as pd

class tableau_data:

    def __init__(self, gameweek):
        self.gameweek = gameweek

    def get_gameweek_data(self):

        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()

        columns = ["id", "code", "first_name", "second_name", "event_points", "element_type", "team", "in_dreamteam", "total_points", "value_season"]
        self.elements = pd.DataFrame(json['elements'])[columns].set_index("id")
        self.elements["value_season"] = self.elements.value_season.astype(float)
        self.elements["total_points"] = self.elements.total_points.astype(int)
        self.elements["cost"] = self.elements.total_points / self.elements.value_season
        self.elements.drop(columns = ["value_season", "total_points"], inplace = True)

        elements_types = pd.DataFrame(json['element_types'])[["id", "singular_name"]].set_index("id")
        self.elements["position"] = self.elements.element_type.map(elements_types.singular_name)
        self.elements.drop(columns = "element_type", inplace = True)

        teams = pd.DataFrame(json['teams'])[["id", "name"]].set_index("id")
        self.elements["team"] = self.elements.team.map(teams.name)

    def _get_top_players_by_postition(self, position):
        topPlayers = self.elements.loc[self.elements.position == position]
        topPlayers["cost"] *= -1
        return topPlayers.sort_values(by = ["event_points", "cost"], ascending = False).head(10).reset_index(drop = True)

    def _validate_team(self, dreamteam):
        if dreamteam.shape[0] < 11:
            return False
        if (dreamteam.position == "Defender").sum() < 3:
            pos = dreamteam.loc[dreamteam.position.isin(["Midfielder", "Forward"])].event_points.idxmin()
            dreamteam.drop(pos, inplace = True)
            return False
        if (dreamteam.position == "Midfielder").sum() < 2:
            pos = dreamteam.loc[dreamteam.position.isin(["Defender", "Forward"])].event_points.idxmin()
            dreamteam.drop(pos, inplace = True)
            return False
        if (dreamteam.position == "Forward").sum() < 1:
            pos = dreamteam.loc[dreamteam.position.isin(["Defender", "Midfielder"])].event_points.idxmin()
            dreamteam.drop(pos, inplace = True)
            return False
        return True

    def generate_gameweek_dreamteam(self):
        # Goalkeeper
        dreamteam = self._get_top_players_by_postition("Goalkeeper").head(1)

        # Best minimal quantity of player by each position
        positions = ["Forward", "Midfielder", "Defender"]
        topPlayers = pd.DataFrame()
        for aux in range(1,4):
            topPositionPlayers = self._get_top_players_by_postition(positions[aux - 1])
            topPlayers = topPlayers.append(topPositionPlayers)

        # Fill remaining spots
        topPlayers.sort_values(by = ["event_points", "cost"], ascending = False, inplace = True)
        topPlayers.reset_index(drop = True, inplace = True)
        postion_limit = {"Defender": 5, "Midfielder": 5, "Forward": 3}
        for _, player in topPlayers.iterrows():
            if (dreamteam.team == player.team).sum() >= 3 or (dreamteam.position == player.position).sum() >= postion_limit[player.position]:
                continue
            dreamteam = dreamteam.append(player)
            if self._validate_team(dreamteam):
                break

        print(dreamteam)

        # Add column to main DataFrame
        self.elements["gw_dreamteam"] = self.elements.code.isin(dreamteam.code)

    def write_gameweek_data(self):
        self.elements.to_csv("data/gameweek_{}.csv".format(self.gameweek), index = False, sep = ";")

    def _get_fixtures_data(self):
        url = "https://fantasy.premierleague.com/api/fixtures/"
        r = requests.get(url.format(id))
        json = r.json()

        self.fixtures = pd.DataFrame(json)[["id", "event"]].set_index("id")
        print(self.fixtures.head())

    def get_historical_data(self):
        self._get_fixtures_data()
        self.history = pd.DataFrame()
        columns = ["fixture", "total_points"]
        url = " https://fantasy.premierleague.com/api/element-summary/{}/"
        for id, player in self.elements.iterrows():
            r = requests.get(url.format(id))
            json = r.json()

            fixtures =  pd.DataFrame(json['history'])[columns].set_index("fixture")
            fixtures = fixtures.join(self.fixtures)
            fixtures["player_id"] = id
            self.history = self.history.append(fixtures)

    def write_base_historical_data(self):
        self.history.to_csv("data/history.csv", index = False, sep = ";")
        self.elements[["first_name", "second_name", "position", "team"]].to_csv("data/players.csv", index = True, sep = ";")
