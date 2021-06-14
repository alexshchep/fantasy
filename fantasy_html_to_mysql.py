import os 
import sys
import re
import codecs
import bs4
import csv
import requests
import time
import MySQLdb as mdb
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
from bs4 import Comment
from collections import namedtuple
from fake_useragent import UserAgent

# import named tuples
import nhltuples
import nhlqueries

def parseSoup(soup, gameid, firstid, season, playoffs):
	'''
		There are 2 Sebastian Ahos, we need to set an ahoflag, NYI Aho will be Aho2
	'''
	# connect to MySQL
	try:
		conn = mdb.connect(host = 'localhost',
			user='sasha',
			passwd='sasha92',
			db='fantasy',
                        charset='UTF8')
		cur = conn.cursor()

		# store in this list for now
		featurelist = []
		goallist = []
		penaltylist = []
		shootoutlist = []
		playerlist = []
		# game title
		gametitle = soup.find_all('h1')
		gametitle = gametitle[0].string
		re_at = re.search(' at ', gametitle)
		re_boxscore = re.search(' Box Score ', gametitle)
		away = gametitle[:re_at.start()]
		home = gametitle[re_at.end():re_boxscore.start()]

		# check for ahoflag
		if away == 'New York Islanders':
			ahoflag_a = True
		else:
			ahoflag_a = False
		if home == 'New York Islanders':
			ahoflag_h = True
		else:
			ahoflag_h = False
		print('--------------------------new game-------------------------------------')
		print('away team is_{}, home team is_{}.'.format(away, home))
		featurelist.append(nhltuples.Feature(name = 'away', value = away))
		featurelist.append(nhltuples.Feature(name = 'home', value = home))
		# scorebox information
		attendance, arena, gameduration, gamedate = parseInformation(soup)

		# retrieve players info
		# skaterlist - ['name', 'gameid', 'teamfor', 'teamagainst', 'goals','assists', 'points', 'plus_minus', 'pim', 'goals_ev',
		# 'goals_pp', 'goals_sh','gw', 'assists_ev', 'assists_pp', 'assists_sh', 'shots', 'shot_percentage', 'shifts', 'toi']
		awayskaterlist, awayscore, awaypim, awayshots = parseSkaters(soup, teamname = away, gameid = gameid, teamagainst = home, ahoflag = ahoflag_a)
		awayadvancedlist = parseAdvanced(soup, away, gameid, ahoflag = ahoflag_a)
		awaygoalielist = parseGoalies(soup, away, gameid, home, ahoflag = ahoflag_a)
		homeskaterlist, homescore, homepim, homeshots = parseSkaters(soup, teamname = home, gameid = gameid, teamagainst = away, ahoflag = ahoflag_h)
		homeadvancedlist = parseAdvanced(soup, home, gameid, ahoflag = ahoflag_h)
		homegoalielist = parseGoalies(soup, home, gameid, away, ahoflag = ahoflag_h)
		# parse soup for Penalties
		penaltylist = parsePenalty(soup)
		goallist, shootoutlist, OT, SO = parseScoring(soup)
		gameinfo = nhltuples.Game(gameid = gameid, away = away, home = home, date = gamedate, attendance = attendance, arena = arena, duration = gameduration, 
					  awayscore = awayscore, homescore = homescore, OT = OT, SO = SO)
		if playoffs < gameinfo.date:
			playoffs = 1
		else:
			playoffs = 0
		# SQL INSERTS------------------------------------
		# INSERT teams into the database

		# insert and get team ids
		
		cur.execute(nhlqueries.insertteamsq, (home, nhltuples.teamDict[home]))
		cur.execute(nhlqueries.insertteamsq, (away, nhltuples.teamDict[away]))
		cur.execute(nhlqueries.selectteamid, [home])
		hometeamid = cur.fetchone()
		cur.execute(nhlqueries.selectteamid, [away])  
		awayteamid = cur.fetchone()
		# import Game into the database
		insertgamesq = """INSERT INTO Games (HomeTeam, AwayTeam, GameDate, Location, Completed, SeasonEndYear, Playoffs) 
			VALUES (%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE GameDate = GameDate;"""
		cur.execute(insertgamesq, (hometeamid, awayteamid, gamedate, arena, 1, season, playoffs))
		print('wrote game to the database..')

		cur.execute(nhlqueries.selectgameidq, (hometeamid, awayteamid, gamedate))
		gameid = cur.fetchone()
		
		#insert skaters to db
		skaterlist_todb(cur, awayskaterlist, gameid, awayteamid, hometeamid, gamedate.date())
		skaterlist_todb(cur, homeskaterlist, gameid, hometeamid, awayteamid, gamedate.date())
		advancedskater_todb(cur, awayadvancedlist, gameid)
		advancedskater_todb(cur, homeadvancedlist, gameid)
		print('wrote skaters to the database..')
		goalielist_todb(cur, awaygoalielist, gameid, awayteamid, hometeamid, gamedate.date())
		goalielist_todb(cur, homegoalielist, gameid, hometeamid, awayteamid, gamedate.date())
		print('wrote goalies to the database..')
		shootoutlist_todb(cur, shootoutlist, gameid)
		print('wrote shootouts to the database..')
		# insert goals into the goals database
		goallist_todb(cur, goallist, gameid, (hometeamid, awayteamid))
		print('wrote goals to the database..')
		penaltylist_todb(cur, penaltylist, gameid, (hometeamid, awayteamid))
		print('wrote penatlies to the database..')

		insertgameinfoq = """INSERT INTO GameStatistics (GameID, HomeTeamID, AwayTeamID, HomeGoals, AwayGoals, HomePIM, AwayPIM, HomeShots, AwayShots, Attendance, 
		Duration) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE GameID = GameID;"""
		cur.execute(insertgameinfoq, (gameid, hometeamid, awayteamid, homescore, awayscore, homepim, awaypim, homeshots, awayshots, attendance, gameduration))
		print('wrote gameinfo to the database..')
		conn.commit()
	except mdb.Error, e:
		#print('Error {}: {}'.format(e.args[0], e.args[1]))
		#sys.exit(1)
		print(e)
	finally:
		if conn:
			conn.close()
	return 0

