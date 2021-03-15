import sys
import os
import random
import csv
import MySQLdb as mdb
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
import nhlqueries
import genetic_algo
import fantasy_html_to_mysql as fhtm

def point_function(position, goals, assists, sog, bs, shp, shootout, win, saves,ga, shutout, coef_arr_player = np.array([3,2,0.5,0.5,1,0.2,1.5] ), coef_arr_goalie = np.array([3,0.2,1,2])):
	if goals >= 3:
		hattrick = 1
	else:
		hattrick = 0
	points = 0
	if position == 'G':
		points = win * coef_arr_goalie[0] + saves * coef_arr_goalie[1] - ga * coef_arr_goalie[2] + shutout * coef_arr_goalie[3]
	else:
		points = goals * coef_arr_player[0] + assists * coef_arr_player[1] + sog * coef_arr_player[2] + bs * coef_arr_player[3] + shp * coef_arr_player[4] + shootout * coef_arr_player[5] + hattrick * coef_arr_player[6]
	return(points)

def playergames_ftpts(playergame, kingsposition):
	# playergame has PlayerPosition, Goals, Assists, Shots, Blocks, Goals_sh, Assists_sh, Result, SV, GA, SO
	if kingsposition == 'G':
		if playergame['Result'] == 'W':
			win = 1
		else:
			win = 0
		ftpts = point_function('G',0,0,0,0,0,0,win, playergame['SV'],playergame['GA'], playergame['SO'])
	else:
		ftpts = point_function(playergame['PlayerPosition'], playergame['Goals'], playergame['Assists'], playergame['Shots'], playergame['Blocks'], playergame['Goals_sh'] + playergame['Assists_sh'], 0, 0,0,0,0)
	return(ftpts)
	#position, goals, assists, sog, bs, shp, shootout, win, saves,ga, shutout

def get_player_last_n_games(cur, dictcur, playerid, ngames, gamedate, kingsposition):
	if kingsposition != 'G':
		dictcur.execute(nhlqueries.selectlastngames, [playerid, gamedate, ngames])
		lastgames = dictcur.fetchall()
	else:
		dictcur.execute(nhlqueries.selectlastngamesgoalies, [playerid, gamedate, ngames])
		lastgames = dictcur.fetchall()
	return(lastgames)

def get_player_last_n_days(cur, dictcur, playerid, ndays, gamedate, kingsposition):
	if kingsposition != 'G':
		dictcur.execute(nhlqueries.selectlastndaygames, [playerid, gamedate, ndays])
		lastgames = dictcur.fetchall()
	else:
		dictcur.execute(nhlqueries.selectlastndaysgoalies, [playerid, gamedate, ngames])
		lastgames = dictcur.fetchall()
	return(lastgames)

def ftpts_historical(dfplayers):
	try:
		conn = mdb.connect(host = 'localhost',
				user='sasha',
				passwd='sasha92',
				db='fantasy')
		cur = conn.cursor()
		dictcur = conn.cursor(mdb.cursors.DictCursor)
		ngames = 2;
		counter = 0
		for idx, row in dfplayers.iterrows():
			counter  = counter + 1
			if counter > 20:
				continue
			print('---------------')
			print(row.Name)
			draftkingsid = row['ID']
			kingsposition = row['Roster Position']
			# get date of the game
			gamedate = row['GameInfo']
			gamedate = gamedate.split()
			datestring = gamedate[1]
			gamedate = dt.datetime.strptime(datestring, '%m/%d/%Y')
			lastgames = get_player_last_n_games(cur, dictcur, draftkingsid, ngames, gamedate, kingsposition)
			if lastgames == None:
				continue
			for game in lastgames:
				print(game)
				ftpts = playergames_ftpts(game, kingsposition)
				print(ftpts)
				# get fantasy points for past games
	except mdb.Error, e:
		print(e)
	finally:
		if conn:
			conn.close()

