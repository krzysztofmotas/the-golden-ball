from neo4j import GraphDatabase
import json

# Konfiguracja połączenia
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "the-golden-ball"

# Wczytaj dane z JSON
with open("players_with_stats.json", "r", encoding="utf-8") as f:
    players = json.load(f)

def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")

def insert_player_data(tx, player):
    name = player["player"]
    print(name)

    profile = player.get("transfermarkt_profile", {})

    # --- Zawodnik ---
    parameters = {
        "name": name,
        "dob": profile.get("date_of_birth"),
        "height": profile.get("height"),
        "club": profile.get("current_club", "").strip(),
        "joined": profile.get("joined"),
        "expires": profile.get("contract_expires"),
        "last_ext": profile.get("last_contract_extension")
    }

    set_clauses = [
        "p.date_of_birth = $dob",
        "p.height = $height",
        "p.current_club = $club",
        "p.joined = $joined",
        "p.contract_expires = $expires",
        "p.last_contract_extension = $last_ext"
    ]

    existing_keys = set(parameters.keys())

    # Statystyki:
    for key, value in player.items():
        if key not in ["player", "transfermarkt_profile", "transfermarkt_transfers", "transfermarkt_awards"] and key not in existing_keys:
            if key[0].isdigit():
                key = 'n' + key  # Dodajemy 'n' na początku

            # Zastępujemy '+' na 'plus' i nawiasy na '_'
            key = key.replace("+", "plus").replace("(", "_").replace(")", "_")

            parameters[key] = value
            set_clauses.append(f"p.{key} = ${key}")

    set_clause = ",\n    ".join(set_clauses)

    tx.run(f"""
        MERGE (p:Player {{name: $name}})
        SET {set_clause}
    """, **parameters)

    # --- Miejsce urodzenia ---
    tx.run("""
        MERGE (c:PlaceOfBirth {name: $place})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:BORN_IN]->(c)
    """, name=name, place=profile.get("place_of_birth"))

    # --- Pozycja na boisku ---
    tx.run("""
        MERGE (c:Position {name: $position})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:PLAYS_AS]->(c)
    """, name=name, position=profile.get("position"))

    # --- Preferowana noga ---
    tx.run("""
        MERGE (c:Foot {name: $foot})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:PLAYS_WITH]->(c)
    """, name=name, foot=profile.get("foot"))

    # --- Sponsorzy wyposażenia ---
    outfitter = profile.get("outfitter")
    if outfitter:
        tx.run("""
            MERGE (c:Outfitter {name: $outfitter})
            MERGE (p:Player {name: $name})
            MERGE (p)-[:SPONSORED_BY]->(c)
        """, name=name, outfitter=outfitter)

    # --- Menadżerowie/agenci ---
    agent = profile.get("player_agent")
    if agent:
        tx.run("""
            MERGE (c:Agent {name: $agent})
            MERGE (p:Player {name: $name})
            MERGE (p)-[:REPRESENTED_BY]->(c)
        """, name=name, agent=agent)

    # --- Obywatelstwa  ---
    for country in profile.get("citizenship", []):
        tx.run("""
            MERGE (c:Country {name: $country})
            MERGE (p:Player {name: $name})
            MERGE (p)-[:HAS_CITIZENSHIP]->(c)
        """, name=name, country=country)

    # --- Relacje z transferami ---
    transfers = player.get("transfermarkt_transfers", [])

    for transfer in transfers:
        old_club = transfer.get("old_club")
        # Ujednolicenie nazw klubów dla Emiliano Martíneza:
        # "Arsenal U21" traktujemy jako "Arsenal Res.", ponieważ w danych zawodnika występują oba,
        # ale odnoszą się do tego samego systemu młodzieżowego. Bez tego "Arsenal U21"
        # pozostaje bez żadnych relacji w grafie.
        if old_club == "Arsenal U21":
            old_club = "Arsenal Res."

        tx.run("""
            MERGE (p:Player {name: $name})
            MERGE (old:Club {name: $old_club})
            MERGE (new:Club {name: $new_club})
            CREATE (p)-[:TRANSFERRED {
                season: $season,
                date: $date,
                market_value: $market_value,
                transfer_fee: $transfer_fee
            }]->(new)
        """, name=name,
             season=transfer.get("season"),
             date=transfer.get("date"),
             old_club=old_club,
             new_club=transfer.get("new_club"),
             market_value=transfer.get("market_value"),
             transfer_fee=transfer.get("transfer_fee"))

    # --- Relacja łącząca zawodnika z jego pierwszym klubem ---
    if transfers:
        first_transfer = transfers[-1]  # Ostatni element to najstarszy transfer
        old_club = first_transfer.get("old_club")
        if old_club:
            tx.run("""
                MERGE (club:Club {name: $club})
                MERGE (p:Player {name: $name})
                MERGE (p)-[:STARTED_CAREER_AT]->(club)
            """, name=name, club=old_club)

    # --- Nagrody ---
    awards = player.get("transfermarkt_awards", [])

    for award in awards:
        title = award.get("title")
        years = award.get("years", [])
        clubs = award.get("clubs", [])
        for year, club in zip(years, clubs):
            tx.run("""
                MERGE (p:Player {name: $name})
                MERGE (a:Award {title: $title, year: $year, club: $club})
                MERGE (p)-[:WON]->(a)
            """, name=name, title=title, year=year, club=club)

# --- Połączenie i import ---
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    print("Czyścimy bazę danych...")
    session.execute_write(clear_database)
    print("Importujemy zawodników:")

    for player in players:
        session.execute_write(insert_player_data, player)

driver.close()
print("Dane zaimportowane do Neo4j!")
