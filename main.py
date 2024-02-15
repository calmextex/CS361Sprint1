from flask import Flask, render_template, request, session
import pandas as pd
from optimizer import Optimizer
import secrets

secret_key = secrets.token_urlsafe(32)
app = Flask(__name__)
app.secret_key = secret_key

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


@app.route('/', methods=['GET'])
def index():
    if 'selected_players' not in session:
        session['selected_players'] = {}

    if request.method == 'GET':
        # Update session based on incoming data
        selected_players = request.args.getlist('selected_player')
        custom_values = {key: request.args[key] for key in request.args if key.startswith('custom_')}

        # Update session with the current state
        for player_id in selected_players:
            session['selected_players'][player_id] = True
        for player_id, custom_value in custom_values.items():
            session['selected_players'][player_id] = custom_value

    position = request.args.get('position', '')
    display_count = request.args.get('count', '20')
    sort_by = request.args.get('sort_by', 'Name')  # Default sort column
    sort_order = request.args.get('sort_order', 'asc')  # Default sort order
    search_query = request.args.get('search', '').lower()
    selected_players = request.args.getlist('selected_player')
    custom_inputs = {key: request.args[key] for key in request.args if key.startswith('custom_')}

    filtered_players_df = filter_players_by_position_from_df(position, players_df)
    # Filter the players by search query
    if search_query:
        filtered_players_df = filtered_players_df[filtered_players_df['Name'].str.lower().str.contains(search_query)]

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

    for player in filtered_players:
        checkbox_value = request.args.get(f"selected_player_{player['ID']}", 'off')
        player['IsSelected'] = True if checkbox_value != 'off' else False

    return render_template('index.html', players=filtered_players, current_count=display_count,
                           current_position=position, sort_by=sort_by, sort_order=sort_order,
                           search_query=search_query, selected_players=selected_players,
                           custom_inputs=custom_inputs)

# @app.route('/optimize', methods=['POST'])
# def optimize():
#     lineup_optimizer = optimizer.Optimizer()
#     lineup_optimizer.load_player_information()
#     optimized_lineup = lineup_optimizer.optimization()
#     return render_template('index.html', optimized_lineup=optimized_lineup)
#

if __name__ == '__main__':
    app.run(debug=True)


# @app.route('/export_lineup')
# def export_lineup():
#     # Retrieve the optimized lineup from session or database
#     csv_file = generate_csv(optimized_lineup)  # Implement this
#     return send_file(csv_file, as_attachment=True, download_name='lineup.csv')
