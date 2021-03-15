from collections import namedtuple



# create a named tuple - Game
Game = namedtuple('Game', ['gameid', 'away', 'home', 'date', 'attendance', 'arena', 'duration', 'awayscore', 'homescore', 'OT', 'SO'])
# create a named tuple - Feature
Feature = namedtuple('Feature', ['name', 'value'])
# create a named tuple - Goal
Goal = namedtuple('Goal', ['goal', 'gameid', 'assist', 'assist2', 'time', 'period', 'teamfor', 'situation']) 
# create a named tuple - Penalty
Penalty = namedtuple('Penalty', ['player', 'gameid', 'minutes', 'reason', 'time', 'period', 'teampenalised'])
# create a named tuple - PlayerGame
PlayerGame = namedtuple('PlayerGame', ['name', 'gameid', 'teamfor', 'teamagainst', 'goals','assists', 'points', 'plus_minus', 'pim', 'goals_ev', 'goals_pp', 'goals_sh', 'gw', 'assists_ev', 'assists_pp', 'assists_sh', 'shots', 'shot_percentage', 'shifts', 'toi']) 
# create a named tuple - GoalieGame
GoalieGame = namedtuple('GoalieGame', ['name', 'gameid', 'teamfor', 'teamagainst', 'result', 'ga', 'sa', 'sv', 'sv_pct', 'so', 'pim', 'toi'])
# create a named tuple - ShootoutAttempt
ShootoutAttempt = namedtuple('ShootoutAttempt', ['gameid', 'shooter', 'goalie', 'goal'])

# create a named tuple - AdvancedStats
AdvancedStats = namedtuple('AdvancedStats', ['name', 'gameid', 'icf', 'satf', 'sata', 'cfpct', 'crel', 'zso', 'zsd', 'ozspct', 'hits', 'blocks'])

# create a dictionary of team names to team shortened abbreviations
teamDict = {'Anaheim Ducks': 'ANA', 'Arizona Coyotes': 'ARI', 'Boston Bruins': 'BOS', 'Buffalo Sabres': 'BUF', 'Calgary Flames': 'CGY', 'Carolina Hurricanes': 'CAR', 'Chicago Blackhawks': 'CHI', 'Colorado Avalanche': 'COL', 'Columbus Blue Jackets': 'CBJ', 'Dallas Stars': 'DAL', 'Detroit Red Wings': 'DET', 'Edmonton Oilers': 'EDM', 'Florida Panthers': 'FLA', 'Los Angeles Kings': 'LAK', 'Minnesota Wild': 'MIN', 'Montreal Canadiens': 'MTL', 'Nashville Predators': 'NSH', 'New Jersey Devils': 'NJD', 'New York Islanders': 'NYI', 'New York Rangers': 'NYR', 'Ottawa Senators': 'OTT', 'Philadelphia Flyers': 'PHI', 'Phoenix Coyotes': 'PHX', 'Pittsburgh Penguins': 'PIT', 'St. Louis Blues': 'STL', 'San Jose Sharks': 'SJS', 'Tampa Bay Lightning': 'TBL', 'Toronto Maple Leafs': 'TOR', 'Vancouver Canucks': 'VAN', 'Vegas Golden Knights': 'VEG', 'Washington Capitals': 'WSH', 'Winnipeg Jets': 'WPG'}

draftkingsDict = {'ANH': 'Anaheim Ducks', 'ARI': 'Arizona Coyotes', 'BOS': 'Boston Bruins', 'BUF': 'Buffalo Sabres', 'CAR': 'Carolina Hurricanes', 'CGY': 'Calgary Flames', 'CHI': 'Chicago Blackhawks', 'CLS': 'Columbus Blue Jackets', 'COL': 'Colorado Avalanche', 'DAL': 'Dallas Stars', 'DET': 'Detroit Red Wings', 'EDM': 'Edmonton Oilers', 'FLA':'Florida Panthers', 'LA': 'Los Angeles Kings', 'MIN': 'Minnesota Wild', 'MON': 'Montreal Canadiens', 'NJ': 'New Jersey Devils', 'NSH': 'Nashville Predators', 'NYI': 'New York Islanders', 'NYR': 'New York Rangers', 'OTT': 'Ottawa Senators', 'PIT': 'Pittsburgh Penguins', 'SJ': 'San Jose Sharks', 'STL': 'St. Louis Blues', 'TB': 'Tampa Bay Lightning', 'TOR': 'Toronto Maple Leafs', 'VAN': 'Vancouver Canucks', 'VGK': 'Vegas Golden Knights', 'WPG': 'Winnipeg Jets' }

# create a dictionary of First names to be same
nameDict = {'alexander': 'alex', 'alexandre': 'alex', 'matthew': 'matt', 'mathew': 'matt', 'nikolai': 'nikolay', 'jonathan': 'jon', 'jonathon': 'jon', 'steven': 'steve', 'joseph':'joe', 'zachary': 'zach', 'mitchell': 'mitch', 'tobias': 'toby'}


# create a dictionary for last games of the season
# keys - team name, values - goals for, goals against
teamgoaldict = {}
