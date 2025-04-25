from neo4j import GraphDatabase
import json

# Konfiguracja połączenia
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "the-golden-ball"

# Wczytaj dane z JSON
with open("players.json", "r", encoding="utf-8") as f:
    players = json.load(f)

def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")

def insert_player_data(tx, player):
    name = player["player"]
    print(name)
    profile = player.get("transfermarkt_profile", {})
    transfers = player.get("transfermarkt_transfers", [])
    awards = player.get("transfermarkt_awards", [])

    # --- Tworzenie Playera i podstawowych info ---
    tx.run("""
        MERGE (p:Player {name: $name})
        SET p.date_of_birth = $dob,
            p.height = $height,
            p.current_club = $club,
            p.joined = $joined,
            p.contract_expires = $expires,
            p.last_contract_extension = $last_ext
    """, name=name,
         dob=profile.get("date_of_birth"),
         height=profile.get("height"),
         club=profile.get("current_club", "").strip(),
         joined=profile.get("joined"),
         expires=profile.get("contract_expires"),
         last_ext=profile.get("last_contract_extension"))

    # --- Relacja z PlaceOfBirth ---
    tx.run("""
        MERGE (c:PlaceOfBirth {name: $place})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:BORN_IN]->(c)
    """, name=name, place=profile.get("place_of_birth"))

    # --- Relacja z Position ---
    tx.run("""
        MERGE (c:Position {name: $position})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:PLAYS_AS]->(c)
    """, name=name, position=profile.get("position"))

    # --- Relacja z Foot ---
    tx.run("""
        MERGE (c:Foot {name: $foot})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:PLAYS_WITH]->(c)
    """, name=name, foot=profile.get("foot"))

    # --- Relacja z Outfitter ---
    tx.run("""
        MERGE (c:Outfitter {name: $outfitter})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:SPONSORED_BY]->(c)
    """, name=name, outfitter=profile.get("outfitter"))

    # --- Relacja z Agent ---
    tx.run("""
        MERGE (c:Agent {name: $agent})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:REPRESENTED_BY]->(c)
    """, name=name, agent=profile.get("player_agent"))

    # --- Relacje z Citizenship ---
    for country in profile.get("citizenship", []):
        tx.run("""
            MERGE (c:Country {name: $country})
            MERGE (p:Player {name: $name})
            MERGE (p)-[:]->(c)
        """, name=name, country=country)

    # --- Relacje z Transferami ---
    for transfer in transfers:
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
             old_club=transfer.get("old_club"),
             new_club=transfer.get("new_club"),
             market_value=transfer.get("market_value"),
             transfer_fee=transfer.get("transfer_fee"))

    # --- Relacje z Nagród (Award) ---
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
