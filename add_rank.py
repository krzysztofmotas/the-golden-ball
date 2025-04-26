import requests
from bs4 import BeautifulSoup
import json
import unicodedata

def remove_accents(input_string):
    # Normalizujemy ciąg znaków, aby usunąć akcenty
    nfkd_form = unicodedata.normalize('NFKD', input_string)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

url = "https://en.wikipedia.org/wiki/2024_Ballon_d%27Or"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Szukamy tabeli z nominowanymi
table = soup.find('table', {'class': 'wikitable'})

with open("players_with_stats.json", "r", encoding="utf-8") as f:
    players_data = json.load(f)

rank = 0
first_zero = True

for row in table.find_all('tr')[1:]:
    columns = row.find_all('td')

    if len(columns) == 5:
        player_name = columns[0].text.strip()
        points = int(columns[4].text.strip())

        # Artem Dovbyk i Mats Hummels mają po zero punktów i zajmują 29 miejsce
        if points != 0 or first_zero:
            rank += 1
            if points == 0: first_zero = False

        if player_name == "Dani Carvajal":
            player_name = "Daniel Carvajal"

        found = False
        for player in players_data:
            if remove_accents(player['player']) == remove_accents(player_name):
                player['rank'] = rank
                player['points'] = points
                found = True

                print(f"Zapisano dane dla gracza {player_name} (Miejsce: {rank}, Punkty: {points})")
                break

        if not found:
            print(f"Nie znaleziono gracza {player_name}")

with open("players_with_ranking_data.json", "w", encoding="utf-8") as f:
    json.dump(players_data, f, ensure_ascii=False, indent=4)

print("Dane zostały zaktualizowane w pliku 'players_with_ranking_data.json'")

