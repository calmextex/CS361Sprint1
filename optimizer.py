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
        file = 'player_ids.csv'
        with open(file, 'r', encoding='utf-8-sig') as f:
            players = csv.DictReader(f)
            print(players.fieldnames)
            for row in players:
                player_name = row['Name'].replace(' ', '#')
                team_name = row['TeamAbbrev']
                positions = row['Position']
                player_id = row['ID']
                salary = row['Salary']
                projection = row['AvgPointsPerGame']

                # Add players to the dictionary. For position, we split the string by '/' and store it as a list
                self.player_dictionary[player_id] = {
                    'Name': player_name,
                    'Team': team_name,
                    'Position': [pos for pos in row["Position"].split('/')],
                    'Salary': float(salary),
                    'Projection': float(projection)
                }
                # Append general positions based on specific positions if needed
                if any(pos in ['PG', 'SG'] for pos in positions):
                    self.player_dictionary[player_id]['Position'].append('G')
                if any(pos in ['SF', 'PF'] for pos in positions):
                    self.player_dictionary[player_id]['Position'].append('F')
                self.player_dictionary[player_id]['Position'].append('UTIL')


    def optimization(self):
        """ Optimization to generate the lineup. Uses Linear Programming to solve the problem"""
        # We want a binary decision for each player and position (0 or 1)
        # Define decision variables for players
        player_vars = {player_id: pulp.LpVariable(f"player_{player_id}", cat=pulp.LpBinary) for player_id in
                       self.player_dictionary}

        # Objective Function: Maximize Total Projection
        self.optimization_problem += pulp.lpSum(
            player_vars[player_id] * self.player_dictionary[player_id]['Projection'] for player_id in
            self.player_dictionary), "Total Projection"

        # Salary Constraints
        self.optimization_problem += pulp.lpSum(
            player_vars[player_id] * self.player_dictionary[player_id]['Salary'] for player_id in
            self.player_dictionary) <= self.max_salary, "MaxSalary"
        self.optimization_problem += pulp.lpSum(
            player_vars[player_id] * self.player_dictionary[player_id]['Salary'] for player_id in
            self.player_dictionary) >= self.min_salary, "MinSalary"

        # Position Constraints
        for position in ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']:
            eligible_players_for_pos = [player_id for player_id, specs in self.player_dictionary.items() if
                                        position in specs['Position']]
            # Ensure exactly one player is selected for each specific position, including the G, F, and UTIL positions

            self.optimization_problem += pulp.lpSum(
                player_vars[player_id] for player_id in eligible_players_for_pos) == 1, f"Constraint_{position}"


        # Team Constraint: Max 3 players from the same team (if needed)
        teams = set(specs['Team'] for specs in self.player_dictionary.values())
        for team in teams:
            players_from_team = [player_id for player_id, specs in self.player_dictionary.items() if
                                 specs['Team'] == team]
            self.optimization_problem += pulp.lpSum(
                player_vars[player_id] for player_id in players_from_team) <= self.team_limit, f"Team_Constraint_{team}"

        # Solve the optimization problem
        self.optimization_problem.solve(pulp.PULP_CBC_CMD(msg=False))

        # Extract and format the optimized lineup
        optimized_lineup = [(self.player_dictionary[player_id]['Name'], player_id) for player_id in
                            self.player_dictionary if player_vars[player_id].value() == 1]
        optimized_lineup_formatted = [f"{name} ({player_id})" for name, player_id in optimized_lineup]

        return optimized_lineup_formatted


if __name__ == "__main__":
    optimizer = Optimizer()
    optimizer.load_player_information()  # Load player data
    optimized_lineup = optimizer.optimization()
    print("Optimized Lineup:", optimized_lineup)