def skaterlist_todb(cur, skaterlist, gameid, teamfor, teamagainst, gamedate):
	# insert players into the players database
	#insertplayersq = """INSERT INTO Players (FullName) VALUES (%s) ON DUPLICATE KEY UPDATE FullName = FullName;"""
	# insert player game statistics into the playergames database
	insertplayergamesq = """INSERT INTO PlayerGames(PlayerID, GameID, GameDate, TeamFor, TeamAgainst, Goals, Assists, Points, PlusMinus, TOI, Shots, PIM, Goals_ev, 
	Goals_pp, Goals_sh, GW, Assists_ev, Assists_pp, Assists_sh, ShotPercentage, Shifts) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
	%s, %s, %s) ON DUPLICATE KEY UPDATE GameID = GameID;"""
	for skater in skaterlist:
		if skater.name == 'TOTAL':
			continue
		cur.execute(nhlqueries.insertplayersq, [skater.name])
		cur.execute(nhlqueries.selectplayerid, [skater.name])
		skater_id = cur.fetchone()
		cur.execute(insertplayergamesq, (skater_id, gameid, gamedate, teamfor, teamagainst, skater.goals, skater.assists, skater.points, skater.plus_minus, 
						 skater.toi, skater.shots, skater.pim, skater.goals_ev, skater.goals_pp, skater.goals_sh, skater.gw, skater.assists_ev, 
						 skater.assists_pp, skater.assists_sh, skater.shot_percentage, skater.shifts ))

def advancedskater_todb(cur, skaterlist, gameid):
	# update players with advanced stats
#	['name', 'gameid', 'icf', 'satf', 'sata', 'cfpct', 'crel', 'zso', 'zsd', 'ozspct', 'hits', 'blocks']
	updateadvancedplayersq = """UPDATE PlayerGames SET ICF = %s, SATF = %s, SATA = %s, CFpct = %s, CREL = %s, ZSO = %s, ZSD = %s, OZSpct = %s, Hits = %s, 
	Blocks = %s WHERE GameID = %s and PlayerID = %s;"""
        for skater in skaterlist:
		cur.execute(nhlqueries.selectplayerid, [skater.name])
		skaterid = cur.fetchone()
		cur.execute(updateadvancedplayersq, (skater.icf, skater.satf, skater.sata, skater.cfpct, skater.crel, skater.zso, skater.zsd, skater.ozspct, 
						     skater.hits, skater.blocks, gameid, skaterid))

