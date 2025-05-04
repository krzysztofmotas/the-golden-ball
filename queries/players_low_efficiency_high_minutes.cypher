MATCH (p:Player)
WHERE p.playing_time_min IS NOT NULL AND p.performance_gls IS NOT NULL AND p.performance_ast IS NOT NULL
WITH p, (toFloat(p.performance_gls) + toFloat(p.performance_ast)) AS ga, toFloat(p.playing_time_min) AS minutes
WITH p.name AS player, ga, minutes, (ga / minutes) AS ga_per_minute
WHERE ga_per_minute < 0.001
RETURN player, ga, minutes, ga_per_minute
ORDER BY ga_per_minute ASC
LIMIT 10;
