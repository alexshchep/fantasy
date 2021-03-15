import random
import sys
import math
from operator import add
import matplotlib.pyplot as plt
from sklearn.cluster.tests.test_affinity_propagation import centers
#import players
from nhl_draftkings import *
import copy

#%matplotlib inline

'''  team = {
  'qb' : random.sample(qbs,1),
  'rb' : random.sample(rbs,2),
  'wr' : random.sample(wrs,3),
  'te' : random.sample(tes,1),
  'flex' : random.sample(flexs,1),
  'dst' : random.sample(dsts,1)
  }'''
  
class GeneticTeam():
    def __init__(self):
        self.self = self
        self.team = {}
        self.budget = 50000 
        self.sport = 'nhl'  
        self.points = 0
        self.salary = 0
        
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
    def addPlayers(self, position, players):
        mylength = len(players)
        for i in range(0, mylength):
            player = players[i]
            if not position in self.team.keys():
                self.team[position] = [player]
                self.points += player.points
                self.salary += player.salary
            else: 
                self.team[position].append(player)
                self.points += player.points
                self.salary += player.salary
     
    def removeallPlayersFromPosition(self, position, players):
        for player in players:
            self.points -= player.points
            self.salary -= player.salary
        del self.team[position]
    
    def playerPosition(self, position, player):
        pname = player.name
        poslist = []
        utillist = []
        extralist = []
        if position in self.team.keys():
            poslist = [x.name for x in self.team[position]]
        if 'UTIL' in self.team.keys():
            utillist = [x.name for x in self.team['UTIL']]
        if position == 'UTIL':
            if 'W' in self.team.keys():
                extralist.extend([x.name for x in self.team['W']])
            if 'C' in self.team.keys():
                extralist.extend([x.name for x in self.team['C']])
            if 'D' in self.team.keys():
                extralist.extend([x.name for x in self.team['D']])
        namelist = poslist + utillist + extralist
        #utillist = [x.name in x for self.team['UTIL']]
        return pname in namelist 
        
    def printTeamNames(self):
        for key, val in self.team.items():
            print(key)
            for player in val:
                print(player.name)
    
    def GetTeamPointTotal(self):
#         for pos, players in self.team.iterrows():
#             for player in players:
#                 self.total_points += player.points
#         return self.points
        return self.points
    def GetSalary(self):
        return self.salary
    def fitness(self):
        if self.salary > self.budget:
            return 0
        else: 
            return self.points   
        
    
    
      
class Hockey(Game):
    def __init__(self):
        Game.__init__(self)
        self.sport = 'nhl'   
        self.teams = []
        self.wingers = []
        self.centers = []
        self.defenders = []
        self.goalies = []
        self.utils = []
    def playersByPosition(self):
        for idx, player in enumerate(self.gamers):
            if player.position == 'C':
                self.centers.append(player)
                self.utils.append(player)
            elif player.position == 'W':
                self.wingers.append(player)
                self.utils.append(player)
            elif player.position == 'D':
                self.defenders.append(player)
                self.utils.append(player)
            else:
                self.goalies.append(player)        
    def getPlayersPosition(self, pos):
        if pos == 'C':
            positionplayers = self.centers
        elif pos == 'D':
            positionplayers = self.defenders
        elif pos == 'W':
            positionplayers = self.wingers
        elif pos == 'G':
            positionplayers = self.goalies
        else:
            positionplayers = self.utils     
        return positionplayers  
#     def playersByPosition(self):
#         for idx, player in self.players.iterrows():
#             if player['Position'] == 'C':
#                 self.centers.append(player)
#                 self.utils.append(player)
#             elif player['Position'] == 'W':
#                 self.wingers.append(player)
#                 self.utils.append(player)
#             elif player['Position'] == 'D':
#                 self.defenders.append(player)
#                 self.utils.append(player)
#             else:
#                 self.goalies.append(player)        
    def CreatePopulation(self, count):
        return [self.CreateRandomTeam(sport = 'nhl') for i in range(0, count)]    
    def CreateRandomTeam(self, sport = 'nhl'):
        newteam = GeneticTeam()
        if sport == 'nhl':
            #centers_temp = sample(self.centers, 2)
            
            newteam.addPlayers('C', random.sample(self.centers,2))
            newteam.addPlayers('W', random.sample(self.wingers,3))
            newteam.addPlayers('D', random.sample(self.defenders,2))
            newteam.addPlayers('G', random.sample(self.goalies,1))
            newteam.addPlayers('UTIL', random.sample(self.utils,1))
