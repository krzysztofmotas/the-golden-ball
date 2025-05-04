MATCH (p:Player)-[:TRANSFERRED]->(c:Club)
WITH p, count(DISTINCT c) AS clubs_played

MATCH (p)-[:WON]->(a:Award)
WITH p.name AS player, clubs_played, count(a) AS awards_won

RETURN player, clubs_played, awards_won
ORDER BY awards_won DESC, clubs_played ASC
LIMIT 10;

