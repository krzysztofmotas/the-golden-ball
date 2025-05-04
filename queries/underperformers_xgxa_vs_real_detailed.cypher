MATCH (p:Player)
WHERE p.expected_xg IS NOT NULL
  AND p.expected_xag IS NOT NULL
  AND p.performance_gls IS NOT NULL
  AND p.performance_ast IS NOT NULL

WITH p.name AS player,
     toFloat(p.expected_xg) AS expected_goals,
     toFloat(p.expected_xag) AS expected_assists,
     toFloat(p.performance_gls) AS actual_goals,
     toFloat(p.performance_ast) AS actual_assists,
     (toFloat(p.expected_xg) + toFloat(p.expected_xag)) AS expected_contributions,
     (toFloat(p.performance_gls) + toFloat(p.performance_ast)) AS actual_contributions

WITH player, expected_contributions, actual_contributions, 
     expected_goals, expected_assists, actual_goals, actual_assists,
     actual_contributions - expected_contributions AS difference

WHERE difference < 0
RETURN player, expected_goals, expected_assists, actual_goals, actual_assists, expected_contributions, actual_contributions, difference
ORDER BY difference ASC
LIMIT 10;
