import sys
import os
import random
import csv
import pandas as pd
import numpy as np
import datetime as dt
import statsmodels.formula.api as sm
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy import stats
from sklearn.linear_model import Ridge

# own libraries
import nhltuples
import genetic_algo

# set options
pd.set_option('display.max_columns', 500)
#pd.set_option('display.max_rows', 1000)

def point_function(position, goals, assists, sog, bs, shp, shootout, win, saves,ga, shutout, coef_arr_player = np.array([3,2,0.5,0.5,1,0.2,1.5] ), 
		   coef_arr_goalie = np.array([3,0.2,1,2])):
	if goals >= 3:
		hattrick = 1
	else:
		hattrick = 0
	points = 0
	if position == 'G':
		points = win * coef_arr_goalie[0] + saves * coef_arr_goalie[1] - ga * coef_arr_goalie[2] + shutout * coef_arr_goalie[3]
	else:
		points = goals * coef_arr_player[0] + assists * coef_arr_player[1] + sog * coef_arr_player[2] + bs * coef_arr_player[3] + shp * coef_arr_player[4] + shootout * coef_arr_player[5] + hattrick * coef_arr_player[6]
	return points

def players_by_position( mydate, folder, draftkings = False, draftkings_date = None):
	# retrieve 10 previous games of the player
	# download player csv
	dfplayers = pd.read_csv('{}/skaters.csv'.format(folder))
# download gameinfo	
	dfgameinfo = pd.read_csv('{}/gameinfo.csv'.format(folder))
	dfgameinfo['date'] = pd.to_datetime(dfgameinfo['date'], errors = 'coerce')
	# download advanced stats
	dfadvanced = pd.read_csv('{}/advanced.csv'.format(folder))
	# download shootout info
	dfshootout = pd.read_csv('{}/shootouts.csv'.format(folder))
	# download basic player info
#	dfplayerinfo = pd.read_csv('{}/basic_players.csv'.format(folder), header = 2)
	dfplayerinfo = pd.read_csv('{}/season_stats.csv'.format(folder))
	dfplayerinfo.rename(columns = {'Player':'name', 'Pos': 'Position'}, inplace = True)
	# replace first name
#	dfplayerinfo['First Name'] = dfplayerinfo['First Name'].str.lower()	
#	dfplayerinfo.replace({"First Name":nhltuples.nameDict}, inplace = True)
	#print(dfplayerinfo['First Name'])
#	dfplayerinfo['name'] = dfplayerinfo['First Name'] + ' ' + dfplayerinfo['Last Name']
	#print(dfplayerinfo)
	# convert names to lower case for easier merging
#	dfplayerinfo['name'] = dfplayerinfo['name'].str.lower()
	#print(dfplayerinfo['name'].to_string() )
	# sort games by date
	dfgameinfo.sort_values(by  = 'date', inplace = True)	
	# keep the matches in which this player participated
	# remove dates after the set date
	dfgameinfo = dfgameinfo[dfgameinfo['date'] < mydate]
	maxgameid = max(dfgameinfo['gameid'])
	# merge dfplayers with dfgameinfo
	dfplayers = dfplayers.merge(dfgameinfo[['gameid', 'away', 'home', 'date', 'attendance']], how = 'inner', on = 'gameid')
	# merge dfplayers with advanced stats
	dfplayers = dfplayers.merge(dfadvanced[['gameid', 'name', 'blocks', 'hits', 'icf', 'satf', 'sata', 'cfpct', 'crel', 'zso', 'zsd', 'ozspct']])
	# merge dfplayers with shootout attempts
	dfplayers = dfplayers.merge(dfshootout[['gameid', 'shooter', 'goal']], how = 'left', left_on = ['gameid', 'name'], right_on = ['gameid', 'shooter'])

	# merge dfplayers with dfplayerinfo to get the position 
	dfplayers = dfplayers.merge(dfplayerinfo[['name', 'Position']], how = 'left', on = 'name')

	# convert names to lower case for easier merging
	dfplayers['name'] = dfplayers['name'].str.lower()
	# change first names
	splitted = dfplayers['name'].str.split(' ',  1)
	dfplayers['first'] = splitted.str[0]
	dfplayers.replace({'first':nhltuples.nameDict}, inplace = True)
	dfplayers['name'] = dfplayers['first'] + ' ' + splitted.str[1]

	# fill the nds with zeroes
	dfplayers.fillna(value = 0, inplace = True)
	# sort games by date
	dfplayers.sort_values(by =  'date', inplace = True)
	# convert toi to a number
	dfplayers['toi'] = dfplayers['toi'].str.split(':').apply(lambda x: int(x[0]) + int(x[1])/60.0)
	dfplayers['playtoday'] = 0
	if draftkings:

		# download players that will play today
		todayplayers = get_draftkings(folder = folder, draftkings_date  = draftkings_date, maxgameid = maxgameid)
		#todayplayers.
		todayplayers.rename(columns = {'Name': 'name'}, inplace = True)
		# join players that exist in both

		# add column to differentiate
		dfplayers['playtoday'] = 0
		todayplayers['playtoday'] = 1
		dfplayers = pd.concat([dfplayers, todayplayers])
		# draftkings and other data sources have different positions assigned to some players, need to fix
		playerlist = list(set(dfplayers['name']))
		for player in playerlist:
			lastpos = dfplayers[dfplayers['name'] == player]['Position'].iloc[-1]
			dfplayers['Position'].loc[dfplayers['name']==player] = lastpos   
		
	dfplayers['pgid'] = dfplayers.index
	myindx = dfplayers['Position'].str.contains('D')
	defensemen = dfplayers[dfplayers['Position'].str.contains('D', na = False)]	
