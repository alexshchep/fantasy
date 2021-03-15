import csv
import numpy as np
import pandas as pd
import datetime as dt
	

class Player():
    def __init__(self, position, name, salary, points, value):
        self.self = self
        self.position = position
        self.name = name
        self.salary = salary
        self.points = points
        self.value = value
        
    def __iter__(self):
        return iter(self.list)
    
    def __str__(self):
        return "{} {} {} {}".format(self.name,self.position,self.salary, self.points)

class Game():
	def __init__(self):
		self.self = self
		self.players = pd.DataFrame()
		self.gamers = []
# 		self.centers= []
# 		self.wingers = []
# 		self.defenders = []
# 		self.goalies = []
# 		self.utils = []
		self.salaryLimit = 50000
	def getPlayers(self):
		df = pd.read_csv('DKSalaries.csv', header = 0)
	#	print(df)
		# csv_file_object = csv.reader(open('DKSalaries.csv', 'r'))       # Load in the csv file
		# header = csv_file_object.next()
		# data =[]
		# for row in csv_file_object:                 # Skip through each row in the csv file
		# 	data.append(row) 
		#print(self.players)
		self.players = df.copy()
		self.players['Value'] = df['AvgPointsPerGame'] / df['Salary']
	#	print(self.players)

	def getPlayersAlgo(self, myday):
		# get predictions
		df = pd.read_csv('results/today_players_all_{}_{}_{}.csv'.format(myday.year, myday.month, myday.day))

		df['Value'] = df['prediction_pts'] / df['Salary']
		self.players = df.copy()

	# get players from the hockeyanalysis website csv
	def getPlayersCSV(self):
		df = pd.read_csv('PuckalyticsSkaterStats.csv', header = 0)
		df2 = pd.read_csv('PuckalyticsGoalieStats.csv', header = 0)
		df = df.append(df2)
		#df[['GP']] = df[['gp']].apply(pd.to_numeric)
		df = df[df['GP'] >=19]
		#df['Name'] = df['Player'].str.upper()
	#	df = df[["Name", "GP"]]
		#print(len(self.players))
		# combine first and last name into one name
		df['Name'] = ''
		for idx, player in df.iterrows():
			df['Name'].iloc[idx] = (player['FirstName'] + " " + player['LastName']).lstrip()
	#		df = self.convertValues(df, 'Pos', )
		
		self.players['Name'] = self.players['Name'].str.upper()
		self.players = pd.merge(self.players, df, how='inner', on=['Name'])
		#print(self.players)
		
		#print(len(result))
	#	with pd.option_context('display.max_rows', 999, 'display.max_columns', 7):
			#print (result)
		#self.players['GP'] = df['gp']
		
	# playernames is a list
	def removePlayers(self, playernames):
		self.players = self.players[~self.players['Name'].isin(playernames)]
	def dfToPlayers(self, df):
		playerlist = []
		for idx, player in df.iterrows():
			tempPlayer = Player(position = player['Position'],
							 name = player['Name'], 
							 salary = player['Salary'], 
							 points = player['AvgPointsPerGame'], 
							 value = player['Value'])
			playerlist.append(tempPlayer)
		return playerlist
	def getStatsFromWebsite(self, site):
		from lxml import html
		import requests
		site = 'https://stats.hockeyanalysis.com/ratings.php?db=201617&sit=all&type=individual&teamid=0&pos=skaters&minutes=1&disp=1&sort=PCT&sortdir=DESC'
		page = requests.get(site)
		tree = html.fromstring(page.content)
	def convertValues(self, df, colname = 'Position', changefrom = ['LW', 'RW'], changeto = 'W'):
	#	print(self.players)
		for idx, player in df.iterrows():
			if player[colname] in changefrom:
				#print(self.players['Position'][idx])			
				df[colname][idx] = changeto
				#print(self.players['Position'][idx])
		return df
	def convertWingers(self):
	#	print(self.players)
		for idx, player in self.players.iterrows():
			if player['Position'] in ['LW', 'RW']:
				#print(self.players['Position'][idx])			
				self.players['Position'][idx] = 'W'
				#print(self.players['Position'][idx])

