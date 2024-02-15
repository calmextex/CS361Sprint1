import pulp
import csv

# Before use, please download the PuLp library.
# More information can be found at https://coin-or.github.io/pulp/


class Optimizer:
    """ Optimizer class that generate the optimized lineup"""
    # Dict variable to store the player information
    player_dictionary = {}
    # empty list to store the lineup information
    lineup = []
    # min and max salary are preset for now. The user will modify this in future implementation
    min_salary = 49000
    max_salary = 50000
    opt_problem = None
    min_projection = None
    team_limit = 3

    def __init__(self, lineups=1):
        """ Initialize the optimizer with the number of lineups to generate, which is set to 1"""
        self.lineups = int(lineups)
        # Create the optimization problem
        self.optimization_problem = pulp.LpProblem("OptimizeLineup", pulp.LpMaximize)

    def load_player_information(self):
        """ Load the player information from the CSV file.
        Reading from a CSV file for now until Microservices are implemented to fetch data from the internet."""
        with open('player_ids.csv') as f:
            players = csv.DictReader(f)
            for row in players:
                player_name = row['Name'].replace(' ', '#')
                team_name = row['TeamAbbrev']
                position = row['Position']
                player_id = row['ID']
                salary = row['Salary']
                projection = row['AvgPointsPerGame']

                # Add players to the dictionary. For position, we split the string by '/' and store it as a list
                self.player_dictionary[player_id] = {
                    'Name': player_name,
                    'Team': team_name,
                    'Position': [pos for pos in row[position].split('/')],
                    'Salary': float(salary),
                    'Projection': float(projection)
                }
                # account for general G (PG, SG), F (SF, PF) and UTL (all) positions. Append
                if 'PG' in row[position] or 'SG' in row[position]:
                    self.player_dictionary[player_id]['Position'].append('G')
                if 'SF' in row[position] or 'PF' in row[position]:
                    self.player_dictionary[player_id]['Position'].append('F')
                self.player_dictionary[player_id]['Position'].append('UTIL')

    def optimization(self):
        """ Optimization to generate the lineup. Uses Linear Programming to solve the problem"""
        # We want a binary decision for each player and position (0 or 1)
        variables = {}
        for player, specs in self.player_dictionary:
            id = specs['ID']
            for position in specs['Position']:
                variables[(player, position, id)] = pulp.LpVariable(
                    name=f"{player}_{position}_{id}", cat=pulp.LpBinary
                )

        # The objective is to maximize the total projection
        self.optimization_problem += (pulp.lpSUM(
            self.player_dictionary[player]['Projection'] * variables[(player, position, id)]
            for player in self.player_dictionary
            for position in self.player_dictionary[player]['Position']), "Objective",)
        # min salary constraint
        self.optimization_problem += (
            pulp.lpSum(self.player_dictionary[player]['Salary'] * variables[(player, position, id)]
                        for player in self.player_dictionary
                        for position in self.player_dictionary[player]['Position']) >= self.min_salary, "MinSalary"
        )
        # max salary constraint
        self.optimization_problem += (
            pulp.lpSum(self.player_dictionary[player]['Salary'] * variables[(player, position, id)]
                        for player in self.player_dictionary
                        for position in self.player_dictionary[player]['Position']) <= self.max_salary, "MaxSalary"
        )
        # Draftkings requires at least 3 teams be represented. We will constrain to max 3 per team to satisfy this

        #  make sure to only select player once

        # Positional constraint
        for position in ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']:
            self.optimization_problem += (pulp.lpSum([player[position] for player in players]) == 1)


        # Solving the problem
        self.optimization_problem.solve(pulp.PULP_CBC_CMD(msg=False))
        # Store the lineup in the lineup list
        self.lineups.append([player for player in players if player.varValue == 1])
        # return the lineup
        return self.lineups




