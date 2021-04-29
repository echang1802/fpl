
import pandas as pd

class dashboard_data:

    def __init__(self, data_type, fpl_class):
        self._data_type = data_type
        if data_type == "gameweek":
            self._get_gameweek_data(fpl_class)
        elif data_type == "season":
            self._get_season_data(fpl_class)

    def _get_gameweek_data(self, fpl_class):
        columns = ["code", "first_name", "second_name", "event_points", "element_type", "team", "in_dreamteam", "cost"]
        self.data = fpl_class.elements[columns]

        self.data["position"] = self.data.element_type.map(fpl_class.elements_type.singular_name)
        self.data["team"] = self.data.team.map(fpl_class.clubs.name)
        self.data.drop(columns = ["element_type"], inplace = True)

    def _get_season_data(self, fpl_class):
        main_columns = ["total_points", "transfers_in", "transfers_out", "minutes", "goals_scored", "assists", "goals_conceded", "own_goals", "yellow_cards", "red_cards", "saves", "bonus", "fixture"]
        fixture_columns = ["event", "kickoff_time", "team_a", "team_a_score", "team_h", "team_h_score", "team_h_difficulty", "team_a_difficulty"]
        elements_columns = ["first_name", "second_name", "team", "element_type","in_dreamteam", "cost"]
        url = " https://fantasy.premierleague.com/api/element-summary/{}/"
        self.data = pd.DataFrame()
        for p_id, player in fpl_class.elements.iterrows():
            json = fpl_class._api_call(url.format(p_id))

            if type(json) != dict or not "history" in json.keys():
                continue
            fixtures =  pd.DataFrame(json['history'])[main_columns].set_index("fixture")
            fixtures = fixtures.join(fpl_class.fixtures[fixture_columns])
            fixtures.sort_values(by = "kickoff_time", inplace = True)
            fixtures["fixture"] = range(fixtures.shape[0])
            fixtures["player_id"] = p_id
            self.data = self.data.append(fixtures)

        self.data = self.data.set_index("player_id").join(fpl_class.elements[elements_columns], how = "inner")
        self.data["position"] = self.data.element_type.map(fpl_class.elements_type.singular_name)
        self.data["team"] = self.data.team.map(fpl_class.clubs.name)
        self.data["team_a"] = self.data.team_a.map(fpl_class.clubs.name)
        self.data["team_h"] = self.data.team_h.map(fpl_class.clubs.name)
        self.data.drop(columns = ["element_type"], inplace = True)

    def _get_top_players_by_postition(self, position):
        topPlayers = self.data.loc[self.data.position == position]
        topPlayers["cost"] *= -1
        return topPlayers.sort_values(by = ["event_points", "cost"], ascending = False).head(10).reset_index(drop = True)

    def _validate_team(self, dreamteam):
        if dreamteam.shape[0] < 11:
            return False
        min_position_limit = {
            "Defender" : 3,
            "Midfielder" : 2,
            "Forward" : 1
        }
        for position, limit in min_position_limit.items():
            if (dreamteam.position == position).sum() < limit:
                lower_value_player = dreamteam.loc[dreamteam.position != position].sort_values(by = ["event_points", "cost"]).index[0]
                dreamteam.drop(lower_value_player, inplace = True)
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

        # Add column to main DataFrame
        self.data["gw_dreamteam"] = self.data.code.isin(dreamteam.code)

    def save(self, gameweek):
        self.data.to_csv("data/{}_{}.csv".format(self._data_type, gameweek), index = False, sep = ";")
