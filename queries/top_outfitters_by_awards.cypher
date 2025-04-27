// Krok 1: znajdź outfitterów, zawodników i ich nagrody
MATCH (o:Outfitter)<-[:SPONSORED_BY]-(p:Player)-[:WON]->(a:Award)

// Krok 2: agreguj dane
WITH 
    o.name AS Outfitter,
    p.name AS Player,
    count(a) AS PlayerAwardCount

// Krok 3: zagreguj dalej na poziomie outfittera
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