#             newteam.team = {
#                 'C': sample(self.centers,2),
#                 'W': sample(self.wingers,3),
#                 'D': sample(self.defenders,2),
#                 'G': sample(self.goalies,1),
#                 'UTIL': sample(self.utils,1)
#                 }
        whilecounter = 0
        while True:
            whilecounter += 1
            if whilecounter >= 100:
                whilecounter = 100
            print('while loop')
            sys.stdout.flush()
            ut = newteam.team['UTIL'][0]
            utname = ut.name
            longlist = []
            for key, val in newteam.team.items():
                if key == 'UTIL':
                    continue
                for val2 in val:
                    longlist.append(val2)

            
            newteamnames = [x.name for x in longlist]
            if utname in newteamnames:
                newteam.removeallPlayersFromPosition('UTIL', newteam.team['UTIL'] )
                newteam.addPlayers('UTIL', random.sample(self.utils,1))
            else:
                break
        return newteam
    def grade(self, pop):
        summed = 0
        for team in pop:
            summed += team.points
        return summed / (len(pop) * 1.0) 
    def evolve(self, pop, retain = 0.35, random_select = 0.05):
        rankings = [(team.fitness(), team) for team in pop]
        #descending order
        rankings = [x[1] for x in sorted(rankings, key = lambda rank: rank[0], reverse = True)]
        retain_length = int(len(rankings)* retain)
        parents = rankings[:retain_length]
        
        # randomly add other individuals to promote genetic diversity
        for individual in rankings[retain_length:]:
            if random_select > random.random():
                parents.append(individual)
        for individual in parents:        
            individual =  self.mutation(individual)
        
        # create children
        parents_length = len(parents)
        desired_length = len(pop) - parents_length
        children = []
        while len(children) < desired_length:
            male = random.randint(0, parents_length - 1)
            female = random.randint(0, parents_length -1)
            if male != female:
                male = parents[male]
                female = parents[female]
                babies = self.breed(female.team, male.team)
                for baby in babies:
                    children.append(baby)
        parents.extend(children)
        return parents
    def breed(self, mother, father):
        son = GeneticTeam()
        daughter = GeneticTeam()
    #   mother = mother.sort(key = lambda x: x.position)
    #   father = father.sort(key = lambda x: x.position)
        for pos, value in mother.items():
            for idx, player in enumerate(value):
            # will allow players to repeat on the same team               
                mom = player
                dad = father[pos][idx]
                randnum = random.randint(0,1)
                if randnum == 0: 
                    # if true, player already on the team
                    while son.playerPosition(pos, mom):     
                        mom = random.choice(self.getPlayersPosition(pos))
                    son.addPlayers(pos, [mom])
                    while daughter.playerPosition(pos, dad):
                        dad = random.choice(self.getPlayersPosition(pos))
                    daughter.addPlayers(pos, [dad])
                else:
                    while son.playerPosition(pos, dad):
                        dad = random.choice(self.getPlayersPosition(pos))
                    son.addPlayers(pos, [dad])
                    while daughter.playerPosition(pos, mom):
                        mom = random.choice(self.getPlayersPosition(pos))
                    daughter.addPlayers(pos, [mom])
        return[son, daughter]  
    def mutation(self, team):
        for key, value in team.team.items():
            for idx, player in enumerate(value):
                randnum = random.randint(0,20)
                if randnum <= 0:  
                    pos = key
                    positionplayers = self.getPlayersPosition(pos)
                    if randnum <= 0:
                        tempplayer = random.choice(positionplayers)
                        while team.playerPosition(pos, tempplayer):
                            tempplayer = random.choice(positionplayers)
                        team.points -= team.team[pos][idx].points
                        team.salary -= team.team[pos][idx].salary
                        team.points += tempplayer.points
                        team.salary += tempplayer.salary
                        team.team[pos][idx] = tempplayer
                        
                
        return team

    def keepCols(self, colstokeep = ['Position', 'Name', 'Salary', 'Value', 'AvgPointsPerGame', 'GP' ] ):
        # http://sambrady3.github.io/knapsack.html
        self.players = self.players[colstokeep]

    def generate(nhl, numsims = 20, numlevels = 40):
    	    best_teams = [] 
    	    history = []
	    for j in range(0, numsims):
		print('Simulation {}'.format(j))
		p = nhl.CreatePopulation(10000)
		fitness_history = [nhl.grade(p)]
		for i in range(0, numlevels):
		    print('**************************************')
		    print('Generation level {}'.format(i))
		    p = nhl.evolve(p)
		    fitness_history.append(nhl.grade(p))
		    print(fitness_history)
		    valid_teams = [team for team in p if team.salary <= 50000]
		    valid_teams.sort(key=lambda x: x.points, reverse=True)
	    #         for idx, team in enumerate(valid_teams):
	    #             print(team.salary)
		   # for team in valid_teams:
		   #     print(team.GetSalary())
		    if len(valid_teams) > 0:
			    tempteam = copy.deepcopy(valid_teams[0])
			    best_teams.append(tempteam)
			    print(valid_teams[0].salary)
		    for datum in fitness_history:
			    history.append(datum)   
		    best_teams = sorted(best_teams, key = lambda x: x.points, reverse = True)    
		    my_choice = best_teams[0] 
	    for ateam in best_teams[0:10]:
		print('*********************************************')
		ateam.printTeamNames()
		print(ateam.points)
		print(ateam.salary)
    
