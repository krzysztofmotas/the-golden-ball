MATCH (p:Player)
WHERE p.performance_gls IS NOT NULL
  AND p.performance_ast IS NOT NULL
  AND p.kp IS NOT NULL
  AND p.carries_prgdist IS NOT NULL
  AND p.int IS NOT NULL
  AND p.blocks_blocks IS NOT NULL
  AND p.take_ons_succ IS NOT NULL
  AND p.playing_time_90s IS NOT NULL

WITH p.name AS player,
     toFloat(p.performance_gls) AS goals,
     toFloat(p.performance_ast) AS assists,
     toFloat(p.kp) AS key_passes,
     toFloat(p.carries_prgdist) AS progressive_carries,
     toFloat(p.int) AS interceptions,
     toFloat(p.blocks_blocks) AS blocks,
     toFloat(p.take_ons_succ) AS successful_dribbles,
     toFloat(p.playing_time_90s) AS games_played,

     (toFloat(p.performance_gls) + toFloat(p.performance_ast)) / toFloat(p.playing_time_90s) AS ga_per_90,
     toFloat(p.kp) / toFloat(p.playing_time_90s) AS kp_per_90,
     toFloat(p.carries_prgdist) / toFloat(p.playing_time_90s) AS carries_per_90,
     (toFloat(p.int) + toFloat(p.blocks_blocks)) / toFloat(p.playing_time_90s) AS defensive_actions_per_90,
     toFloat(p.take_ons_succ) / toFloat(p.playing_time_90s) AS dribbles_per_90

WITH player, ga_per_90, kp_per_90, carries_per_90, defensive_actions_per_90, dribbles_per_90,
     (ga_per_90 + kp_per_90 + carries_per_90 + defensive_actions_per_90 + dribbles_per_90) AS total_score
ORDER BY total_score DESC
LIMIT 10;
