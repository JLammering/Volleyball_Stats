import csv
import math
import os
import re
import time
import logging
from typing import Dict

import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

# Configure the logging settings
logging.basicConfig(level=logging.INFO)  # Set the logging level (e.g., INFO, DEBUG)

# Create a logger
logger = logging.getLogger("Volleyball_stats")

class SetResult:
    def __init__(self, set: int, home_points: int, away_points: int):
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
    

    def addPlayer(self, number: int, exchange, change, change_back, is_home: bool, names):
        end_result = f"{self.home_points}:{self.away_points}" if is_home else f"{self.away_points}:{self.home_points}"

        if isinstance(change_back, str):
            self.players[number] = Player(number, names[number], "0:0", change, change_back, end_result)
            self.players[exchange] = Player(exchange, names[exchange], change, change_back)
        elif isinstance(change, str):
            self.players[number] = Player(number, names[number], "0:0", change)
            self.players[exchange] = Player(exchange, names[exchange], change, end_result)
        else:#starting player plays till end
            self.players[number] = Player(number, names[number], "0:0", end_result)


class GameResult:
    def __init__(self, sets: Dict[int, SetResult], home_name: str, away_name: str, season: str, team: str):
        self.sets = sets
        self.home_team_name = home_name
        self.away_team_name = away_name
        self.season = season
        self.team = team
    
    def getPointsPlayed(self):
        result = 0
        for key, set in self.sets.items():
            result += set.getPointsPlayed()
        return result
            
def listToScore(list):
    return f"{list[0]}:{list[1]}"

class Player:
    def __init__(self, number: int, name:str, start_score: str, end_score: str, second_start_score: str=None, second_end_score: str=None, ) -> None:
        self.number = int(number)
        self.name = name
        self.start_score = start_score.split(':')
        self.end_score = end_score.split(':')
        self.second_start_score = second_start_score.split(':') if second_start_score != None else None
        self.second_end_score = second_end_score.split(':') if second_end_score != None else None


    def getPlayedScores(self):
        result = f"{listToScore(self.start_score)}-{listToScore(self.end_score)}"
        if self.second_start_score != None:
            result += f" & {listToScore(self.second_start_score)}-{listToScore(self.second_end_score)}"
        return result


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


def getGameInfo(directory_path, team_to_look_for):

    path_parts = directory_path.split('/')

    # List all files in the directory
    files = os.listdir(directory_path)

    # Specify the pattern for the files you're interested in
    game_pattern = '.*-game.csv'
    player_pattern = '.*-players.csv'
    name_pattern = '.*-names.csv'

    # Filter files based on the pattern
    game_files = [file for file in files if re.match(game_pattern, file)]
    player_files = [file for file in files if re.match(player_pattern, file)]
    name_files = [file for file in files if re.match(name_pattern, file)]
    game_files.sort()
    player_files.sort()
    name_files = files_to_dict(name_files)#not always a file

    #read in normal names
    names_dict_normally = read_csv_to_dict(f"{directory_path}/player-names-normally.csv")

    results = {}

    for i, game_file in enumerate(game_files):

        teams = game_file.split('-')

        # Extract team names
        home_team = teams[0]
        is_home = home_team == team_to_look_for
        away_team = teams[1]
        game_name = f"{home_team}-{away_team}"
        logger.info(f"processing {game_name}")

        #read files
        df_game = pd.read_csv(f"{directory_path}/{game_file}", delimiter=';', skipinitialspace=True)
        df_players = pd.read_csv(f"{directory_path}/{player_files[i]}", delimiter=';', skipinitialspace=True)

        #get names
        game_names = read_csv_to_dict(f"{directory_path}/{name_files[game_name]}") if game_name in name_files else {}
        names_dict = names_dict_normally.copy()
        names_dict.update(game_names)

        #construct setresults
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
            sets[set].addPlayer(number, exchange, change, change_back, is_home, names_dict)

        results[game_name] = GameResult(sets, home_team, away_team, path_parts[1], path_parts[2])

    return results


def tabeliseResults(results: Dict[str, SetResult]):
    datas = []
    for game_name, result in results.items():
        data = []
        total_game = {}
        data.append([game_name, result.season.replace('_', '/'), result.team])
        for set_number, set in result.sets.items():
            data.append([f"Satz: {set_number}. Ergebnis: {set.home_points}:{set.away_points}. Gespielte Punkte: {set.getPointsPlayed()}"])
            data.append(["Spieler:in"," PlusMinus", "Gespielte Punkte", "Anteil am Satz", "Ein-/Auswechslung"])
            for key, player in set.players.items():
                data.append([f"{player.name}", f"{player.getPlusMinus()}",f"{player.getPointsPlayed()}", f"{(player.getPointsPlayed()/set.getPointsPlayed())*100:.0f}%", f"{player.getPlayedScores()}"])
                if player.number not in total_game:
                    total_game[player.number] = [player.name, player.getPlusMinus(), player.getPointsPlayed()]
                else:
                    total_game[player.number][1] += player.getPlusMinus()
                    total_game[player.number][2] += player.getPointsPlayed()
        data.append([f"Ganzes Spiel. Gespielte Punkte: {result.getPointsPlayed()}"])
        data.append(["Spieler:in"," PlusMinus", "Gespielte Punkte", "Anteil am Spiel"])
        for number, stat in total_game.items():
            data.append([f"{stat[0]}", f"{stat[1]}", f"{stat[2]}", f"{(stat[2]/result.getPointsPlayed())*100:.0f}%"])
        datas.append(data)
    return datas
            

def makePdf(data, output_path):

    createPathIfNotExists(output_path)
    # Create a PDF
    pdf_filename = f"{output_path}/{data[0][0]}.pdf"
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
    logger.info(f"{pdf_filename} created")


def getDirsInDir(directory_path):
    # Get the list of all items in the directory
    all_items = os.listdir(directory_path)

    # Filter out only directories
    directories = [item for item in all_items if os.path.isdir(os.path.join(directory_path, item))]

    return directories


def files_to_dict(file_list):
    result_dict = {}
    
    for file_name in file_list:
        # Extract the key from the file name
        file_parts = file_name.split('-')
        key = f"{file_parts[0]}-{file_parts[1]}"
        # Add the key-value pair to the dictionary
        result_dict[key] = file_name
    
    return result_dict


def read_csv_to_dict(file_path):
    result_dict = {}
    
    with open(file_path, 'r') as file:
        # Create a CSV reader object
        csv_reader = csv.reader(file, delimiter=';')
        
        # Read the header
        header = next(csv_reader)
        
        # Check if there are two columns in the header
        if len(header) == 2:
            # Iterate through the rows and create a dictionary
            for row in csv_reader:
                key, value = row
                result_dict[int(key)] = value
        else:
            raise SyntaxError("header of name file doesnt have two cloumns")
                
    return result_dict


def createPathIfNotExists(directory_path):
    if not os.path.exists(directory_path):
            # Create the directory if it doesn't exist
            os.makedirs(directory_path)


def main():

    for season in getDirsInDir("data"):
        for team in getDirsInDir(f"data/{season}"):
            results = getGameInfo(f"data/{season}/{team}", "TSC")

            datas = tabeliseResults(results)
            for data in datas:
                makePdf(data, f"results/{season}/{team}")


if __name__ == "__main__":
    main()