#	goalies = dfplayers[dfplayers['Position'].str.contains('G')]
	wingers = dfplayers[dfplayers['Position'].str.contains('W', na = False)]
	centers = dfplayers[dfplayers['Position'].str.contains('C', na = False)]
	return (defensemen, wingers, centers)

def get_goalies(mydate, folder, draftkings = False, maxgameid = None, draftkings_date = None):

	# download from goalie csv
	dfgoalies = pd.DataFrame.from_csv('{}/goalies.csv'.format(folder))	
	# make name a column
	dfgoalies.reset_index(inplace = True)
	# download gameinfo
	dfgameinfo = pd.read_csv('{}/gameinfo.csv'.format(folder))
	maxgameid = max(dfgameinfo['gameid'])
	dfgameinfo['date'] = pd.to_datetime(dfgameinfo['date'], errors = 'coerce')
	# sort games by date
	dfgameinfo.sort_values(by  = 'date', inplace = True)	
	# keep the matches in which this player participated
	# remove dates after the set date
	dfgameinfo = dfgameinfo[dfgameinfo['date'] < mydate]
	# merge dfplayers with dfgameinfo	
	dfplayers = dfgoalies.merge(dfgameinfo[['gameid', 'away', 'home', 'date', 'attendance']], how = 'inner', on = 'gameid')
	# convert toi to a number
	dfplayers['toi'] = dfplayers['toi'].str.split(':').apply(lambda x: int(x[0]) + int(x[1])/60.0)
	dfplayers.sort_values(by = 'date', inplace = True)

	# convert result to wins/OT/losses
	dfplayers['win'] = 0
	dfplayers['loss'] = 0
	dfplayers['OT'] = 0
	dfplayers['win'].loc[dfplayers['result']== 'W'] = 1 
	dfplayers['loss'].loc[dfplayers['result']== 'L'] = 1 
	dfplayers['OT'].loc[dfplayers['result']== 'O'] = 1
	dfplayers['playtoday'] = 0

	# convert names to lower case for easier merging
	dfplayers['name'] = dfplayers['name'].str.lower()
	# change first names
	splitted = dfplayers['name'].str.split(' ',  1)
	dfplayers['first'] = splitted.str[0]
	dfplayers.replace({'first':nhltuples.nameDict}, inplace = True)
	dfplayers['name'] = dfplayers['first'] + ' ' + splitted.str[1]

	if draftkings:
		todayplayers = get_draftkings(folder = folder, draftkings_date  = draftkings_date, maxgameid = maxgameid, goalies = True)
		
		#todayplayers.
		todayplayers.rename(columns = {'Name': 'name'}, inplace = True)
		# join players that exist in both
		print('the length of draftkings df before merge: {}'.format(len(todayplayers)))
		# add column to differentiate
		dfplayers['playtoday'] = 0
		todayplayers['playtoday'] = 1
		dfplayers = pd.concat([dfplayers, todayplayers])
		print('the length of players df after merge: {}'.format(len(dfplayers)))

		
	dfplayers['pgid'] = dfplayers.index
	
	return dfplayers
	
