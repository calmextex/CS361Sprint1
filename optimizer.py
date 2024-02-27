
from pulp import *
import csv
from random import shuffle, choice

# Before use, please download the PuLp library.
# More information can be found at https://coin-or.github.io/pulp/


class Optimizer:
    """ Optimizer class that generate the optimized lineup"""
    # Dict variable to store the player information
    player_dictionary = {}
    # empty list to store the lineup information

    lineup = {}

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

        self.opt_problem = LpProblem('FantasyBasketball', LpMaximize)
    def load_player_information(self):
        """ Load the player information from the CSV file.
        Reading from a CSV file for now until Microservices are implemented to fetch data from the internet."""
        with open('player_ids.csv') as f:
            players = csv.DictReader(f)
            for row in players:
                player_name = row['Name'].replace(' ', '#')
                team_name = row['TeamAbbrev']

                player_id = row['ID']
                salary = row['Salary']
                projection = row['AvgPointsPerGame']

                # Add players to the dictionary. For position, we split the string by '/' and store it as a list

                position_data = row['Position'].split('/') if '/' in row['Position'] else [row['Position']]
                self.player_dictionary[player_id] = {
                    'Name': player_name,
                    'Team': team_name,
                    'Position': position_data,
                    'Salary': float(salary),
                    'Projection': float(projection)
                }
                # After adding players to the dictionary with their positions split
                for pos in position_data:  # Iterate through the list of positions
                    # Check for general positions and append them as needed
                    if 'PG' in pos or 'SG' in pos:
                        self.player_dictionary[player_id]['Position'].append('G')
                    if 'SF' in pos or 'PF' in pos:
                        self.player_dictionary[player_id]['Position'].append('F')
                # Since 'UTIL' is a universal position, append it outside the loop
                self.player_dictionary[player_id]['Position'].append('UTIL')

    def optimization(self):
        variables = {player: LpVariable(player, cat='Binary') for player, _ in self.player_dictionary.items()}

        self.opt_problem += lpSum(self.player_dictionary[player]['Projection'] * variables[player] for player in self.player_dictionary), 'Objective'
        self.opt_problem += lpSum(self.player_dictionary[player]['Salary'] * variables[player] for player in self.player_dictionary) <= self.max_salary
        self.opt_problem += lpSum(self.player_dictionary[player]['Salary'] * variables[player] for player in self.player_dictionary) >= self.min_salary

         # Need at least 1 point guard, can have up to 3 if utilizing G and UTIL slots
        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'PG' in self.player_dictionary[player]['Position']) >= 1
        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'PG' in self.player_dictionary[player]['Position']) <= 3

        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'SG' in self.player_dictionary[player]['Position']) >= 1
        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'SG' in self.player_dictionary[player]['Position']) <= 3
        
        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'SF' in self.player_dictionary[player]['Position']) >= 1
        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'SF' in self.player_dictionary[player]['Position']) <= 3

        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'PF' in self.player_dictionary[player]['Position']) >= 1
        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'PF' in self.player_dictionary[player]['Position']) <= 3

        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'C' in self.player_dictionary[player]['Position']) >= 1
        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'C' in self.player_dictionary[player]['Position']) <= 2

        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'PG' in self.player_dictionary[player]['Position'] or 'SG' in self.player_dictionary[player]['Position']) >= 3

        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if 'SF' in self.player_dictionary[player]['Position'] or 'PF' in self.player_dictionary[player]['Position']) >= 3

        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary if ['PG'] == self.player_dictionary[player]['Position'] or ['C'] == self.player_dictionary[player]['Position']) <= 4

        self.opt_problem += lpSum(variables[player] for player in self.player_dictionary) == 8

        self.opt_problem.solve(PULP_CBC_CMD(msg=0))

        score = str(self.opt_problem.objective)
        for var in self.opt_problem.variables():
            score = score.replace(var.name, str(var.varValue))
        
        player_names = [var.name.replace('_', ' ') for var in self.opt_problem.variables() if var.varValue != 0]
        fpts = eval(score)
        self.lineup[fpts] = player_names
        return print(self.lineup)

    def export(self):
        self.format()
        with open('lineup.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL', 'FPTS'])
            for fpts, players in self.lineup.items():
                lineup_data = []
                for player_id in players:  # Assuming players contains the correct player IDs
                    player = self.player_dictionary[player_id]  # Accessing by player ID
                    player_name = player['Name'].replace('#', ' ')  # Assuming '#' was used as a placeholder for spaces
                    lineup_data.append(f"{player_name} ({player_id})")
                lineup_data.append(fpts)  # Add fantasy points to the end
                writer.writerow(lineup_data)

    def format(self):
        roster = [['PG'], ['SG'], ['SF'], ['PF'], ['C'], ['G'], ['F'], ['UTIL']]
        temp = self.lineup.items()
        self.lineup = {}
        for fpts, lineups in temp:
            lineup = [None] * 8
            for i, positions in enumerate(roster):
                available_players = [p for p in lineups if any(
                    pos in positions for pos in self.player_dictionary[p]['Position']) and p not in lineup]
                if available_players:
                    selected_player = choice(available_players)
                    lineup[i] = selected_player
                else:
                    print(f"Cannot fill position {positions} due to lack of available players.")
                    # Handle the error or choose to fill the position differently.
            self.lineup[fpts] = lineup