def goalielist_todb(cur, goalielist, gameid, teamfor, teamagainst, gamedate):
#('GoalieGame', ['name', 'gameid', 'teamfor', 'teamagainst', 'result', 'ga', 'sa', 'sv', 'sv_pct', 'so', 'pim', 'toi'])
	# insert goalies 
	# insert players into the players database
	#insertgoaliesq = """INSERT INTO Players (FullName, Goalie) VALUES (%s, 1) ON DUPLICATE KEY UPDATE FullName = FullName;"""
	insertgoaliegamesq = """INSERT INTO GoalieGames(PlayerID, GameID, GameDate, TeamFor, TeamAgainst, Result, GA, SA, SV, SVpct, SO, TOI,PIM) 
	VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE GameID = GameID;"""
	for goalie in goalielist:
		cur.execute(nhlqueries.insertgoaliesq, [goalie.name])
		cur.execute(nhlqueries.selectplayerid, [goalie.name])
		goalieid = cur.fetchone()
		cur.execute(insertgoaliegamesq, (goalieid, gameid, gamedate, teamfor, teamagainst, goalie.result, goalie.ga, goalie.sa, goalie.sv, 
						 goalie.sv_pct, goalie.so, goalie.toi, goalie.pim))

def shootoutlist_todb(cur, shooterlist, gameid):
	insertshootersq = """INSERT INTO Shootouts (GameID, PlayerID, GoalieID, Goal) VALUES(%s, %s, %s, %s) ON DUPLICATE KEY UPDATE GameID = GameID;"""
	for shot in shooterlist:
		# get shooter id
		# namedtuple('ShootoutAttempt', ['gameid', 'shooter', 'goalie', 'goal'])
		cur.execute(nhlqueries.selectplayerid, [shot.shooter])
		playerid = cur.fetchone()
		cur.execute(nhlqueries.selectplayerid, [shot.goalie])
		goalieid = cur.fetchone()		
		cur.execute(insertshootersq, (gameid, playerid, goalieid, shot.goal)) 

def goallist_todb(cur, goallist, gameid, teams):
	# goallist = ['goal', 'gameid', 'assist', 'assist2', 'time', 'period', 'teamfor', 'situation']
	insertgoalsq = """INSERT INTO Goals (Scorer, GameID, PrimaryAssist, SecondaryAssist, TeamFor, TeamAgainst, TimeGoal, Period, Situation) 
	VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE GameID = GameID;"""
	for goal in goallist:
		# tuple of ids for scorer, primaryassist and secondary assist
		cur.execute(nhlqueries.selectplayerid, [goal.goal])
		scorer = cur.fetchone()
		cur.execute(nhlqueries.selectplayerid, [goal.assist])
		primaryAssist = cur.fetchone()
		cur.execute(nhlqueries.selectplayerid, [goal.assist2])
		secondaryAssist = cur.fetchone()
		# Retrieve teamIDs
		cur.execute(nhlqueries.selectteamid_abbrev, [goal.teamfor])
		teamforid = cur.fetchone()
		if teamforid == teams[0]:
			teamagainstid = teams[1]
		else:
			teamagainstid = teams[0]
		cur.execute(insertgoalsq, (scorer, gameid, primaryAssist, secondaryAssist, teamforid, teamagainstid, goal.time, goal.period, goal.situation))

