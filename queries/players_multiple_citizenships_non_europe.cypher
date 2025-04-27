MATCH (p:Player)-[:HAS_CITIZENSHIP]->(c:Country)
WITH p, collect(c.name) AS citizenships
WHERE size(citizenships) > 1 
  AND any(country IN citizenships WHERE NOT country IN [
    'England', 'Spain', 'Germany', 'France', 'Italy', 'Portugal', 'Netherlands', 'Belgium', 'Norway', 
    'Sweden', 'Denmark', 'Switzerland', 'Austria', 'Croatia', 'Poland', 'Serbia', 'Ukraine', 'Turkey'
])
RETURN 
    p.name AS Player, 
    citizenships AS Countries
ORDER BY p.name