MATCH (p:Player)
WHERE p.kp IS NOT NULL AND p.playing_time_90s IS NOT NULL
WITH p.name AS player, 
     toFloat(p.kp) AS key_passes, 
     toFloat(p.playing_time_90s) AS games_played,
     toFloat(p.kp) / toFloat(p.playing_time_90s) AS kp_per_90
RETURN player, key_passes, games_played, kp_per_90
ORDER BY kp_per_90 DESC
LIMIT 10;