def penaltylist_todb(cur, penaltylist, gameid, teams):
	insertpenaltiesq = """INSERT INTO Penalties (PlayerID, GameID, Minutes, Reason, TimePenalty, Period, TeamFor, TeamAgainst) 
	VALUES(%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE GameID = GameID;"""
	for penalty in penaltylist:
		cur.execute(nhlqueries.selectplayerid, [penalty.player])
		playerid = cur.fetchone()
		cur.execute(nhlqueries.selectteamid_abbrev, [penalty.teampenalised])
		teampenalisedid = cur.fetchone()
		if teampenalisedid == teams[0]:
			teamagainstid = teams[1]
		else:
			teamagainstid = teams[0]
		cur.execute(insertpenaltiesq, (playerid, gameid, penalty.minutes, penalty.reason, penalty.time, penalty.period, teampenalisedid, teamagainstid ))

def writeToCSV(filename, mylist, header, gameid, firsttype = False, folder = 'CSVdata/2018/', firstid = 1):
	print('writing to {}'.format(folder+filename))
	# write to csv
	if gameid == firstid and firsttype:
		writetype = 'w'
	else:
		writetype = 'a'
	with open(folder+filename, writetype) as fd:
		wr = csv.writer(fd)
		if writetype == 'w' and gameid == firstid:
			wr.writerow(header)
		for myl in mylist:
			wr.writerow(myl)
	
	
def parseInformation(soup):
	scorebox = soup.find_all('div', {'class': 'scorebox_meta'})
	for data in scorebox:
		mylist = data.contents
		for val in mylist:
			if type(None) == type(val.string):
				for val2 in val:
					if isinstance(val2, bs4.element.Tag):
						featname = val2.string
					if isinstance(val2, bs4.element.NavigableString):
						featvalue = val2
						if featname == 'Attendance':
							attendance = featvalue[2:]
							# convert to integer
							attendance = int(attendance.replace(',', ''))
						elif featname == 'Arena':
							arena = featvalue[2:]
						elif featname == 'Game Duration':
							gameduration = featvalue[2:]
							gameduration = string_to_seconds(gameduration)
					#	featurelist.append(Feature(name = futname, value = futvalue))	
			else:
				print('************')
				#print('getting date of the game')
				# try parsing date
				try:
					gamedate = dt.datetime.strptime(str(val.string), "%B %d, %Y, %I:%M %p")
					print('gamedate is {}'.format(gamedate))
					# create a Future and add to list
			#		featurelist.append(Feature(name = 'date', value = gamedate))
					
				except:
					pass
	return attendance, arena, gameduration, gamedate
def parseScoring(soup):
	goallist = []
	shootoutlist = []
	goaltable = soup.find('table', {'id': 'scoring'})
	rows = goaltable.find_all('tr')
	period = 0
	SO = False
	OT = False
	for row in rows:
		# check if shootout flag is on
		if SO:
			shootout = parseShootout(row, gameid)
			shootoutlist.append(shootout)
			continue
		# identify period
		periodlabel = row.find('th')
		if periodlabel:
			if '1st Period' in periodlabel:
				period = 1
			elif '2nd Period' in periodlabel:
				period = 2
			elif '3rd Period' in periodlabel:
				period = 3
			elif 'OT' in periodlabel: 
				period = 'OT'
				OT = True
			elif 'Shootout' in periodlabel:
				period = 'SO'
				SO = True
				OT = False
		cols = row.find_all('td')
		cols = [ele.text.strip() for ele in cols]
		# get goal information
		if len(cols) > 0:
			goaltime = cols[0]
			# convert goaltime MM:SS to seconds
			goaltime = string_to_seconds(goaltime)
			teamfor = cols[1]
			# check if special goal (PP, SH, SO, or EN)
				
			wordlist = cols[2].split('\n\t\t\t')
			if wordlist[0] in ['PP', 'SH', 'SO', 'EN', 'PS']:
				situation = wordlist[0]
				try:
					localidx = next(idx for idx, x in enumerate(wordlist) if '(' in x)
				except: 
					localidx = 0 
				wordlist = wordlist[localidx:]
			else:
				situation = 'EV'
	#		print(wordlist)
			# aho check, if ahocheck then add 2 to Aho name
			if teamfor == 'NYI':
				wordlist = [x+'2' if x == 'Sebastian Aho' else x for x in wordlist ] 
			re_paren = re.search(' \(', wordlist[0]) 
			goalscorer = wordlist[0][:re_paren.start()]			
			if len(wordlist) == 1:
				primaryassist = ''
				secondaryassist = ''
			elif len(wordlist) > 1:
				primaryassist = wordlist[1].strip()
				secondaryassist = ''
			if len(wordlist) > 2:
				re_and = re.search(' and ', wordlist[2])
				secondaryassist = wordlist[2][re_and.end():].strip()
			goallist.append(nhltuples.Goal(goal = goalscorer, gameid = gameid, assist = primaryassist, assist2 = secondaryassist, 
						       time = goaltime, period = period, teamfor = teamfor, situation = situation))
	return goallist, shootoutlist, OT, SO
	
