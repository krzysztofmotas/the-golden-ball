MATCH (p:Player)
WHERE p.total_att IS NOT NULL
  AND p.total_cmp IS NOT NULL
  AND p.progression_prgp IS NOT NULL
  AND p.playing_time_90s IS NOT NULL

WITH p.name AS player,
     toFloat(p.total_att) AS passes_attempted,
     toFloat(p.total_cmp) AS passes_completed,
     toFloat(p.progression_prgp) AS progressive_passes,
     toFloat(p.playing_time_90s) AS games_played

WITH player, passes_attempted, passes_completed, progressive_passes, games_played,
     passes_completed / passes_attempted AS pass_accuracy,
     progressive_passes / games_played AS progressive_passes_per_90

RETURN player, pass_accuracy, progressive_passes_per_90
ORDER BY progressive_passes_per_90 DESC, pass_accuracy DESC
LIMIT 5;
