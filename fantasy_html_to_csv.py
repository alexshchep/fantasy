import os 
import sys
import re
import codecs
import bs4
import csv
import requests
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
from bs4 import Comment
from collections import namedtuple
from fake_useragent import UserAgent

# import named tuples
import nhltuples

def parseSoup(soup, gameid, firstid):
	'''

	'''
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
	print('away team is_{}, home team is_{}.'.format(away, home))
	featurelist.append(nhltuples.Feature(name = 'away', value = away))
	featurelist.append(nhltuples.Feature(name = 'home', value = home))
	# scorebox information
	attendance, arena, gameduration, gamedate = parseInformation(soup)
	# goal information
	goallist, shootoutlist, OT, SO = parseScoring(soup)
	# parse soup for Penalties
	penaltylist = parsePenalty(soup)
	awayskaterlist, awayscore = parseSkaters(soup, teamname = away, gameid = gameid, teamagainst = home)
	awayadvancedlist = parseAdvanced(soup, away, gameid)
	awaygoalielist = parseGoalies(soup, away, gameid, home)
	homeskaterlist, homescore = parseSkaters(soup, teamname = home, gameid = gameid, teamagainst = away)
	homeadvancedlist = parseAdvanced(soup, home, gameid)
	homegoalielist = parseGoalies(soup, home, gameid, away)
	gameinfo = nhltuples.Game(gameid = gameid, away = away, home = home, date = gamedate, attendance = attendance, arena = arena, 
		duration = gameduration, awayscore = awayscore, homescore = homescore, OT = OT, SO = SO)
#	print('goals:\n{}'.format(goallist))
#	print('penalties:\n{}'.format(penaltylist))
#	print('away skaters:\n{}'.format(awayskaterlist))
#	print('away goalies:\n{}'.format(awaygoalielist))
#	print('home skaters:\n{}'.format(homeskaterlist))
#	print('home goalies:\n{}'.format(homegoalielist))
#	print('game info is: \n{}'.format(gameinfo))
#	print('\n')
	# to csv
	writeToCSV('goals.csv', goallist, ['goal', 'gameid', 'assist', 'assist2', 'time', 'period', 'teamfor', 'situation'], gameid, True, firstid=firstid) 
	writeToCSV('shootouts.csv', shootoutlist, ['gameid', 'shooter', 'goalie', 'goal'], gameid, True, firstid=firstid)
	writeToCSV('penalties.csv', penaltylist, ['player', 'gameid', 'minutes', 'reason', 'time', 'period', 'teampenalised'], gameid, True, firstid=firstid)
	writeToCSV('skaters.csv', awayskaterlist, ['name', 'gameid', 'teamfor', 'teamagainst', 'goals','assists', 'points', 'plus_minus', 'pim', 'goals_ev', 
						   'goals_pp', 'goals_sh','gw', 'assists_ev', 'assists_pp', 'assists_sh', 'shots', 'shot_percentage', 'shifts', 'toi'],
		   gameid, True, firstid=firstid)
	writeToCSV('skaters.csv', homeskaterlist, ['name', 'gameid', 'teamfor', 'teamagainst', 'goals','assists', 'points', 'plus_minus', 'pim', 'goals_ev', 'goals_pp', 
						   'goals_sh', 'gw', 'assists_ev', 'assists_pp', 'assists_sh', 'shots', 'shot_percentage', 'shifts', 'toi'], 
		   gameid, False, firstid=firstid)
	writeToCSV('advanced.csv', awayadvancedlist, ['name',  'gameid', 'icf', 'satf', 'sata', 'cfpct', 'crel', 'zso', 'zsd', 'ozspct', 'hits', 'blocks'], 
		   gameid, True, firstid = firstid)
	writeToCSV('advanced.csv', homeadvancedlist, ['name',  'gameid', 'icf', 'satf', 'sata', 'cfpct', 'crel', 'zso', 'zsd', 'ozspct', 'hits', 'blocks'], 
		   gameid, False, firstid = firstid)
	writeToCSV('goalies.csv', awaygoalielist, ['name', 'gameid', 'teamfor', 'teamagainst', 'result', 'ga', 'sa', 'sv', 'sv_pct', 'so', 'pim', 'toi'], 
		   gameid, True, firstid = firstid)
	writeToCSV('goalies.csv', homegoalielist, ['name', 'gameid', 'teamfor', 'teamagainst', 'result', 'ga', 'sa', 'sv', 'sv_pct', 'so', 'pim', 'toi'], 
		   gameid, False, firstid = firstid)
	writeToCSV('gameinfo.csv', [gameinfo], ['gameid', 'away', 'home', 'date', 'attendance', 'arena', 'duration', 'awayscore', 'homescore', 'OT', 'SO'], 
		   gameid, True, firstid = firstid)

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
	# print(len(scorebox))
	for data in scorebox:
		mylist = data.contents
		for val in mylist:
			if type(None) == type(val.string):
				for val2 in val:
					if isinstance(val2, bs4.element.Tag):
						print('this is a tag {}'.format(val2))
						featname = val2.string
					if isinstance(val2, bs4.element.NavigableString):
						print('this is a Navigable String {}'.format(val2))
						featvalue = val2
						if featname == 'Attendance':
							attendance = featvalue[2:]
						elif featname == 'Arena':
							arena = featvalue[2:]
						elif featname == 'Game Duration':
							gameduration = featvalue[2:]
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
	#	print('row is {}'.format(row))
		# check if shootout flag is on
		if SO:
	#		print('row is {} \n end row...'.format(row))
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
			teamfor = cols[1]
			# check if special goal (PP, SH, SO, or EN)
				
			wordlist = cols[2].split('\n\t\t\t')
			if wordlist[0] in ['PP', 'SH', 'SO', 'EN']:
				situation = wordlist[0]
				try:
					localidx = next(idx for idx, x in enumerate(wordlist) if '(' in x)
				except: 
					localidx = 0 
				wordlist = wordlist[localidx:]
			else:
				situation = 'EV'
	#		print(wordlist)
			re_paren = re.search(' \(', wordlist[0]) 
			goalscorer = wordlist[0][:re_paren.start()]
			if len(wordlist) == 1:
				primaryassist = ''
				secondaryassist = ''
			elif len(wordlist) > 1:
				primaryassist = wordlist[1]
				secondaryassist = ''
			if len(wordlist) > 2:
				re_and = re.search(' and ', wordlist[2])
				secondaryassist = wordlist[2][re_and.end():]
			goallist.append(nhltuples.Goal(goal = goalscorer, gameid = gameid, assist = primaryassist, assist2 = secondaryassist, time = goaltime, 
						       period = period, teamfor = teamfor, situation = situation))
	return goallist, shootoutlist, OT, SO
	