def parseShootout(row, gameid):
	'''
		to do: ahocheck
	'''
	cols = row.find_all('td')
	cols = [x.text.strip() for x in cols if x]
	val = cols[2]
	if 'unsuccessful' in val:
		successful = 0
	else:
		successful = 1
	shooter = val.split(' ')[0:2]
	goalie = val.split(' ')[-2:]
	# combine into one string
	shooter = ' '.join(shooter)
	goalie = ' '.join(goalie)
	return nhltuples.ShootoutAttempt(gameid = gameid, shooter = shooter, goalie = goalie, goal = successful)

def parsePenalty(soup):
	penaltylist = []
	# penalty information
	penaltytable = soup.find('table', {'id': 'penalty'})
	rows = penaltytable.find_all('tr')
	period = 0
	for row in rows:
		periodlabel = row.find('th')
		# check if period changed
		if periodlabel:
			period+=1
		cols = row.find_all('td')
		cols = [ele.text.strip() for ele in cols]
		# get penalty information
		if len(cols) > 0:
			penaltytime = cols[0]
			# convert penaltytime MM:SS to seconds
			penaltytime = string_to_seconds(penaltytime)
			teampenalised = cols[1]
			# players come before the :
			unprocessed = cols[2].split(': ')
			# check if too many men on ice lacks the ':'
			if len(unprocessed) == 1:
				player = teampenalised
				unprocessed = unprocessed[0].split(u' \u2014 ')
			else:
				player = unprocessed[0]
				unprocessed = unprocessed[1].split(u' \u2014 ')
			# remove blanks
			unprocessed = [x for x in unprocessed if x]
			# ahocheck
			if teampenalised == 'NYI':
				if player == 'Sebastian Aho':
					player = 'Sebastian Aho2'
			reason = unprocessed[0]
			try:
				penaltylength = int(unprocessed[1].split(' ')[0])
			except IndexError:
				penaltylength = 0
			penaltylist.append(nhltuples.Penalty(player = player, gameid = gameid, reason = reason, time = penaltytime, 
				minutes = penaltylength, teampenalised = teampenalised, period = period))
#	print('my penalty list {}'.format(penaltylist))
	return penaltylist

def parseSkaters(soup, teamname, gameid, teamagainst, ahoflag):
	skaterlist = []
	skatertable = soup.find('table', {'id': nhltuples.teamDict[teamname] + '_skaters'})
	# row by row
	rows = skatertable.find_all('tr')		
	for row in rows:
		cols = row.find_all('td')
		cols = [ele.text.strip() for ele in cols]
		if len(cols) == 0:
			continue
		name = cols[0]
		if ahoflag:
			if name == 'Sebastian Aho':
				name = 'Sebastian Aho2'
		if name == 'TOTAL':
			teamgoals = cols[1]
			teampim = cols[5]
			teamshots = cols[13]
		goals = cols[1]
		assists = cols[2]
		points = cols[3]
		plus_minus = cols[4]
		pim = cols[5]
		goals_ev = cols[6]
		goals_pp = cols[7]
		goals_sh = cols[8]
		gw = cols[9]
		assists_ev = cols[10]
		assists_pp = cols[11]
		assists_sh = cols[12]
		shots = cols[13]
		shot_percentage = cols[14]
		# convert to double 
		if shot_percentage:
			shot_percentage = float(shot_percentage)
		else:
			shot_percentage = None
		shifts = cols[15]
		toi = cols[16]		
		# convert toi MM:SS to seconds
		toi = string_to_seconds(toi)	
		teamfor = teamname
		teamagainst = teamagainst	