def compile_data_prevgames(dfplayers, prevgames, folder, label = '', test = False): 
	if label == 'G':
		return compile_goalie_prevgames(dfplayers, prevgames,folder = folder, label = 'G', test = test)
	allteams = list(nhltuples.teamDict.keys())
	# key is teamname, value is (dataframe with columns gameid, goalsfor, goalsagainst)
	teamgoaldict = {}
	for myteam in allteams:
		if len(dfplayers['teamfor'].iloc[0]) > 3:
			teamkey = nhltuples.teamDict[myteam]
		if test:
			if myteam == 'Phoenix Coyotes':
				continue
			testrow = dfplayers[dfplayers['teamfor'] == myteam]
			testrow = testrow[pd.notnull(testrow['Salary'])]	
			if len(testrow) > 0:
				testrow = testrow.iloc[0]
			else: 
				testrow = None
		else:
			testrow = None

		teamgoaldict[teamkey] = getgoalsteam(myteam, prevgames, folder, test = test, testrow = testrow )
	rollavgcols = ['goals', 'assists', 'shots', 'blocks', 'goals_sh', 'assists_sh', 'goal', 'hits', 'icf', 'satf', 'sata', 'zso', 'zsd','toi']
	colscopy = ['name', 'date', 'pgid', 'teamagainst', 'gameid', 'teamfor', 'playtoday']
	if test:
		colscopy.extend(['Salary', 'Position'])
	# playerlist
	playerlist = list(set(list(dfplayers['name'])))
	# list of dfs
	dflist = []
	print('Compiling data for {}...'.format(label))
	for myplayer in playerlist:
		# iterate through each statistic and player
		dfmyplayer = dfplayers[dfplayers['name'] == myplayer]
	#	dfmyplayer = dfmyplayer.iloc[-prevgames:]
		# calculate fantasy points
		dfmyplayer['fantasy_pts'] = dfmyplayer.apply(lambda row: point_function('notgoalie', row['goals'], row['assists'], row['shots'], 
											row['blocks'], row['goals_sh'] + row['assists_sh'], 
											row['goal'], 0, 0, 0, 0), axis = 1) 
		# fantasy points for all matches except the first
		fpts = dfmyplayer['fantasy_pts']
		# calculate averages without last row
	#	myavg = pd.rolling_mean(dfmyplayer[rollavgcols].iloc[:-1], window = prevgames)
		myavg = dfmyplayer[rollavgcols].rolling(window = prevgames, center = False).mean().shift(1)
#		print('my avg is {}'.format(myavg))
	#	myavg = myavg.iloc[:-1]
		myavg['fantasy_pts'] = fpts
		myavg[colscopy] = dfmyplayer[colscopy]
		# get the games for the player's team and team against
		# get goals for and against
		myavg[['oppgoalsfor', 'oppgoalsagainst']] = myavg.apply(lambda row:extractteamgoals(teamgoaldict, row['teamagainst'],row['gameid'] ) ,axis = 1)
		myavg[['myteamgoalsfor', 'myteamgoalsagainst']] = myavg.apply(lambda row:extractteamgoals(teamgoaldict, row['teamfor'],row['gameid'] ) ,axis = 1)
	# drop nas
	#	myavg.dropna( inplace = True)
		dflist.append(myavg)
	dftrain = pd.concat(dflist)
#	dfplayers = dfplayers.transpose()
#	dfplayers.set_index('name', inplace = True)
	return dftrain