def parseShootout(row, gameid):
	
	cols = row.find_all('td')
	cols = [x.text.strip() for x in cols if x]
	val = cols[2]
	print('-------------')
	print(val)
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
			reason = unprocessed[0]
			penaltylength = int(unprocessed[1].split(' ')[0])
			penaltylist.append(nhltuples.Penalty(player = player, gameid = gameid, reason = reason, time = penaltytime, 
				minutes = penaltylength, teampenalised = teampenalised, period = period))
#	print('my penalty list {}'.format(penaltylist))
	return penaltylist

def parseSkaters(soup, teamname, gameid, teamagainst):
#	print('team name is {}'.format(teamname))
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
		if name == 'TOTAL':
			teamgoals = cols[1]
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
		shifts = cols[15]
		toi = cols[16]			
		teamfor = teamname
		teamagainst = teamagainst	
#		print(name)
		# find block shots
		
		skaterlist.append(nhltuples.PlayerGame(name = name, gameid = gameid, teamfor = teamfor, teamagainst = teamagainst, goals = goals, 
						       assists = assists, points = points, plus_minus = plus_minus, pim = pim, goals_ev = goals_ev, 
						       goals_pp = goals_pp, goals_sh = goals_sh, gw = gw, assists_ev = assists_ev, assists_pp = assists_pp, 
						       assists_sh = assists_sh, shots = shots, shot_percentage = shot_percentage, shifts = shifts, toi = toi)) 
	return(skaterlist, teamgoals)
		
def parseAdvanced(soup, teamname, gameid):
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
		if name == 'TOTAL':
			continue
		cols = row.find_all('td')
		cols = [ele.text.strip() for ele in cols]
		if len(cols) == 0:
			continue			
		icf = cols[0]
		satf = cols[1]
		sata = cols[2]
		cfpct = cols[3]
		crel = cols[4]
		zso = cols[5]
		zsd = cols[6]
		ozspct = cols[7]
		hits = cols[8]
		blocks = cols[9]
		advancedlist.append(nhltuples.AdvancedStats(name = name, gameid = gameid, icf = icf, satf = satf, sata = sata, cfpct = cfpct, crel = crel, 
							    zso = zso, zsd = zsd, ozspct = ozspct, hits = hits, blocks = blocks))
	return advancedlist

def parseGoalies(soup, teamname, gameid, teamagainst):
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
		result = cols[1]
		ga = cols[2]
		sa = cols[3]
		sv = cols[4]
		sv_pct = cols[5]
		so = cols[6]
		pim = cols[7]
		toi = cols[8]
		teamname = teamname
		teamagainst = teamagainst
		goalielist.append(nhltuples.GoalieGame(name = name, gameid = gameid, teamfor = teamname, teamagainst = teamagainst, result = result, 
						       ga = ga, sa = sa, sv = sv, sv_pct = sv_pct, so = so, pim = pim, toi = toi))
	return goalielist
		  
def rewriteFiles(dataloc):
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

if __name__ == '__main__':
	download_season_stats('https://www.hockey-reference.com/leagues/NHL_2017_skaters.html')
	# go through files
#	datadir = 'data/2018/'
#	firstid = 1318
#	gameid = firstid
##	rewriteFiles(datadir)
#	myfiles = os.listdir(datadir)
#	myfiles.sort()
#	for filename in myfiles:
#		if 'nhl' in filename  in filename:
#			myf = codecs.open(datadir + filename, 'r')
#			soup = BeautifulSoup(myf, 'lxml')
#			myf.close()
#		# parse through soup
#			parseSoup(soup, gameid, firstid)
#			gameid += 1
#
		