#		print(name)
		# find block shots
		
		skaterlist.append(nhltuples.PlayerGame(name = name, gameid = gameid, teamfor = teamfor, teamagainst = teamagainst, goals = goals, 
						       assists = assists, points = points, plus_minus = plus_minus, pim = pim, goals_ev = goals_ev, 
						       goals_pp = goals_pp, goals_sh = goals_sh, gw = gw, assists_ev = assists_ev, assists_pp = assists_pp, 
						       assists_sh = assists_sh, shots = shots, shot_percentage = shot_percentage, shifts = shifts, toi = toi)) 
	return(skaterlist, teamgoals, teampim, teamshots)
		
def parseAdvanced(soup, teamname, gameid, ahoflag):
	print('parsing advanced stats')
	advancedlist = []
	# find commented out tags
	comments = soup.findAll(text = lambda text:isinstance(text, Comment))
	c = [x for x in comments if 'div_advanced' in x]
	c = c[0]
	commentsoup = BeautifulSoup(c, 'lxml')
	advstats = commentsoup.find('table', {'id': nhltuples.teamDict[teamname] + '_adv'})
	# All situations
	rows = advstats.findAll('tr', {'class': 'ALLAll'})
	for row in rows:
		# get name
		alink = row.find('a')
		if alink is None:
			continue
		name = alink.contents[0]
		if ahoflag:
			if name == 'Sebastian Aho':
				name = 'Sebastian Aho2'
		if name == 'TOTAL':
			continue
		cols = row.find_all('td')
		cols = [ele.text.strip() for ele in cols]
		if len(cols) == 0:
			continue
		cols = [float(x) if x else None for x in cols]

		icf = cols[0]
		satf = cols[1]
		sata = cols[2]
		cfpct = cols[3]
		crel = cols[4]
		zso = cols[5]
		zsd = cols[6]
		ozspct = cols[7]
		if cols[8]:
			hits = int(cols[8])
		else:
			hits = 0
		if cols[9]:		
			blocks = int(cols[9])
		else:
			blocks = 0	
		advancedlist.append(nhltuples.AdvancedStats(name = name, gameid = gameid, icf = icf, satf = satf, sata = sata, cfpct = cfpct, crel = crel, 
							    zso = zso, zsd = zsd, ozspct = ozspct, hits = hits, blocks = blocks))
	return advancedlist

def parseGoalies(soup, teamname, gameid, teamagainst, ahoflag):
	print('parsing goalies')
	goalielist = []
	goalietable = soup.find('table', {'id': nhltuples.teamDict[teamname] + '_goalies'})
	# row by row
	rows = goalietable.find_all('tr')
	for row in rows:
		cols = row.find_all('td')
		cols = [ele.text.strip() for ele in cols]
		if len(cols) == 0:
			continue
		name = cols[0]
		if ahoflag:
			if name == 'Sebastian Aho':
				name = 'Sebastian Aho2'
		result = cols[1]
		if not result:
			result = 'ND'
		ga = int(cols[2])
		sa = int(cols[3])
		sv = int(cols[4])
		try:
			sv_pct = float(cols[5])
		except ValueError:
			sv_pct = None
		so = int(cols[6])
		pim = int(cols[7])
		toi = cols[8]
		# convert toi MM:SS to seconds
		toi = string_to_seconds(toi)
		teamname = teamname
		teamagainst = teamagainst
		goalielist.append(nhltuples.GoalieGame(name = name, gameid = gameid, teamfor = teamname, teamagainst = teamagainst, result = result, 
						       ga = ga, sa = sa, sv = sv, sv_pct = sv_pct, so = so, pim = pim, toi = toi))
	return goalielist
		  
def rewriteFiles(datadir):
	'''
		after downloading html files, there were extra '' 
		before every ', replacing '' '' with ''and writing to 			new files that start with nhl_
	'''
	quote = "\""
	double_quote = quote + quote
	for filename in os.listdir(datadir):
		if 'nhl' in filename:
			continue
		print(filename)
		with open(datadir + filename, 'r') as fin:
			with open(datadir + 'nhl' + filename, 'w') as fout:
				for line in fin:
					fout.write(line.replace(double_quote, quote))