class Knapsack():
	def __init__(self, data, salarymax, numplayers):
		self.self = self
		# data has columns Value and Salary
		self.data = data
		

		#self.data.sort(key = lambda x: x.Value, reverse = True)
		# salarymax is capacity
		self.salarymax = salarymax
		# solution is matrix of size (number of players  x (length salarymax / increments between salaries))
		# numplayers is number of players to be picked
		self.numplayers = numplayers
		self.sortedbysalary = False
		print(len(data.index))
		print (salarymax/100)
		self.solution = np.zeros((len(data.index), int(salarymax/100)))
		self.constraints = {
			'C': 2,
			'W': 3,
			'D': 2,
			'G': 1,
			'UTIL': 1
		}
		self.counts = {
			'C': 0,
			'W': 0,
			'D': 0,
			'G': 0,
			'UTIL': 0
		}	
	def solveKnapsack(self, method, budget = 50000):
		if method == 'value':
			myteam = self.valueKnapsack(budget)
			return myteam
	def valueKnapsack(self, budget, utillist = ['C', 'W', 'D']):
		# http://sambrady3.github.io/knapsack.html
		colstokeep = ['Position', 'Name', 'Salary', 'Value', 'AvgPointsPerGame', 'GP' ]
		self.data = self.data[colstokeep]
		team = []
		# need to substitute to IDs
		currentsalary = 0
		# first, pick all the best value players
		minsal = {'G': min(self.data['Salary'][self.data['Position'] == 'G']),
				'D':min(self.data['Salary'][self.data['Position'] == 'D']),
				'C': min(self.data['Salary'][self.data['Position'] == 'C']),
				'W': min(self.data['Salary'][self.data['Position'] == 'W'])}
		minsal['UTIL'] = min(minsal['C'], minsal['D'], minsal['W'])
		
		self.data.sort(['Value'], ascending = False, inplace = True )
		for idx, player in self.data.iterrows():

			pos = player['Position']
			sal = player['Salary']
			if (self.counts[pos] < self.constraints[pos] and 
					(currentsalary + sal +minsal[pos] <= budget or 
					(len(team) + 1 == sum(self.constraints.values()) and currentsalary + sal <= budget))):
				team.append(player)
				self.counts[pos] = self.counts[pos] + 1
				currentsalary += sal
				continue
			if (self.counts['UTIL'] < self.constraints['UTIL'] and
					pos in utillist and
			 		(currentsalary + sal +minsal[pos]  <= budget or 
					currentsalary + sal <= budget and len(team) + 1 == sum(self.constraints.values()))):
				team.append(player)
				self.counts['UTIL'] = self.counts['UTIL'] + 1
				currentsalary += sal
		# Second, pick all the best players
		self.data.sort(['AvgPointsPerGame'], ascending = False, inplace = True)
		for idx, player in self.data.iterrows():
			name = player['Name']
			pos = player['Position']
			sal = player['Salary']
			# val = player['Value']
			# gp = player['gp']
			pts = player['AvgPointsPerGame']
			teamnames = [x['Name'] for x  in team]
			if name not in teamnames:
				pos_players = [x for x in team if x['Position'] == pos]
				pos_players.sort(key = lambda x: x['AvgPointsPerGame'])
				# replace the least valuable player first
