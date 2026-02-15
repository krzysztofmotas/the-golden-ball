from neo4j import GraphDatabase
import json

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "the-golden-ball"

with open("players_with_ranking_data.json", "r", encoding="utf-8") as f:
    players = json.load(f)

def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")

def insert_player_data(tx, player):
    name = player["player"]
    print("\t -", name)

    profile = player.get("transfermarkt_profile", {})

    parameters = {
        "name": name,
        "dob": profile.get("date_of_birth"),
        "height": profile.get("height"),
        "club": profile.get("current_club", "").strip(),
        "joined": profile.get("joined"),
        "expires": profile.get("contract_expires"),
        "last_ext": profile.get("last_contract_extension"),
        "points": player["points"],
        "rank": player["rank"]
    }

    set_clauses = [
        "p.date_of_birth = $dob",
        "p.height = $height",
        "p.current_club = $club",
        "p.joined = $joined",
        "p.contract_expires = $expires",
        "p.last_contract_extension = $last_ext",
        "p.points = $points",
        "p.rank = $rank",
    ]

    existing_keys = set(parameters.keys())

    for key, value in player.items():
        if key not in ["player", "transfermarkt_profile", "transfermarkt_transfers", "transfermarkt_awards"] and key not in existing_keys:
            if key[0].isdigit():
                key = 'n' + key

            key = key.replace("+", "plus").replace("(", "_").replace(")", "_")

            parameters[key] = value
            set_clauses.append(f"p.{key} = ${key}")

    set_clause = ",\n    ".join(set_clauses)

    tx.run(f"""
        MERGE (p:Player {{name: $name}})
        SET {set_clause}
    """, **parameters)

    tx.run("""
        MERGE (c:PlaceOfBirth {name: $place})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:BORN_IN]->(c)
    """, name=name, place=profile.get("place_of_birth"))

    tx.run("""
        MERGE (c:Position {name: $position})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:PLAYS_AS]->(c)
    """, name=name, position=profile.get("position"))

    tx.run("""
        MERGE (c:Foot {name: $foot})
        MERGE (p:Player {name: $name})
        MERGE (p)-[:PLAYS_WITH]->(c)
    """, name=name, foot=profile.get("foot"))


    outfitter = profile.get("outfitter")
    if outfitter:
        tx.run("""
            MERGE (c:Outfitter {name: $outfitter})
            MERGE (p:Player {name: $name})
            MERGE (p)-[:SPONSORED_BY]->(c)
        """, name=name, outfitter=outfitter)

    agent = profile.get("player_agent")
    if agent:
        tx.run("""
            MERGE (c:Agent {name: $agent})
            MERGE (p:Player {name: $name})
            MERGE (p)-[:REPRESENTED_BY]->(c)
        """, name=name, agent=agent)

    for country in profile.get("citizenship", []):
        tx.run("""
            MERGE (c:Country {name: $country})
            MERGE (p:Player {name: $name})
            MERGE (p)-[:HAS_CITIZENSHIP]->(c)
        """, name=name, country=country)

    transfers = player.get("transfermarkt_transfers", [])

    for transfer in transfers:
        old_club = transfer.get("old_club")
        # Unifying club names for Emiliano Martínez:
        # "Arsenal U21" is treated as "Arsenal Res.", because both appear in player data,
        # but refer to the same youth system. Without this, "Arsenal U21"
        # remains without any relationships in the graph.
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

    # Relationship linking player to their first club
    if transfers:
        first_transfer = transfers[-1]
        old_club = first_transfer.get("old_club")
        if old_club:
            tx.run("""
                MERGE (club:Club {name: $club})
                MERGE (p:Player {name: $name})
                MERGE (p)-[:STARTED_CAREER_AT]->(club)
            """, name=name, club=old_club)

    awards = player.get("transfermarkt_awards", [])

    for award in awards:
        title = award.get("title")
        years = award.get("years", [])
        clubs = award.get("clubs", [])

        if clubs:
            for year, club in zip(years, clubs):
                tx.run("""
                    MERGE (p:Player {name: $name})
                    MERGE (a:Award {title: $title, year: $year, club: $club})
                    MERGE (p)-[:WON]->(a)
                """, name=name, title=title, year=year, club=club)
        else:
            for year in years:
                tx.run("""
                    MERGE (p:Player {name: $name})
                    MERGE (a:Award {title: $title, year: $year})
                    MERGE (p)-[:WON]->(a)
                """, name=name, title=title, year=year)

def get_database_stats(tx):
    node_stats = tx.run("""
        MATCH (n)
        RETURN labels(n) AS labels, count(*) AS count
        ORDER BY count DESC
    """).data()

    rel_stats = tx.run("""
        MATCH ()-[r]->()
        RETURN type(r) AS type, count(*) AS count
        ORDER BY count DESC
    """).data()

    return {"nodes": node_stats, "relationships": rel_stats}

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    print("Clearing the database...")
    session.execute_write(clear_database)
    print("Importing players:")

    for player in players:
        session.execute_write(insert_player_data, player)

    stats = session.execute_read(get_database_stats)

    print("\nDatabase statistics:")
    print("\nNodes:")
    nodes_count = 0
    for stat in stats["nodes"]:
        labels = stat["labels"]
        count = stat["count"]
        nodes_count += count
        print(f"\t- {labels[0] if labels else 'No label'}: {count}")

    print("\nTotal number of nodes:", nodes_count)

    print("\nRelationships:")
    rel_count = 0
    for stat in stats["relationships"]:
        rel_type = stat["type"]
        count = stat["count"]
        rel_count += count
        print(f"\t- {rel_type}: {count}")

    print("\nTotal number of relationships:", rel_count)

driver.close()
print("\nData has been successfully imported to Neo4j!")