def download_season_stats(link):
	'''
		download stats from https://www.hockey-reference.com/leagues/NHL_2018_skaters.html
	'''
	ua = UserAgent()
	myheader = {'User-Agent': ua.ff} 
	page = requests.get(link, headers = myheader)
	soup = BeautifulSoup(page.content, 'lxml')	
	statstable = soup.find('table', {'id': 'stats'})
	dflist = pd.read_html(link, header = 1)
	df = dflist[0]
	df = df[df['Rk'] != 'Rk']
	df.to_csv('CSVdata/2017/season_stats.csv')

def season_stats_to_sql(seasonendyear):
	try:
		conn = mdb.connect(host = 'localhost',
				user='sasha',
				passwd='sasha92',
				db='fantasy',
                                charset='UTF8')
		cur = conn.cursor()

		# insert and get team ids
		insertplayersseasonq = """INSERT INTO PlayerSeasons(PlayerID, SeasonEndYear, FullName, Age, Goalie, Defender, Center, LeftWing, RightWing, 
		TeamID, GP, Goals, Assists, Points, PlusMinus, PIM, PointShares, Goals_ev, Goals_pp, Goals_sh, GW, Assists_ev, Assists_pp, Assists_sh, Shots, 
		SHpct, TOI, ATOI, Blocks, Hits, FOW, FOL, FOpct) 
		VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
		ON DUPLICATE KEY UPDATE TeamID = TeamID;"""
		csvfile = 'CSVdata/{}/season_stats.csv'.format(seasonendyear)
		df = pd.read_csv(csvfile)
		# convert pd.nan to None
		df = df.where((pd.notnull(df)), None)
		df['ATOI'] = df['ATOI'].apply(lambda x: string_to_seconds(x))

		for index, row in df.iterrows():
			# insert into players
			cur.execute(nhlqueries.insertplayersq, [row['Player']])
			# figure out positions
			(goalie, defender, center, leftwing, rightwing) = 0,0,0,0,0	
			if 'G' in row['Pos']:
				goalie = 1
			if 'D' in row['Pos']:
				defender = 1
			if 'C' in row['Pos']:
				center = 1
			if 'LW' in row['Pos']:
				leftwing = 1
			if 'RW' in row['Pos']:
				rightwing = 1
			# get player id
			cur.execute(nhlqueries.selectplayerid, [row['Player']])
			playerid = cur.fetchone()
			# get team id 
			cur.execute(nhlqueries.selectteamid_abbrev, [row['Tm']])
			teamid = cur.fetchone()
			executablelist = [playerid, seasonendyear, row['Player'], row['Age'], goalie, defender, center, leftwing, rightwing, teamid]
			executablelist.extend(list(row[6:]))
			if row['Player'] == 'Patrik Berglund':
				print(executablelist)
			cur.execute(insertplayersseasonq, executablelist)
			conn.commit()
	except mdb.Error, e:
		print(e)
	finally:
		if conn:
			conn.close()
def string_to_seconds(timestring, separator = ':'):
	# convert toi MM:SS to seconds
	if timestring:
		timestring = timestring.split(':')
		toi = int(timestring[0])*60 + int(timestring[1])
	else:
		return None
	return toi	

def parseDraftkings(filename):
	df = pd.DataFrame.from_csv(filename, header = 6)
	# remove columns without names
	colskeep = [x for x in df.columns if 'Unnamed' not in x]
	# remove columns with NAs from the df
	df.dropna(axis = 1, how = 'all', inplace = True)
	df.columns = colskeep
	# drop name+ID column
	df.drop('Name + ID', axis = 1, inplace = True)
	return df

