MATCH (p:Player)-[:HAS_CITIZENSHIP]->(c:Country)
WHERE p.height IS NOT NULL
WITH c.name AS country, 
     toFloat(REPLACE(REPLACE(p.height, " m", ""), ",", ".")) AS height_numeric
WITH country, 
     count(height_numeric) AS players_count,
     avg(height_numeric) AS avg_height,
     min(height_numeric) AS min_height,
     max(height_numeric) AS max_height,
     max(height_numeric) - min(height_numeric) AS height_range
RETURN country, players_count, avg_height, min_height, max_height, height_range
ORDER BY avg_height DESC;