if __name__ == '__main__':

    nhl = Hockey()
    nhl.getPlayers()
    nhl.getPlayersCSV()
    nhl.keepCols()
    nhl.players = nhl.convertValues(nhl.players)
    deletelist = ['STEVEN STAMKOS', 'MITCHELL MARNER', 'TRAVIS HAMONIC']
    nhl.removePlayers(deletelist)
    nhl.gamers = nhl.dfToPlayers(nhl.players)
    nhl.playersByPosition()


    best_teams = [] 
    history = []
    # run 20 times
    for j in range(0,20):
        print('Simulation {}'.format(j))
        p = nhl.CreatePopulation(10000)
        fitness_history = [nhl.grade(p)]
        for i in range(0,40):
            print('**************************************')
            print('Generation level {}'.format(i))
            p = nhl.evolve(p)
            fitness_history.append(nhl.grade(p))
            print(fitness_history)
            valid_teams = [team for team in p if team.salary <= 50000]
            valid_teams.sort(key=lambda x: x.points, reverse=True)
    #         for idx, team in enumerate(valid_teams):
    #             print(team.salary)
           # for team in valid_teams:
           #     print(team.GetSalary())
            if len(valid_teams) > 0:
                    tempteam = copy.deepcopy(valid_teams[0])
                    best_teams.append(tempteam)
                    print(valid_teams[0].salary)
            for datum in fitness_history:
                    history.append(datum)   
            best_teams = sorted(best_teams, key = lambda x: x.points, reverse = True)    
            my_choice = best_teams[0] 
    for ateam in best_teams[0:10]:
        print('*********************************************')
        ateam.printTeamNames()
        print(ateam.points)
        print(ateam.salary)
            
        #print(fitness_history)
        '''for i in range(0,40):
            p = evolve(p)
            fitness_history.append(grade(p))
            valid_teams = [team for team in p if GetTeamPointTotal(team) <= 50000]
            valid_teams = sorted(valid_teams, key = points, reverse = True)
            if len(valid_teams) > 0:
                best_teams.append(valid_teams[0])
            for datum in fitness_history:
                history.append(datum)
                    
             #   best_teams = sorted(best_teams, key = GetTeamSalary, reverse = True)
            #    choice = best_teams[0]'''
            
        
         
        
        
