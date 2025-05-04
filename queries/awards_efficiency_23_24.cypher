MATCH (p:Player)-[:WON]->(a:Award)
WHERE p.playing_time_min IS NOT NULL
  AND a.year = "23/24"
WITH p, collect(DISTINCT a.title) AS awards_titles, count(a) AS awards_count, toFloat(p.playing_time_min) AS minutes
WITH p.name AS player, awards_titles, awards_count, minutes, minutes / awards_count AS minutes_per_award
RETURN player, awards_titles AS awards, awards_count, minutes, minutes_per_award
ORDER BY minutes_per_award ASC
LIMIT 10;
