import os
import re
import time
import logging

import pandas as pd

# Configure the logging settings
logging.basicConfig(level=logging.INFO)  # Set the logging level (e.g., INFO, DEBUG)

# Create a logger
logger = logging.getLogger("Volleyball_stats")

class SetResult:
    def __init__(self, set, home_team, away_team):
        logger.info(f"Set Result {set} {home_team}:{away_team}")
        if set < 1 or set > 5:
            raise ValueError("Set has to be between 1 and 5")
        self.set = set
        if home_team == away_team:
            raise ValueError(f"points cant be equal in set {set}: {home_team}:{away_team}")
        elif set < 5 and home_team < 25 and away_team < 25:
            raise ValueError("somebody has to have over 25 points")
        elif set == 5 and home_team < 15 and away_team < 15:
            raise ValueError("somebody has to have over 15 points")
        self.home_team = home_team
        self.away_team = away_team

class GameResult:
    def __init__(self, sets, home_name, away_name):
        self.sets = sets
        self.home_team_name = home_name
        self.away_team_name = away_name
            



def getGameInfo(directory_path):

    # List all files in the directory
    files = os.listdir(directory_path)

    # Specify the pattern for the files you're interested in
    file_pattern = '.*-game.csv'

    # Filter files based on the pattern
    game_files = [file for file in files if re.match(file_pattern, file)]

    result = {}

    for game_file in game_files:

        teams = game_file.split('-')

        # Extract team names
        home_team = teams[0]
        away_team = teams[1]
        df = pd.read_csv(f"{directory_path}/{game_file}", delimiter=';', skipinitialspace=True)

        sets = {}
        for index, row in df.iterrows():
            # Access individual columns using column names
            set = row['Set']
            home_points = row[home_team]
            away_points = row[away_team]
            sets[set] = SetResult(set, home_points, away_points)
        result[f"{home_team}-{away_team}"] = GameResult(sets, home_team, away_team)

    return result



def main():
    result = getGameInfo("23_24")

    print (result)


if __name__ == "__main__":
    main()