def compile_goalie_prevgames(dfplayers, prevgames, folder, label = '', normalize = False, test = False): 
	# create a dictionary for each team that will hold the goals scored for and against	
	# get a list of teams
	allteams = list(nhltuples.teamDict.keys())
	# key is teamname, value is (dataframe with columns gameid, goalsfor, goalsagainst)
	teamgoaldict = {}
	for myteam in allteams:
		if len(dfplayers['teamfor'].iloc[0]) > 3:
			print('changing dictionary key from {} to {}'.format(myteam, nhltuples.teamDict[myteam]))
			teamkey = nhltuples.teamDict[myteam]
		if test:
			print(myteam)
			if myteam == 'Phoenix Coyotes':
				continue
			testrow = dfplayers[dfplayers['teamfor'] == myteam]
			testrow = testrow[pd.notnull(testrow['Salary'])]	
			if len(testrow) > 0:
				testrow = testrow.iloc[0]
			else: 
				testrow = None
		else:
			testrow = None

		teamgoaldict[teamkey] = getgoalsteam(myteam, prevgames, folder, test = test, testrow = testrow )

	rollavgcols = ['ga', 'so', 'sa', 'toi', 'win', 'loss', 'OT']
	rollsumcols = ['sv', 'sa']
	colscopy = ['name', 'date', 'pgid', 'teamagainst', 'gameid', 'teamfor', 'playtoday']
	if test:
		colscopy.extend(['Salary', 'Position'])
	# playerlist
	# playerlist
	playerlist = list(set(list(dfplayers['name'])))
	# list of dfs
	dflist = []
	if normalize:
		normcols = ['win', 'save_pct', 'ga', 'so', 'sa', 'myteamgoalsfor', 'myteamgoalsagainst', 'oppgoalsfor', 'oppgoalsagainst']
		# get averages
		league_svpct = dfplayers['sv'].sum() / dfplayers['sa'].sum()
		league_ga = dfplayers['ga'].mean() / dfplayers['toi'].mean() * 60 
		league_so = dfplayers['so'].mean()
		league_sa = dfplayers['sa'].mean()
		normmeans = [0.5, league_svpct, league_ga, league_so, league_sa, League_ga, league_ga, league_ga, league_ga]
		normmax = dfplayers[['win', 'save_pct', 'ga', 'so', 'sa']].max()
		normmin = dfplayers[['win', 'save_pct', 'ga', 'so', 'sa']].min()

		
	print('Compiling data for {}...'.format(label))
	for myplayer in playerlist:
		# iterate through each statistic and player
		dfmyplayer = dfplayers[dfplayers['name'] == myplayer]
	#	dfmyplayer = dfmyplayer.iloc[-prevgames:]
		# calculate fantasy points 
		dfmyplayer['fantasy_pts'] = dfmyplayer.apply(lambda row: point_function('G',0,0, 0,0,0,0, row['win'], row['sv'], row['ga'], row['so']), axis = 1) 
		# fantasy points for all matches except the first
		fpts = dfmyplayer['fantasy_pts']
		# calculate averages without last row
	#	myavg = pd.rolling_mean(dfmyplayer[rollavgcols].iloc[:-1], window = prevgames)
		myavg = dfmyplayer[rollavgcols].rolling(window = prevgames, center = False).mean().shift(1)	
		myavg[['totalsaves', 'totalshotsagainst']] = dfmyplayer[rollsumcols].rolling(window = prevgames, center = False).sum().shift(1)
		# save percentage
		myavg['save_pct'] = myavg['totalsaves'] / myavg['totalshotsagainst'] 
	#	myavg = myavg.iloc[:-1]
		myavg['fantasy_pts'] = fpts
		myavg[colscopy] = dfmyplayer[colscopy]
	#	myavg['name'] = dfmyplayer['name']
	#	myavg['date'] = dfmyplayer['date']
	#	myavg['pgid'] = dfmyplayer['pgid']
	#	myavg['gameid'] = dfmyplayer['gameid']	
	#	myavg['teamagainst'] = dfmyplayer['teamagainst']
	#	myavg['teamfor'] = dfmyplayer['teamfor']
		# get the games for the player's team and team against
#		teamfor = dfmyplayer['teamfor'].iloc[-1]
		# get goals for and against
	#	dfgoalsfor = getgoalsteam(teamfor, prevgames)
#		dfgoalsfor = teamgoaldict[teamfor].copy()
		# rename columns
#		dfgoalsfor.columns = ['gameid', 'myteamgoalsfor', 'myteamgoalsagainst']
#		myavg = myavg.merge(dfgoalsfor, how = 'inner', on = 'gameid')

	#	dfgoalsopp = getgoalsteam(teamagainst, prevgames)
#		dfgoalsopp.columns = ['gameid', 'oppgoalsfor', 'oppgoalsagainst']
		# need to find the closest day to the gameid match
		myavg[['oppgoalsfor', 'oppgoalsagainst']] = myavg.apply(lambda row:extractteamgoals(teamgoaldict, row['teamagainst'],row['gameid'] ) ,axis = 1)
		myavg[['myteamgoalsfor', 'myteamgoalsagainst']] = myavg.apply(lambda row:extractteamgoals(teamgoaldict, row['teamfor'],row['gameid'] ) ,axis = 1)
		if normalize:
			normcols = ['win', 'save_pct', 'ga', 'so', 'sa', 'myteamgoalsfor', 'myteamgoalsagainst', 'oppgoalsfor', 'oppgoalsagainst']
			myavg[normcols] = (myavg[normcols] - normmeans) / (myavg[normcols].max() - myavg[normcols].min())
		dflist.append(myavg)
	dftrain = pd.concat(dflist)
