from flask import Flask, render_template, request, jsonify
import pandas as pd
import optimizer

app = Flask(__name__)

# for now, we'll use a custom csv file to generate a player list.
file_path = 'player_ids.csv'

# Try reading the CSV file into a DataFrame. else return error.
try:
    players_df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    raise


def filter_players_by_position_from_df(position, players_df):
    if not position:
        return players_df
    filtered_players_df = players_df[players_df['Roster Position'].apply(lambda x: position in x.split('/'))]
    return filtered_players_df


@app.route('/')
def index():
    position = request.args.get('position', '')
    display_count = request.args.get('count', '20')
    sort_by = request.args.get('sort_by', 'Name')  # Default sort column
    sort_order = request.args.get('sort_order', 'asc')  # Default sort order

    filtered_players_df = filter_players_by_position_from_df(position, players_df)

    # Convert 'all' to actual number for DataFrame handling
    if display_count == 'all':
        display_count = len(filtered_players_df)
    else:
        display_count = int(display_count)

    # Sorting
    if sort_order == 'desc':
        filtered_players_df = filtered_players_df.sort_values(by=sort_by, ascending=False)
    else:
        filtered_players_df = filtered_players_df.sort_values(by=sort_by, ascending=True)

    limited_players_df = filtered_players_df.head(display_count)
    filtered_players = limited_players_df.to_dict(orient='records')

    return render_template('index.html', players=filtered_players, current_count=display_count,
                           current_position=position, sort_by=sort_by, sort_order=sort_order)


@app.route('/optimize', methods=['POST'])
def optimize():
    lineup_optimizer = optimizer.Optimizer()
    lineup_optimizer.load_player_information()
    optimized_lineup = lineup_optimizer.optimization()
    lineup_optimizer.export()
    return render_template('index.html', optimized_lineup=optimized_lineup)
# @app.route('/export_lineup')
# def export_lineup():
#     # upon clicking button, export the lineup (as a table in the html page) to a csv file
if __name__ == '__main__':
    app.run(debug=True)


