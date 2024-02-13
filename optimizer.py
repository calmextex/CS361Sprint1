import pulp
import csv

# Before use, please download the PuLp library.
# More information can be found at https://coin-or.github.io/pulp/


class Optimizer:
    """ Optimizer class that generate the optimized lineup"""
    def __init__(self, lineups=1):
        """ Initialize the optimizer with the number of lineups to generate, which is set to 1"""
        self.lineups = int(lineups)
        # Create the optimization problem
        self.optimization_problem = pulp.LpProblem("OptimizeLineup", pulp.LpMaximize)

    def load_player_information(self):
        """ Load the player information from the CSV file.  This is a temporary solution until microservice is implemented."""
        with open('player_ids.csv') as f:
            players = csv.DictReader(f)
            for row in players:
                player_name = row['Name'].replace(' ', '#')
                team_name = row['TeamAbbrev']
                position = row['Position']

    def optimization(self):
        """ Optimization to generate the lineup"""

        # Positional constraint
        for position in ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']:
            self.optimization_problem += (pulp.lpSum([player[position] for player in players]) == 1

        # Player can only be selected once:

        #5