#	dfplayers = dfplayers.transpose()
#	dfplayers.set_index('name', inplace = True)
	return dftrain

def extractteamgoals(mydict, teamname, gameid):
	if len(teamname) > 3:
		teamname = nhltuples.teamDict[teamname]
	dfgoals = mydict[teamname]
	result = dfgoals[dfgoals['gameid'] == gameid]
	
	if len(result) == 0:
#		print('new team name is {} game id is {}, dictionary is {}'.format(teamname, gameid, mydict))
#		print('result is \n'.format(result))
		return pd.Series([np.nan, np.nan])
	else:
		return result[['sum_goalsfor', 'sum_goalsagainst']].iloc[-1]

def getgoalsteam(teamname, prevgames, folder, gameid = -1, test = False, testrow = None):
	dfgameinfo = pd.read_csv('{}/gameinfo.csv'.format(folder))
	dfgameinfo['date'] = pd.to_datetime(dfgameinfo['date'])
	# keep the games of players team
	dfgamesfor = dfgameinfo[dfgameinfo['home'].str.contains(teamname) | dfgameinfo['away'].str.contains(teamname)].copy()
	keepcols = ['gameid', 'away', 'home', 'date', 'awayscore', 'homescore']
	dfgamesfor = dfgamesfor[keepcols]
	if test and testrow is not None:
		# add the draftkings gameinfo
		testser = pd.Series([testrow['gameid'], testrow['away'], testrow['home'], testrow['date'], np.nan, np.nan], index = keepcols) 
		dfgamesfor = dfgamesfor.append(testser, ignore_index = True)
	dfgamesfor['ishome'] = 0
	dfgamesfor['ishome'].loc[dfgamesfor['home'].str.contains(teamname)] = 1 
	# sort by date
	dfgamesfor.sort_values(by  = 'date', inplace = True)	
	# keep the previous number of games for both teams
	#dfgamesfor = dfgamesfor.iloc[-prevgames:]
	# count goals for
	dfgamesfor['goalsfor'] = np.nan
	dfgamesfor['goalsagainst'] = np.nan
	dfgamesfor['goalsfor'].loc[dfgamesfor['ishome'] == 1] = dfgamesfor['homescore'].loc[dfgamesfor['ishome'] == 1]
	dfgamesfor['goalsfor'].loc[dfgamesfor['ishome'] == 0] = dfgamesfor['awayscore'].loc[dfgamesfor['ishome'] == 0]
	dfgamesfor['goalsagainst'].loc[dfgamesfor['ishome'] == 1] = dfgamesfor['awayscore'].loc[dfgamesfor['ishome'] == 1]
	dfgamesfor['goalsagainst'].loc[dfgamesfor['ishome'] == 0] = dfgamesfor['homescore'].loc[dfgamesfor['ishome'] == 0]
	dfgamesfor['sum_goalsfor'] = dfgamesfor['goalsfor'].rolling(prevgames).mean().shift(1)
	dfgamesfor['sum_goalsagainst'] = dfgamesfor['goalsagainst'].rolling(prevgames).mean().shift(1)
	# count goals against
	if gameid == -1:
		return dfgamesfor[['gameid', 'sum_goalsfor', 'sum_goalsagainst']]
	else:
		return dfgamesfor[['sum_goalsfor', 'sum_goalsagainst']][dfgamesfor['gameid']==gameid]