def calculate_error_ngames():
	try:
		conn = mdb.connect(host = 'localhost',
				user='sasha',
				passwd='sasha92',
				db='fantasy')
		cur = conn.cursor()
		dictcur = conn.cursor(mdb.cursors.DictCursor)

		# get all games
		dictcur.execute(nhlqueries.selectplayergames, [])
		playergames = dictcur.fetchall()
		ngamelist = range(1,42)
		errorlist = []
		for ngames in ngamelist:
			print('computing errors for {} games').format(ngames)
			print('errorlist is {}'.format(errorlist))
			ngameerrorlist = []
			for playergame in playergames:
				playerid = playergame['PlayerID']
				gamedate = playergame['GameDate']
				# get the players last two games
				lastgames = get_player_last_n_games(cur, dictcur, playerid, ngames, gamedate, kingsposition = 'notg')	
				# dont count if length is not equal to ngames
				if len(lastgames) != ngames:
					continue
				# calculate fantasy points
				realpts = playergames_ftpts(playergame, kingsposition = 'notg')
				# lastgame points
				avg_list = []
				for lastgame in lastgames:
					lastgamepoints = playergames_ftpts(lastgame, kingsposition = 'notg')
					avg_list.append(lastgamepoints)

				pts_prediction = np.asarray(avg_list).mean()
				pts_error = pts_prediction - realpts
				if np.isnan(pts_error):
					continue
				ngameerrorlist.append(pts_error)
			print('length of ngameerrorlist is {}'.format(len(ngameerrorlist)))
			error_avg = np.absolute(np.asarray(ngameerrorlist)).mean()
			errorlist.append(error_avg)
		print(errorlist)
	except mdb.Error, e:
		print(e)
	finally:
		if conn:
			conn.close()

def calculate_error_ndates():
	try:
		conn = mdb.connect(host = 'localhost',
				user='sasha',
				passwd='sasha92',
				db='fantasy')
		cur = conn.cursor()
		dictcur = conn.cursor(mdb.cursors.DictCursor)

		# get all games
		dictcur.execute(nhlqueries.selectplayergames, [])
		playergames = dictcur.fetchall()
		ndatelist = range(100,205,5)
		errorlist = []
		for ndays in ndatelist:
			print('computing errors for past {} days').format(ndays)
			print('errorlist is {}'.format(errorlist))
			ngameerrorlist = []
			for playergame in playergames:
				playerid = playergame['PlayerID']
				gamedate = playergame['GameDate']
				# get the players last two games
				cutoffdate = gamedate - dt.timedelta(days = ndays)
				lastgames =get_player_last_n_days(cur, dictcur, playerid, cutoffdate, gamedate, kingsposition = 'notg')	
				# calculate fantasy points
				realpts = playergames_ftpts(playergame, kingsposition = 'notg')
				# lastgame points
				avg_list = []
				for lastgame in lastgames:
					lastgamepoints = playergames_ftpts(lastgame, kingsposition = 'notg')
					avg_list.append(lastgamepoints)

				pts_prediction = np.asarray(avg_list).mean()
				pts_error = pts_prediction - realpts
				if np.isnan(pts_error):
					continue
				ngameerrorlist.append(pts_error)
			print('length of ngameerrorlist is {}'.format(len(ngameerrorlist)))
			error_avg = np.absolute(np.asarray(ngameerrorlist)).mean()
			errorlist.append(error_avg)
		print(errorlist)
	except mdb.Error, e:
		print(e)
	finally:
		if conn:
			conn.close()

	
if __name__ == '__main__':
	gamedate = dt.datetime(2018,1,30)
	season = 2018
	
	#	dfplayers = fhtm.run_draftkings(season, gamedate)
	# get players who are about to play
#	kingsfile =  '/home/sasha/Dropbox/fantasy/fantasy/CSVdata/{}/draftkings/DKSalaries{}-{}-{}.csv'.format(season, gamedate.year, gamedate.month, gamedate.day)
#	dfplayers = fhtm.parseDraftkings(kingsfile)
#	ftpts_historical(dfplayers)
	# calculate errors
	calculate_error_ndates()
