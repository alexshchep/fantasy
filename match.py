from matplotlib.font_manager import home
class Match():
    def __init__(self, id, home, away, homegoals, awaygoals, result, players, date):
        self.id = id
        self.home = home
        self.away = away
        self.homegoals = homegoals
        self.awaygoals = awaygoals
        self.result = result
        self.players = players
        self.date = date