def setup_test(mydate, datadivision = [0.50, 0.25, 0.25], errordict = {}):
	if len(errordict) == 0:
		print('get players...')
		dfdef, dfwin, dfcen = players_by_position( mydate, folder = 'CSVdata/2017')
		# get testplayers pool for the season
		testdef, testwin, testcen = players_by_position(mydate, folder = 'CSVdata/2018', draftkings = True, draftkings_date = dt.date(2017,11,24))
		dfgoalies = get_goalies(mydate, folder = 'CSVdata/2017')
		testgoalies = get_goalies(mydate, folder = 'CSVdata/2018', draftkings = True, draftkings_date = dt.date(2017, 11, 24))
		# get testplayers for the day
	#	myseed = random.randint(1,10000)
		myseed = 500
		rangegames = range(1,25)
		def_predictions = predict_ridge(dfdef, list(dfdef['pgid']), 'D', datadivision, myseed, rangegames, testdef, list(testdef['pgid']))
		win_predictions = predict_ridge(dfwin, list(dfwin['pgid']), 'W', datadivision, myseed, rangegames, testwin, list(testwin['pgid']))
		cen_predictions = predict_ridge(dfcen, list(dfcen['pgid']), 'C', datadivision, myseed, rangegames, testcen, list(testcen['pgid']))
		goalie_predictions = predict_ridge(dfgoalies, list(dfgoalies['pgid']), 'G', datadivision, myseed, rangegames, testgoalies, list(testgoalies['pgid']))
		dfpredictions = pd.concat([def_predictions, win_predictions, cen_predictions, goalie_predictions])

		dfpredictions.to_csv('results/today_players_all_{}_{}_{}.csv'.format(mydate.year, mydate.month, mydate.day))
	else:
		print('get players...')
		dfdef, dfwin, dfcen = players_by_position( mydate, folder = 'CSVdata/2017')
		# get testplayers pool for the season
		testdef, testwin, testcen = players_by_position(mydate, folder = 'CSVdata/2018', draftkings = True, draftkings_date = dt.date(2017,11,24))
		dfgoalies = get_goalies(mydate, folder = 'CSVdata/2017')
		testgoalies = get_goalies(mydate, folder = 'CSVdata/2018', draftkings = True, draftkings_date = dt.date(2017, 11, 24))
		# get testplayers for the day
	#	myseed = random.randint(1,10000)
		myseed = 500
		def_alpha, def_ngames = errordict['d']
		def_predictions = predict_ridge(dfdef, list(dfdef['pgid']), 'D', datadivision, myseed, def_ngames, testdef, list(testdef['pgid']), def_alpha)
		win_alpha, win_ngames = errordict['w']
		win_predictions = predict_ridge(dfwin, list(dfwin['pgid']), 'W', datadivision, myseed, win_ngames, testwin, list(testwin['pgid']), win_alpha)
		cen_alpha, cen_ngames = errordict['c']
		cen_predictions = predict_ridge(dfcen, list(dfcen['pgid']), 'C', datadivision, myseed, cen_ngames, testcen, list(testcen['pgid']), cen_alpha)
		g_alpha, g_ngames = errordict['g']
		goalie_predictions = predict_ridge(dfgoalies, list(dfgoalies['pgid']), 'G', datadivision, myseed, g_ngames, testgoalies, list(testgoalies['pgid']), g_alpha)
		dfpredictions = pd.concat([def_predictions, win_predictions, cen_predictions, goalie_predictions])

		dfpredictions.to_csv('results/today_players_all_{}_{}_{}.csv'.format(mydate.year, mydate.month, mydate.day))

def predict_ridge(dfplayers, listids, position, datadivision, myseed, rangegames, testplayers, testids, alpha = 0):
	trainids, validids, testidsone = divideData(listids, datadivision, myseed)
	# error arrays
	if position == 'G':
		predictcols = ['win', 'save_pct', 'ga', 'so', 'sa', 'myteamgoalsfor', 'myteamgoalsagainst', 'oppgoalsfor', 'oppgoalsagainst']
	else:
		predictcols = ['goals', 'assists', 'shots', 'blocks', 'goals_sh', 'goal', 'hits', 'satf', 'sata', 'zso', 'zsd', 'toi', 'myteamgoalsfor', 
			       'myteamgoalsagainst', 'oppgoalsfor', 'oppgoalsagainst']
	errlist = []
	if type(rangegames) == type([]):
		for prevgame in rangegames:
			print('**************************************')
			trainplayers = compile_data_prevgames(dfplayers, prevgame, folder = 'CSVdata/2017', label = position)
			error, alpha, ridge = trainData(trainplayers[trainplayers['pgid'].isin(trainids)], trainplayers[trainplayers['pgid'].isin(validids)], 
							position = position, colnames = predictcols)
			# print results 
			print('finished {}'.format(position))
			print('the errors for {} for {} games was \n {}'.format(position, prevgame, stats.describe(error, nan_policy = 'omit')))
			
			# append to error lists
			errlist.append((prevgame, np.absolute(error).mean(), alpha, ridge))
		# save error calculations to csv 
		with open('results/errorlist_{}_{}'.format(position, str(dt.datetime.today())), 'wb') as myfile:
	    		wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
	    		wr.writerow(errlist)
		print('{} error list {}'.format(position, errlist))
		# choose the best prevgames and best alpha
		smallesterr = [x[1] for x in errlist]
		# get the indices
		minerrorindex = smallesterr.index(min(smallesterr))
		bestgames, besterror, bestalpha, bestridge = errlist[minerrorindex]
	else:
		error, alpha, bestridge = trainData(trainplayers[trainplayers['pgid'].isin(trainids)], trainplayers[trainplayers['pgid'].isin(validids)], 
						    position = position, colnames = predictcols)
		bestgames = rangegames
		bestalpha = alpha

	testplayers = compile_data_prevgames(testplayers, bestgames, folder = 'CSVdata/2018', label = position, test = True)

	testplayers = testplayers[testplayers['pgid'].isin(testids)]
	testplayers.dropna(subset = predictcols, how = 'any', inplace = True)
	testplayers['prediction_pts'] = bestridge.predict(testplayers[predictcols])
	# write to csv 
	testplayers.to_csv('results/testdata_{}_{}.csv'.format(position, str(dt.datetime.today())))
	# keep only players who play today
	testplayers = testplayers[testplayers['playtoday'] == 1]
	myday = dt.datetime.today()
	testplayers.to_csv('results/today_players_{}_{}_{}_{}.csv'.format(position, myday.year, myday.month, myday.day))
	return testplayers

