
import requests
import pandas as pd

class tableau_data:

    def __init__(self, gameweek):
        self.gameweek = gameweek

        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()

        columns = ["code", "first_name", "second_name", "event_points", "element_type", "team", "in_dreamteam", "total_points", "value_season"]
        self.elements = pd.DataFrame(json['elements'])[columns]
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
        postion_limit = {"Defender": 5, "Midfielder": 5, "Forward": 3}
        for _, player in topPlayers.iterrows():
            if (dreamteam.team == player.team).sum() >= 3 or (dreamteam.position == player.position).sum() >= postion_limit[player.position]:
                continue
            dreamteam = dreamteam.append(player)
            if dreamteam.shape[0] == 11:
                break

        print(dreamteam)

        # Add column to main DataFrame
        self.elements["gw_dreamteam"] = self.elements.code.isin(dreamteam.code)


    def write_data(self):
        self.elements.to_csv("data/gameweek_{}.csv".format(self.gameweek), index = False, sep = ";")
