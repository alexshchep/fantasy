#SQL queries collection

# =============SELECTS=================
# select playerid based on full name
selectplayerid = """SELECT PlayerID FROM Players WHERE FullName = %s;"""
# select teamid based on abbreviation of team name
selectteamid_abbrev = """SELECT TeamID FROM Teams WHERE Abbreviation = %s;"""
# select gameid based on home team, away team and game date
selectgameidq = """SELECT GameID FROM Games WHERE HomeTeam = %s AND AwayTeam = %s AND GameDate = %s;"""
# select teamid based on team name
selectteamid = """SELECT TeamID FROM Teams WHERE TeamName = %s;"""
# select playerid based on lastname match
selectplayeridonlastname = """SELECT PlayerID FROM Players WHERE FullName LIKE %s;"""
# select player name based on playerid
selectplayername = """SELECT FullName FROM Players WHERE PlayerID = %s;"""
# select player based on playerdraftkingsid
selectplayersondraftkingsid = """SELECT PlayerID FROM Players WHERE PlayerDraftKingsID = %s;"""
# select players based on game id
selectplayergames = """SELECT * FROM PlayerGames;"""
# select last ngames of game players
selectlastngames = """SELECT * FROM PlayerGames WHERE PlayerID = %s AND GameDate < %s ORDER BY GameDate DESC LIMIT %s ;"""
# select last ngames of game goalies
selectlastngamesgoalies = """SELECT * FROM GoalieGames WHERE PlayerID = %s AND GameDate < %s ORDER BY GameDate DESC LIMIT %s ;"""
# select games by player within the last n days
selectlastndaygames = """SELECT * FROM PlayerGames WHERE PlayerID = %s AND GameDate < %s AND GameDate > %s; """ 
# select games by player within the last n days
selectlastndaygamesgoalies = """SELECT * FROM GoalieGames WHERE PlayerID = %s AND GameDate < %s AND GameDate > %s; """ 
# select all completed games 
selectallgames = """SELECT * FROM Games WHERE Completed = 1;"""


#=============INSERTS=================
# insert teams into teams database
insertteamsq = """INSERT INTO Teams (TeamName, Abbreviation) 
			VALUES(%s, %s) ON DUPLICATE KEY UPDATE TeamID = TeamID;"""
# insert players into the players database
insertplayersq = """INSERT INTO Players (FullName) VALUES (%s) ON DUPLICATE KEY UPDATE FullName = FullName;"""
# insert goalies
insertgoaliesq = """INSERT INTO Players (FullName, Goalie) VALUES (%s, 1) ON DUPLICATE KEY UPDATE FullName = FullName;"""
# insert into draftkings
insertdraftkingsq = """INSERT INTO DraftKings (DraftKingsName, HomeTeamID, AwayTeamID, TeamForID, TeamAgainstID, GameDateTime, PlayerDraftKingsID, Salary, Position, RosterPosition) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE HomeTeamID = HomeTeamID;"""

#=============UPDATES==================
# update players after draftkings file read
updateplayersdraftkings = """UPDATE Players SET DraftKingsName = %s, PlayerDraftKingsID = %s WHERE PlayerID = %s;"""

