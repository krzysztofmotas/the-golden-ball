import json
import pandas as pd
import re

with open("players.json", "r", encoding="utf-8") as f:
    players_data = json.load(f)

df = pd.read_csv("nominees.csv")
df.set_index("player", inplace=True)

start_col = "Playing Time-MP"
start_index = list(df.columns).index(start_col)
selected_columns = df.columns[start_index:]

def normalize_key(dict_key):
    dict_key = dict_key.lower()
    dict_key = dict_key.replace('%', 'percent')
    dict_key = dict_key.replace('#', 'num')
    dict_key = re.sub(r'[\s:/\-]+', '_', dict_key)
    dict_key = re.sub(r'__+', '_', dict_key)
    dict_key = dict_key.strip('_')
    return dict_key

for player in players_data:
    name = player.get("player")
    if name in df.index:
        stats = df.loc[name, selected_columns].to_dict()
        for key, value in stats.items():
            if pd.notna(value):
                clean_key = normalize_key(key)
                player[clean_key] = value

with open("players_with_stats.json", "w", encoding="utf-8") as f:
    json.dump(players_data, f, ensure_ascii=False, indent=2)

print("File saved as players_with_stats.json")