def get_draftkings(folder, draftkings_date, maxgameid, goalies = False):
	'''
		params 
		mydate - dt.date() type
	'''
	df = pd.DataFrame.from_csv('{}/draftkings/DKSalaries{}.csv'.format(folder, str(draftkings_date)))
	df.reset_index(inplace = True )

	# convert names to lower case for easier merging
	df['Name'] = df['Name'].str.lower()
	# change first names
	splitted = df['Name'].str.split(' ',  1)
	df['first'] = splitted.str[0]
	df.replace({'first':nhltuples.nameDict}, inplace = True)
	df['Name'] = df['first'] + ' ' + splitted.str[1]

	newcols = ['teams', 'date', 'time', 'timeet']
	diffgames = list(df['GameInfo'].unique())
	gameidDict = dict(zip(diffgames, range(maxgameid, maxgameid + len(diffgames) + 1)))
	df['gameid'] = df['GameInfo'] 
	df.replace({'gameid':gameidDict}, inplace = True)
	tempdf = pd.DataFrame(df['GameInfo'].str.split(' ').tolist(),
                                   columns = newcols)
	df = pd.concat([df, tempdf], axis = 1)
	df.drop(['time', 'timeet'], axis = 1,  inplace = True)
	newcols = ['away', 'home']

	df[newcols] = pd.DataFrame(df['teams'].str.split('@').tolist(), columns = newcols)
	df.replace({'away': nhltuples.draftkingsDict, 'home':nhltuples.draftkingsDict, 'teamAbbrev': nhltuples.draftkingsDict}, inplace = True)
	df.rename(columns = {'teamAbbrev':'teamfor'}, inplace = True)
	df['teamagainst'] = df['away']
	df['teamagainst'].loc[df['home'] != df['teamfor']] = df['home'].loc[df['home'] != df['teamfor']] 
	df['date'] = pd.to_datetime(df['date'], errors = 'coerce')
	if goalies:
		df = df[df['Position'] == 'G']
	return df

def mult_sum_coefs(row, colnames, coef_array, suppressInt):
	# assert that length of colnames is 2 less than coefficient array due to the intercept
	# multiply and sum the row to get the expected value
	# coef_array[0] is the intercept
	if suppressInt:
		assert len(colnames) == len(coef_array)
		ev = sum(row[colnames]*coef_array)
	else:
		ev = sum(row[colnames] * coef_array[1:]) + coef_array[0]
		assert len(colnames) == len(coef_array) - 1
	return ev

def trainData(traindata, validdata, position, colnames):
	print('******************************')
#	print('traindata is\n {} \n'.format(traindata))
#	print('validdata is\n {} \n'.format(validdata))
#	traindata.to_csv('results/traindata_'+str(dt.datetime.today())+'.csv')
#	validdata.to_csv('results/validdata_'+str(dt.datetime.today())+'.csv')
	# run regression