def draftkingsToSql(df):
	dfnames = pd.DataFrame.from_csv('/home/sasha/Dropbox/fantasy/fantasy/misc/names.csv', index_col = None)
	namesdict = {}
	for idx, row in dfnames.iterrows():
		draftname = row['DraftKingsName'].strip()
		hrname = row['HockeyReferenceName'].strip()
		namesdict[draftname] = hrname
	try:
		conn = mdb.connect(host = 'localhost',
				user='sasha',
				passwd='sasha92',
				db='fantasy',
                                charset='UTF8')
		cur = conn.cursor()

		for idx, row in df.iterrows():
			print(row)
			# ignore players who have salary of 2500
			
			player = row['Name']
			cur.execute(nhlqueries.selectplayerid, [player])
			skater_id = cur.fetchone()
		
			if skater_id == None:
				print('------------------')
				print(player)
				print(row['Salary'])
				# search by last name and another first name
				if player in namesdict.keys():
					draftname = namesdict[player]
					cur.execute(nhlqueries.selectplayerid, [draftname])
					skater_id = cur.fetchall()
					if skater_id == None:
						print('still null')
					else: 
						if len(skater_id) > 1:
							print('multiple skaters with the last name')
						else:	
							# get name in the database
							cur.execute(nhlqueries.selectplayername, [skater_id])
							skater_name = cur.fetchone()
							print(skater_name)
			#######
			if skater_id != None:
				# update player
				cur.execute(nhlqueries.updateplayersdraftkings, [player, row['ID'], skater_id])
			# fullteam name
			
			fullteam = nhltuples.draftkingsDict[row['TeamAbbrev ']]			
			# get team id
			cur.execute(nhlqueries.selectteamid, [fullteam])
			teamforid = cur.fetchone()

			# get gameinfo
			gameinfo = row['GameInfo'].split() 
			teams = gameinfo[0]
			hometeam = teams.split('@')[1]
			awayteam = teams.split('@')[0]
			datestring ='{}{}'.format(gameinfo[1],gameinfo[2])

			gamedate = dt.datetime.strptime( datestring, '%m/%d/%Y%I:%M%p')
			#gamedate = gamedate.date()

			hometeamabbrev = nhltuples.draftkingsDict[hometeam]
			awayteamabbrev = nhltuples.draftkingsDict[awayteam]
			
			# get more team ids
			cur.execute(nhlqueries.selectteamid, [hometeamabbrev])
			hometeamid = cur.fetchone()
			cur.execute(nhlqueries.selectteamid, [awayteamabbrev])
			awayteamid = cur.fetchone()

			if teamforid == hometeamid:
				teamagainstid = awayteamid
			else:
				teamagainstid = hometeamid
			# insert into draftkings
			# PlayerName, HomeTeamID, AwayTeamID, TeamForID, TeamAgainstID, GameDate, PlayerDraftKingsID, DraftKingsName, Position, RosterPosition
			cur.execute(nhlqueries.insertdraftkingsq,(player, hometeamid, awayteamid, teamforid, teamagainstid, gamedate, row['ID'], 
								  row['Salary'], row['Position'], row['Roster Position']))
			conn.commit()
	except mdb.Error, e:
		print(e)
	finally:
		if conn:
			conn.close()

def run_draftkings(season, gamedate):
	kingsfile =  '/home/sasha/Dropbox/fantasy/fantasy/CSVdata/{}/draftkings/DKSalaries{}-{}-{}.csv'.format(season, gamedate.year, gamedate.month, gamedate.day)
	df = parseDraftkings(kingsfile)
	draftkingsToSql(df)

if __name__ == '__main__':
	#download_season_stats('https://www.hockey-reference.com/leagues/NHL_2017_skaters.html')
	# go through files
	firstid = 1
	season = 2018
	playoffs = dt.datetime(2018, 4, 12)
	gameid = firstid
	datadir = 'data/{}/new/'.format(season)
##	rewriteFiles(datadir)
	myfiles = os.listdir(datadir)
	myfiles.sort()
	for filename in myfiles:
		if 'nhl' in filename: 
			myf = codecs.open(datadir + filename, 'r')
			soup = BeautifulSoup(myf, 'lxml')
			myf.close()
		# parse through soup
			parseSoup(soup, gameid, firstid, season, playoffs)
			gameid += 1
			# move file to the archive folder
	
			os.rename(datadir + filename, datadir.replace('new', 'archive') + filename)

	# draftkings filename
	#run_draftkings(season)
	#season_stats_to_sql(season)

		
