MATCH (o:Outfitter)<-[:SPONSORED_BY]-(p:Player)-[:WON]->(a:Award)

WITH 
    o.name AS Outfitter,
    p.name AS Player,
    count(a) AS PlayerAwardCount

WITH 
    Outfitter,
    collect({player: Player, awards: PlayerAwardCount}) AS PlayersAwards,
    sum(PlayerAwardCount) AS TotalAwards,
    avg(PlayerAwardCount) AS AvgAwardsPerPlayer

UNWIND PlayersAwards AS pa
WITH 
    Outfitter,
    TotalAwards,
    AvgAwardsPerPlayer,
    pa.player AS PlayerName,
    pa.awards AS PlayerAwards

WITH 
    Outfitter,
    TotalAwards,
    AvgAwardsPerPlayer,
    collect({name: PlayerName, awards: PlayerAwards}) AS AllPlayers,
    max(PlayerAwards) AS MaxAwards

WITH Outfitter, 
     TotalAwards, 
     AvgAwardsPerPlayer,
     [p IN AllPlayers WHERE p.awards = MaxAwards][0] AS TopPlayer

RETURN 
    Outfitter,
    TotalAwards,
    AvgAwardsPerPlayer,
    TopPlayer.name AS BestPlayer,
    TopPlayer.awards AS BestPlayerAwards
ORDER BY TotalAwards DESC