#	if position == 'G':
#		colnames = ['win', 'save_pct', 'ga', 'so', 'sa', 'myteamgoalsfor', 'myteamgoalsagainst', 'oppgoalsfor', 'oppgoalsagainst']
#	else:
#		colnames = ['goals', 'assists', 'shots', 'blocks', 'goals_sh', 'goal', 'hits', 'satf', 'sata', 'zso', 'zsd', 'toi', 'myteamgoalsfor', 'myteamgoalsagainst', 'oppgoalsfor', 'oppgoalsagainst']
	ridge = True
	if ridge:
		alphalist = [0.001, 0.01, 0.1, 0.5, 1, 2, 10]
		resultlist = []
		ridgereglist = []
		for idx, alpha in enumerate(alphalist):
			print('testing alpha {}'.format(alpha))
			ridgereg = run_ridge(traindata, colnames, 'fantasy_pts', alpha)
			validdata.dropna(how = 'any', inplace = True)
			validdata['fantasy_pts_regression'] = ridgereg.predict(validdata[colnames])
			validdata['error'] = validdata['fantasy_pts_regression'] - validdata['fantasy_pts']
			resultlist.append(np.mean(np.absolute(validdata['error'])))
			ridgereglist.append(ridgereg)
		minindex = resultlist.index(min(resultlist))
		print(resultlist)
		print('the minimum result is {}, the minimum alpha is {}'.format(resultlist[minindex], alphalist[minindex]))	
		return resultlist[minindex], alphalist[minindex], ridgereglist[minindex]
	#	print(ridgereg.predict(validdata[colnames].dropna(how = 'any')))
	# test on validation data

	formula = 'fantasy_pts ~ ' + ' + '.join(colnames) + ' - 1' 
	myparams = run_regression(traindata, formula)
	# calculate player ev according to the regression results
	validdata['fantasy_pts_regression'] = validdata.apply(lambda row: mult_sum_coefs(row = row, colnames = colnames, coef_array = myparams, suppressInt = True), axis = 1) 
	# calculate the error between regression results and actual
	validdata['error'] = validdata['fantasy_pts_regression'] - validdata['fantasy_pts']
	# write to csv
#	validdata.to_csv('results/results' + str(random.randint(1, 10000))+'.csv')
	return validdata['error']
 
def run_regression(df, formula):
	result = sm.ols(formula=formula, data = df ).fit()
	print(result.summary())
	print(result.params)
	return result.params

def run_ridge(df, predictors, prediction, alpha):
	df.dropna(how = 'any', inplace = True)
	print('length of df is {}'.format(len(df)))
	ridgereg = Ridge(alpha = alpha, normalize = True, fit_intercept = False)
	ridgereg.fit(df[predictors], df[prediction])
	return ridgereg
#	print(ridgereg.metrics.classification_report)	

def divideData(gameplayerids, datadivision, myseed):
	'''
		shuffle the gameplayer ids 
	'''
#	print(gameplayerids)
	random.Random(myseed).shuffle(gameplayerids)
#	df = df.loc[gameplayerids]
	trainnum = int(datadivision[0] * len(gameplayerids) )
	validnum = int((datadivision[0] + datadivision[1]) * len(gameplayerids))
	trainids = gameplayerids[0:trainnum]
	validids = gameplayerids[trainnum:validnum]
	testids = gameplayerids[validnum:]

	return (trainids, validids, testids)

if __name__ == '__main__':
	print('calculating the best outcome...')
	# there are 1271 matches in total
	# 2017, april 9th is last regular season match
	mydate = dt.date(2017, 11, 23)
	# set up the test
	# errordict - key is position, values are tuples of [alpha, ngames] 
	errordict = {'g':(0.001, 14), 'd': (10, 5), 'c':(0.001, 5), 'w': (0.001, 6)}
	# download advanced stats
#	players_fan = player_ev('Bobby Ryan', 10, dt.date(2017, 4, 10))
	setup_test(mydate, datadivision = [0.75, 0.25, 0], errordict = errordict)

	# run genetic algo
	print('calculating the best roster...')
	nhl = genetic_algo.Hockey()
	nhl.getPlayersAlgo(mydate)
	
	nhl.keepCols(colstokeep = ['name', 'Salary', 'Value', 'prediction_pts' ])
	nhl.players = nhl.convertValues(nhl.players)
	deletelist = []
	nhl.removePlayers(deletelist)
	nhl.gamers = nhl.dfToPlayers(nhl.players)
	nhl.playersByPosition()	
	nhl.generate()