#				pos_players.sort(key = lambda x: x['Value'], reverse = True)
				for pos_player in pos_players:
					if(currentsalary + sal - pos_player['Salary'] <= budget and pts > pos_player['AvgPointsPerGame']):
						team[teamnames.index(pos_player['Name'])] = player
						currentsalary = currentsalary + sal - pos_player['Salary']
						break
		return team
	# def solveKnapsack(self):
	# 	shape = self.solution.shape
	# 	# n is number of distinct items (players)
	# 	# w is different possible capacities of a knapsack
	# 	n = shape[0] 
	# 	w = shape[1] 
	# 	keep = np.zeros((n, w))
	# 	print(len(self.data))
	# 	for i in range(1,10):
	# 		#print("/n")
	# 		for j in range(0,w):
	# 			# check that this players salary isnt too high
	# 			numplayersleft = self.getNumPlayersLeft(keep, i, j)	
	# 			print('player is {}, his salary is {}'.format(self.data['Name'][i], self.data['Salary'][i]))
	# 			print('min salary is {}, salary left after getting him is {}'.format(self.getMinSalary(numplayersleft), j * 100- self.data['Salary'][i]))
	# 			print('current position is {}.format'(j*100))

	# 			if (self.data['Salary'][i] > j * 100) or (self.getMinSalary(numplayersleft) > (j * 100) - self.data['Salary'][i] ):
	# 	#		if (self.data['Salary'][i] > j * 100):
	# 				self.solution[i,j] = self.solution[i-1, j]
	# 				print("not picking him")
	# 				#keep[i,j] = 0
	# 			elif (self.solution[i-1,j-self.data['Salary'][i]/100] + self.data['AvgPointsPerGame'][i] > self.solution[i-1, j] ):
	# 			#	pdb.set_trace()
	# 				self.solution[i,j] =  self.solution[i-1,j-self.data['Salary'][i]/100] + self.data['AvgPointsPerGame'][i]
	# 				print('player {} was chosen'.format(self.data['Name'][i]))
	# 				keep[i,j] = 1
	# 			else:
	# 				self.solution[i,j] = self.solution[i-1, j]
	# 				#keep[i,j] = 0
	# 			print(self.getPlayersPicked(keep))
				
	# 	return keep
		# for index, row in df.iterrows():
		# 	#print(index)
		# 	name = row[1]
		# 	position = row[0]
		# 	salary = int(row[2])
		# 	points = float(row[4])
		# 	value = points / salary
		# 	player = Player(position, name, salary, points, value)
		# 	players.append(player)

	def getPlayersPicked(self, keep):
		shape = self.solution.shape
		# n is number of distinct items (players)
		# w is different possible capacities of a knapsack
		n = shape[0] - 1
		w = shape[1] - 1
		playerspicked = []
		while (n > 0):
			if (keep[n][w] == 0):
				n = n - 1
			else:
				n = n - 1
				w = w - self.data['Salary'][n] / 100	
				playerspicked.append(self.data['Name'][n+1])
		print(playerspicked)
	def sortBySalary(self):
		if (self.sortedbysalary == False):
			self.data.sort(['Salary'], descending = True, inplace = True)
			self.sortedbysalary = True
	def getMinSalary(self, numPlayersLeft):
		df = self.data.copy()
		shape = self.solution.shape
		# n is number of distinct items (players)
		# w is different possible capacities of a knapsack
		n = shape[0]

		sumsalary = 0
		for i in range(1,numPlayersLeft):
			sumsalary = sumsalary + self.data['Salary'][n-i]
		return sumsalary
	def getNumPlayersLeft(self , keep, currentplayer, currentweight):
		shape = self.solution.shape
		# n is number of distinct items (players)
		# w is different possible capacities of a knapsack
		n = currentplayer - 1
		w = currentweight 
		numPlayersLeft = self.numplayers
		while (n > 0):
			# if(currentplayer == 17):
			# 	print('{} {} {}'.format(currentplayer, n, w))
			if (keep[n][w] == 0):
				n = n - 1
			else:
				n = n - 1
				w = w - self.data['Salary'][n] / 100	
				numPlayersLeft = numPlayersLeft - 1
		return numPlayersLeft
if __name__ == '__main__':
	import pdb; print(pdb.__file__) ;
	
	nhl = Game()
	
	test = nhl.getPlayers()
	nhl.getPlayersCSV()
	nhl.players = nhl.convertValues(nhl.players)
	#pdb.set_trace()
	nhl_knapsack = Knapsack(nhl.players, 50000, 9 )
	#pdb.set_trace()
	keep1 = nhl_knapsack.solveKnapsack('value')
	print(keep1)
	#nhl_knapsack.getPlayersPicked(keep1)
	totalsal = 0
	totalval = 0
	for idx, val in enumerate(keep1):
		print(val['Salary'])
		totalsal += val['Salary']
		totalval += val['AvgPointsPerGame']
	print('total sal is {}'.format(totalsal))
	print('total avg points per game is {}'.format(totalval))
