
import pandas as pd

class dashboard_data:

    def __init__(self, data_type, fpl_class):
        if data_type == "gameweek":
            self._get_gameweek_data(fpl_class)
        elif data_type == "season":
            self._get_season_data(fpl_class)

    def _get_gameweek_data(self, fpl_class):
        columns = ["code", "first_name", "second_name", "event_points", "element_type", "team", "in_dreamteam", "cost"]
        self.data = fpl_class.data[columns]

        self.data["position"] = self.data.element_type.map(fpl_class.element_types.singular_name)
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

            fixtures =  pd.DataFrame(json['history'])[main_columns].set_index("fixture")
            fixtures = fixtures.join(fpl_class.fixtures[fixture_columns])
            fixtures.sort_values(by = "kickoff_time", inplace = True)
            fixtures["fixture"] = range(fixtures.shape[0])
            fixtures["player_id"] = id
            fixtures = fixtures.set_index("player_id").join(self.elements[elements_columns])
            self.data = self.data.append(fixtures)

        self.data["position"] = self.data.element_type.map(fpl_class.element_types.singular_name)
        self.data["team"] = self.data.team.map(fpl_class.clubs.name)
        self.data.drop(columns = ["element_type"], inplace = True)
