# Analiza piłkarzy nominowanych do Złotej Piłki 2024 – grafowa baza danych

Projekt zaliczeniowy z przedmiotu **Sieci semantyczne** — grafowa baza danych służąca do analizy piłkarzy nominowanych do Złotej Piłki 2024.

## Opis projektu

The Golden Ball umożliwia przeprowadzanie zapytań dotyczących:

- kariery zawodników,
- osiągnięć oraz zdobytych nagród,
- statystyk sezonowych (gole, asysty, expected goals, expected assists itd.),
- powiązań z klubami, outfitterami i sponsorami.

Model grafowy pozwala przeprowadzać analizy relacyjne oraz tworzyć raporty na podstawie danych.

## Zawartość bazy danych

### Typy węzłów (Nodes)

- Player
- Club
- Country
- PlaceOfBirth
- Position
- Foot
- Outfitter
- Agent
- Award

### Typy relacji (Relationships)

- BORN_IN
- HAS_CITIZENSHIP
- PLAYS_AS
- PLAYS_WITH
- SPONSORED_BY
- REPRESENTED_BY
- WON
- TRANSFERRED
- STARTED_CAREER_AT

### Źródła danych

Dane do bazy zostały pobrane za pomocą scrapingu z następujących źródeł:

- [Kaggle - Statystyki meczowe 2023/2024](https://www.kaggle.com/datasets/willianoliveiragibin/ballon-dor-2024)
- [Transfermarkt - dane biograficzne i transfery](https://www.transfermarkt.pl/)
- [Wikipedia - oficjalne wyniki Ballon d'Or](https://en.wikipedia.org/wiki/2024_Ballon_d%27Or)

## Przykładowe zapytania Cypher

W ramach projektu przygotowano zestaw nietrywialnych zapytań w języku Cypher, umożliwiających analizę zgromadzonych danych.
Zapytania pozwalają m.in. na ocenę efektywności zawodników, analizę ścieżek kariery, wpływu agentów na sukcesy piłkarzy itp.

| Zapytanie                                          | Opis                                                                                                  | Plik                                               |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| **Wielonarodowość zawodników (spoza Europy)**      | Wyszukaj zawodników, którzy mają więcej niż jedno obywatelstwo, w tym co najmniej jedno spoza Europy. | `queries/multi_citizenship_outside_europe.cypher`  |
| **Sponsorzy z największą liczbą nagród**           | Wypisz sponsorów, których zawodnicy zdobyli największą liczbę nagród.                                 | `queries/outfitter_awards_leaders.cypher`          |
| **Średni wzrost zawodników wg krajów**             | Wypisz kraje, których zawodnicy mają najwyższy średni wzrost, minimalny/maksymalny oraz rozrzut.      | `queries/countries_avg_height_distribution.cypher` |
| **Defensywny profil zawodników (mało G+A)**        | Wypisz zawodników z dużą liczbą minut, ale minimalnym udziałem w golach i asystach.                   | `queries/low_offensive_contribution.cypher`        |
| **Najlepsi kreatorzy gry (key passes per 90)**     | Znajdź zawodników z największą liczbą kluczowych podań na 90 minut.                                   | `queries/top_key_passers.cypher`                   |
| **TOP kompletni zawodnicy**                        | Wypisz zawodników o wszechstronnym profilu (ofensywa, kreatywność, defensywa, drybling).              | `queries/complete_players_profiles.cypher`         |
| **Top 5 progresywnych podających**                 | Wypisz top 5 zawodników z progresywnymi podaniami i wysoką skutecznością podań.                       | `queries/top_progressive_passers.cypher`           |
| **Lojalność i sukces — najmniej klubów + nagrody** | Wypisz zawodników, którzy zdobyli najwięcej nagród grając w najmniejszej liczbie klubów.              | `queries/loyal_award_winners.cypher`               |
| **Underperformance względem xG + xA**              | Wypisz zawodników, których gole i asysty są niższe niż suma xG + xA.                                  | `queries/underperformance_xg_xa.cypher`            |
| **Efektywność nagradzania w sezonie 23/24**        | Wypisz zawodników z nagrodami w 23/24 oraz liczbą minut przypadającą na nagrodę.                      | `queries/awards_efficiency_23_24.cypher`           |

### Przykład wyników zapytania — efektywność nagradzania w sezonie 23/24

Poniżej przedstawiono przykładowe wyniki zapytania, które analizuje zawodników pod względem liczby zdobytych nagród w sezonie 23/24 w odniesieniu do liczby rozegranych minut.
Dzięki temu możliwe jest określenie, którzy zawodnicy byli najbardziej "efektywni" — czyli zdobywali nagrody mimo stosunkowo niewielkiej liczby minut spędzonych na boisku.

**Przykładowe wyniki zapytania**:

![awards_efficiency_23_24](queries/awards_efficiency_23_24.png)

#### Interpretacja wyników — przykład Kylian Mbappé (sezon 23/24)

Kylian Mbappé zdobył aż **7 nagród** przy zaledwie **2158 minutach** rozegranych w sezonie. Choć liczba minut jest niższa niż u wielu innych zawodników, doskonale odzwierciedla to realną sytuację z sezonu:

* Mbappé był częściowo **odsuwany od składu PSG** z powodu decyzji o nieprzedłużeniu kontraktu oraz planowanego transferu do Realu Madryt.
* Mimo tego, pozostawał niezwykle skuteczny i wpływowy — zdobywając prestiżowe wyróżnienia jak **Top goal scorer** czy **Player of the Year**.
* Zapytanie w trafny sposób pokazuje zawodników, którzy **nawet przy ograniczonej liczbie minut** potrafili osiągnąć ponadprzeciętne sukcesy.

## Struktura projektu

### Główne skrypty

| Plik | Opis |
|------|------|
| `main_scrapper.py` | Główny scraper danych o zawodnikach z Transfermarkt i innych źródeł. |
| `import_players_to_neo4j.py` | Skrypt importujący zawodników oraz ich dane do bazy Neo4j. |
| `add_stats.py` | Dodanie sezonowych statystyk do zawodników w Neo4j. |
| `add_rank.py` | Dodanie rankingów oraz wyników głosowania Ballon d'Or 2024 do bazy Neo4j. |

### Pliki danych (JSON / CSV)

| Plik | Opis |
|------|------|
| `players.json` | Podstawowe dane zawodników (bio, wiek, wzrost itd.). |
| `players_with_stats.json` | Rozszerzone dane zawodników — z sezonowymi statystykami. |
| `players_with_ranking_data.json` | Dane zawodników uzupełnione o rankingi i wyniki Ballon d'Or 2024. |
| `nominees.csv` | Lista nominowanych do Złotej Piłki. |
