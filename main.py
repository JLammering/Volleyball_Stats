import math
import os
import re
import time
import logging
from typing import Dict

import pandas as pd

# Configure the logging settings
logging.basicConfig(level=logging.INFO)  # Set the logging level (e.g., INFO, DEBUG)

# Create a logger
logger = logging.getLogger("Volleyball_stats")

class SetResult:
    def __init__(self, set: int, home_points: int, away_points: int):
        logger.info(f"Set Result {set} {home_points}:{away_points}")
        if set < 1 or set > 5:
            raise ValueError("Set has to be between 1 and 5")
        self.set = set
        if home_points == away_points:
            raise ValueError(f"points cant be equal in set {set}: {home_points}:{away_points}")
        elif set < 5 and home_points < 25 and away_points < 25:
            raise ValueError("somebody has to have over 25 points")
        elif set == 5 and home_points < 15 and away_points < 15:
            raise ValueError("somebody has to have over 15 points")
        self.home_points = home_points
        self.away_points = away_points
        self.players = {}
    

    def getPointsPlayed(self):
        return self.home_points + self.away_points
    

    def addPlayer(self, number: int, exchange, change, change_back):
        if isinstance(change_back, str):
            self.players[number] = Player(number, "0:0", change, change_back, f"{self.home_points}:{self.away_points}")
            self.players[exchange] = Player(exchange, change, change_back)
        elif isinstance(change, str):
            self.players[number] = Player(number, "0:0", change)
            self.players[exchange] = Player(exchange, change, f"{self.home_points}:{self.away_points}")
        else:#starting player plays till end
            self.players[number] = Player(number, "0:0", f"{self.home_points}:{self.away_points}")


class GameResult:
    def __init__(self, sets: Dict[int, SetResult], home_name: str, away_name: str):
        self.sets = sets
        self.home_team_name = home_name
        self.away_team_name = away_name
    
    def getPointsPlayed(self):
        result = 0
        for key, set in self.sets.items():
            result += set.getPointsPlayed()
        return result
            


class Player:
    def __init__(self, number: int, start_score: str, end_score: str, second_start_score: str=None, second_end_score: str=None) -> None:
        self.number = int(number)
        self.start_score = start_score.split(':')
        self.end_score = end_score.split(':')
        self.second_start_score = second_start_score.split(':') if second_start_score != None else None
        self.second_end_score = second_end_score.split(':') if second_end_score != None else None


    def getPlusMinus(self):
        own_points = int(self.end_score[0]) - int(self.start_score[0])
        other_points = int(self.end_score[1]) - int(self.start_score[1])
        if self.second_start_score != None:
            own_points += int(self.second_end_score[0]) - int(self.second_start_score[0])
            other_points += int(self.second_end_score[1]) - int(self.second_start_score[1])
        return own_points - other_points


    def getPointsPlayed(self):
        own_points = int(self.end_score[0]) - int(self.start_score[0])
        other_points = int(self.end_score[1]) - int(self.start_score[1])
        if self.second_start_score != None:
            own_points += int(self.second_end_score[0]) - int(self.second_start_score[0])
            other_points += int(self.second_end_score[1]) - int(self.second_start_score[1])
        return own_points + other_points


def getGameInfo(directory_path):

    # List all files in the directory
    files = os.listdir(directory_path)

    # Specify the pattern for the files you're interested in
    game_pattern = '.*-game.csv'
    player_pattern = '.*-players.csv'

    # Filter files based on the pattern
    game_files = [file for file in files if re.match(game_pattern, file)]
    player_files = [file for file in files if re.match(player_pattern, file)]
    game_files.sort()
    player_files.sort()

    results = {}

    for i, game_file in enumerate(game_files):

        teams = game_file.split('-')

        # Extract team names
        home_team = teams[0]
        away_team = teams[1]
        df_game = pd.read_csv(f"{directory_path}/{game_file}", delimiter=';', skipinitialspace=True)
        df_players = pd.read_csv(f"{directory_path}/{player_files[i]}", delimiter=';', skipinitialspace=True)

        sets: Dict[int, SetResult] = {}
        for index, row in df_game.iterrows():
            # Access individual columns using column names
            set = row['Set']
            home_points = row['Home']
            away_points = row['Away']
            sets[set] = SetResult(set, home_points, away_points)
        for index, row in df_players.iterrows():
            set = row['Set']
            number = row['Player']
            exchange = row['Player New']
            change = row['Change']
            change_back = row['Change Back']
            sets[set].addPlayer(number, exchange, change, change_back)

        results[f"{home_team}-{away_team}"] = GameResult(sets, home_team, away_team)

    return results


def tabeliseResults(results: Dict[str, SetResult]):
    data = []
    total_game = {}
    for game_name, result in results.items():
        data.append([game_name])
        for set_number, set in result.sets.items():
            data.append([f"Satz: {set_number}. Ergebnis: {set.home_points}:{set.away_points}. Gespielte Punkte: {set.getPointsPlayed()}"])
            data.append(["Nummer"," PlusMinus", "Gespielte Punkte", "Anteil am Satz"])
            for key, player in set.players.items():
                data.append([f"{player.number}", f"{player.getPlusMinus()}",f"{player.getPointsPlayed()}", f"{(player.getPointsPlayed()/set.getPointsPlayed())*100:.0f}%"])
                if player.number not in total_game:
                    total_game[player.number] = [player.getPlusMinus(), player.getPointsPlayed()]
                else:
                    total_game[player.number][0] += player.getPlusMinus()
                    total_game[player.number][1] += player.getPointsPlayed()
        data.append([f"Ganzes Spiel. Gespielte Punkte: {result.getPointsPlayed()}"])
        data.append(["Nummer"," PlusMinus", "Gespielte Punkte", "Anteil am Spiel"])
        for number, stat in total_game.items():
            data.append([f"{number}", f"{stat[0]}", f"{stat[1]}", f"{(stat[1]/result.getPointsPlayed())*100:.0f}%"])
    return data
            

def makePdf(data):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    # Create a PDF
    pdf_filename = f"results/{data[0][0]}.pdf"
    document = SimpleDocTemplate(pdf_filename, pagesize=letter)
    table = Table(data)

    # Add style to the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#77AABB'),
        ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1, 1)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#DDDDDD'),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ])

    table.setStyle(style)

    # Build the PDF
    document.build([table])



def main():
    results = getGameInfo("23_24")

    data = tabeliseResults(results)
    makePdf(data)


if __name__ == "__main__":
    main()