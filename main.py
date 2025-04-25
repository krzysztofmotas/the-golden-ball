import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import traceback

chrome_driver_path = "C:\chromedriver-win64\chromedriver.exe"  # Konfiguracja Selenium

service = Service(executable_path=chrome_driver_path)  # Ścieżka do ChromeDrivera
options = webdriver.ChromeOptions()  # Tworzymy obiekt opcji

options.add_argument("--start-maximized")  # Maksymalizacja okna
options.add_argument("--disable-blink-features=AutomationControlled")  # Ukrycie automatyzacji (bot)
options.add_experimental_option("excludeSwitches",
                                ["enable-automation"])  # Usunięcie ostrzeżenia "Chrome is controlled"
options.add_experimental_option('useAutomationExtension', False)  # Wyłączenie rozszerzenia automation

driver = webdriver.Chrome(service=service, options=options)  # Start przeglądarki z opcjami

driver.switch_to.window(driver.current_window_handle)  # Aktywujemy główne okno

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {  # Ukrywamy navigator.webdriver
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

clicked = False


# Funkcja do zaakceptowania ciasteczek, również z obsługą iframe'ów
def accept_cookies_if_present():
    # Jeśli prośba o ciasteczka została już zaakceptowana, pomiń
    global clicked
    if clicked:
        return

    # Pobierz wszystkie iframe'y na stronie
    iframes = driver.find_elements(By.TAG_NAME, "iframe")

    # Iteruj przez każdy iframe, próbując znaleźć i kliknąć przycisk akceptacji ciasteczek
    for index, iframe in enumerate(iframes):
        try:
            # Przełącz się do iframe
            driver.switch_to.frame(iframe)

            # Poczekaj, aż przycisk stanie się klikalny i kliknij go
            button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Accept & continue')]"))
            )
            button.click()
            print("Kliknięto cookies w iframe!")

            clicked = True

            # Przywróć możliwość przewijania strony po akceptacji
            driver.execute_script(
                "document.body.style.overflow = 'auto';"
                "document.documentElement.style.overflow = 'auto';"
            )

            # Wróć do głównego kontekstu strony
            driver.switch_to.default_content()

            # Odświeżenie strony po zaakceptowaniu cookies
            time.sleep(1)
            driver.refresh()
            return  # Zakończ po skutecznym kliknięciu
        except:
            # Jeśli nie udało się kliknąć w tym iframe, wróć do kontekstu głównego i spróbuj dalej
            driver.switch_to.default_content()


# Funkcja wyszukuje gracza po nazwie i zwraca link do jego profilu z Transfermarkt
def find_player_profile_link(player_name):
    # Tworzenie URL do wyszukiwarki Transfermarkt, zamieniając spacje na plusy
    search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={player_name.replace(' ', '+')}"

    # Ustawienie nagłówka User-Agent, aby symulować przeglądarkę
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    # Wysłanie zapytania HTTP do strony wyszukiwania
    response = requests.get(search_url, headers=headers)

    # Sprawdzenie poprawności odpowiedzi
    if response.status_code != 200:
        print("Błąd pobierania wyników wyszukiwania.")
        return None

    # Parsowanie odpowiedzi HTML za pomocą BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Pobranie wierszy graczy z wyników wyszukiwania (klasy 'odd' i 'even')
    player_list = soup.find_all('tr', class_='odd') + soup.find_all('tr', class_='even')

    # Jeżeli znaleziono jakichkolwiek graczy
    if player_list:
        # Wybierz pierwszego gracza z listy
        first_player = player_list[0]

        # Wyodrębnij nazwę i link do profilu gracza
        player_name = first_player.find('td', class_='hauptlink').text.strip()
        player_link = first_player.find('td', class_='hauptlink').find('a')['href']

        # Wypisz informacje o graczu
        print(f'Znaleziono: {player_name} - {player_link}')

        # Zwróć względny link do profilu gracza
        return player_link
    else:
        # Gdy brak wyników wyszukiwania
        print('Nie znaleziono wyników dla tego gracza.')
        return None


# Funkcja analizuje dane zawodnika z sekcji "Facts and data" na stronie Transfermarkt
def parse_player_info(driver):
    # print("\nDane zawodnika:")

    # Parsowanie HTML-a strony przez BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Szukanie nagłówka "Informacje i fakty"
    headline = soup.find("span", string=lambda s: s and "Facts and data" in s)
    if not headline:
        print("Nie znaleziono sekcji 'Facts and data'.")
        return {}

    # Szukanie najbliższego diva zawierającego dane
    info_block = headline.find_next("div", class_=lambda c: c and "info-table" in c)
    if not info_block:
        print("Nie znaleziono bloku danych gracza.")
        return {}

    # Znalezienie wszystkich pól oznaczonych jako klucze (regularne)
    rows = soup.select("div.info-table span.info-table__content--regular")
    data = {}

    for row in rows:
        key = row.text.strip().removesuffix(":")

        if (key == "Social-Media" or
                key == "Name in home country"): continue

        # Szukanie wartości bezpośrednio po kluczu
        val_span = row.find_next_sibling("span")
        if val_span:
            # Jeżeli są linki, pobierz ich teksty
            links = val_span.select("a")
            if links:
                val = " ".join(link.text.strip() for link in links)
            else:
                val = val_span.get_text(strip=True)

            val = val.replace("\xa0", " ")
            data[key] = val

    # Wypisywanie wyników do terminala
    # for k, v in data.items():
    #     print(f"{k} {v}")

    # Zwracanie wynikowego słownika
    return data


# Funkcja analizuje historię transferów zawodnika na stronie Transfermarkt i zwraca je jako listę słowników
def parse_transfers(driver):
    # print("\nHistoria transferów:")

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Wybieramy wszystkie kontenery transferów (każdy transfer jest osobnym divem)
    grid_rows = soup.select("div.grid.tm-player-transfer-history-grid")

    transfers = []

    for i, row in enumerate(grid_rows):
        # Pobieranie elementów z transferu
        season = row.select_one(".tm-player-transfer-history-grid__season")
        date = row.select_one(".tm-player-transfer-history-grid__date")
        old_club = row.select_one(
            ".tm-player-transfer-history-grid__old-club .tm-player-transfer-history-grid__club-link")
        new_club = row.select_one(
            ".tm-player-transfer-history-grid__new-club .tm-player-transfer-history-grid__club-link")
        market_value = row.select_one(".tm-player-transfer-history-grid__market-value")
        fee = row.select_one(".tm-player-transfer-history-grid__fee")

        # Pomijamy niekompletne rekordy (np. nagłówki)
        if not season or not old_club or not new_club:
            continue

        # Tworzymy słownik z informacjami o transferze
        transfer_data = {
            "season": season.text.strip(),
            "date": date.text.strip() if date else "-",
            "old_club": old_club.text.strip(),
            "new_club": new_club.text.strip(),
            "market_value": market_value.text.strip() if market_value else "-",
            "transfer_fee": fee.text.strip() if fee else "-"
        }

        # Dodajemy do listy transferów
        transfers.append(transfer_data)

        # Debug: wypisujemy transfer do konsoli
        # print(f"\nTransfer {i + 1}:")
        # for k, v in transfer_data.items():
        #     print(f"{k}: {v}")

    return transfers


def simulate_user_scroll(driver, scroll_times=10, step=500):
    # print("Scrolluję stronę przez window.scrollBy(...) z debugiem...")

    # Aktywujemy okno i symulujemy kliknięcie w stronę
    driver.execute_script("window.focus();")
    driver.execute_script("document.body.click();")
    time.sleep(1)  # dajemy czas na przetworzenie

    for i in range(scroll_times):
        before = driver.execute_script("return window.scrollY")
        driver.execute_script(f"window.scrollBy(0, {step})")
        time.sleep(0.5)
        after = driver.execute_script("return window.scrollY")

        # print(f"Scroll {i+1}/{scroll_times} | Przed: {before}px -> Po: {after}px")

        if before == after:
            print("Nie przewinięto dalej – osiągnięto koniec strony lub scroll został zablokowany.")
            if before != 0:
                break


# Funkcja otwiera stronę profilu zawodnika, akceptuje cookies, przewija stronę, pobiera dane i zapisuje HTML
def get_player_profile(player_link):
    url = f"https://www.transfermarkt.com{player_link}"
    # print(f"\nOtwieram stronę: {url}")
    driver.get(url)

    # Obsługa cookies (również przez iframe)
    accept_cookies_if_present()

    try:
        # Czekamy na komponent transferów typu <tm-transfer-history> i symulujemy scroll
        transfer_component = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "tm-transfer-history"))
        )

        simulate_user_scroll(driver)  # symulujemy scrollowanie w dół
        time.sleep(3)  # dodatkowe czekanie na załadowanie dynamicznych danych

        # Parsowanie informacji o graczu
        parse_player_info(driver)

        # Czekamy na załadowanie danych transferowych (grid)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tm-player-transfer-history-grid"))
        )

        # Parsowanie historii transferów
        parse_transfers(driver)

    except Exception as e:
        # Obsługa błędów, zrzut ekranu i traceback
        print(f"Błąd ładowania profilu: {type(e).__name__} – {str(e)}")
        traceback.print_exc()


def get_player_awards(player_id):
    # Składamy URL do strony z nagrodami danego zawodnika
    url = f"https://www.transfermarkt.com/-/erfolge/spieler/{player_id}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # Wysyłamy zapytanie HTTP do strony
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Błąd pobierania strony: {response.status_code}")
        return []

    # Parsujemy HTML za pomocą BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Szukamy nagłówka sekcji z nagrodami
    titles_h2 = soup.find("h2", string=lambda x: x and "All titles" in x)
    if not titles_h2:
        print("Nie znaleziono nagłówka 'All titles'")
        return []

    # Pobieramy następną tabelę po nagłówku
    table = titles_h2.find_next("table")
    if not table:
        print("Nie znaleziono tabeli z nagrodami.")
        return []

    # Zbieramy wszystkie wiersze tabeli
    rows = table.find_all("tr")
    awards = []
    current_award = None

    for row in rows:
        # Jeśli wiersz to nagłówek nowej nagrody (klasa bg_Sturm)
        if "bg_Sturm" in row.get("class", []):
            award_name = row.get_text(strip=True)
            award_name = re.sub(r'^\d+x\s+', '', award_name)  # usuń "3x "

            current_award = {
                "title": award_name,
                "years": [],
                "clubs": []
            }
            awards.append(current_award)
        else:
            # Jeśli to wiersz z sezonem i opcjonalnie klubem
            tds = row.find_all("td")
            if len(tds) == 0 or current_award is None:
                continue

            # Rok/sezon zawsze jest w pierwszej kolumnie
            rok = tds[0].get_text(strip=True)
            # Klub, jeśli obecny, jest w ostatniej kolumnie
            klub = tds[-1].get_text(strip=True) if len(tds) > 2 else None
            klub = re.sub(r'\s*-\s*\d+\s+[Gg]oals$', '', klub)  # usuń "- 4 Goals" lub "- 10 goals"

            # Dodajemy dane do bieżącej nagrody
            current_award["years"].append(rok)
            if klub:
                current_award["clubs"].append(klub)

    return awards


def convert_transfermarkt_profile_data(data):
    new_dict = {}
    for key, value in data.items():
        clean_key = re.sub(r'[^a-z0-9_]', '',
                           key.strip()
                           .lower()
                           .replace(" ", "_")
                           .replace("/", "_"))

        # Specjalne traktowanie citizenship
        if clean_key == "citizenship" and isinstance(value, str):
            parsed_list = re.findall(r'[A-Z][a-z]+', value)
            new_dict[clean_key] = parsed_list
        elif clean_key == "player_agent" and isinstance(value, str):
            # usuwa "..." lub inne śmieciowe końcówki
            cleaned = re.sub(r'\s*\.\.\..*$', '', value).strip()
            new_dict[clean_key] = cleaned
        elif clean_key == "date_of_birth_age" and isinstance(value, str):
            # usuń nawiasy, np. (23)
            cleaned = re.sub(r'\s*\([^)]*\)', '', value).strip()
            clean_key = "date_of_birth"
            new_dict[clean_key] = cleaned
        else:
            new_dict[clean_key] = value

    return new_dict


def scrape_and_save_players_to_json(csv_path: str, output_path: str, limit: int = -1):
    # Wczytaj CSV
    df = pd.read_csv(csv_path)

    # Przygotuj listę wynikową
    players_data = []

    # Iteruj po wierszach z ograniczeniem
    for index, row in df.iterrows():
        if index >= limit != -1:
            break

        full_name = row['player']
        team = row['team']
        age = row['age']
        position = row['pos']
        nation = row['nation']

        # Poprawka dla tego gracza, rozwijamy jego imię, ponieważ Transfermarkt wskazuje na niepoprawny profil
        if full_name == "Dani Carvajal":
            full_name = "Daniel Carvajal"

        print(f"\nSzukam: {full_name} ({team}, {age} lat)")

        # Znajdź link do profilu
        player_link = find_player_profile_link(full_name)
        if not player_link:
            print(f"Nie znaleziono profilu dla: {full_name}")
            continue

        # Załaduj profil i zapisz HTML (Twój kod)
        get_player_profile(player_link)

        # Pobierz dane szczegółowe z otwartej strony (Twój kod)
        profile_info = parse_player_info(driver)
        transfer_info = parse_transfers(driver)

        # Wyciągnij ID zawodnika z URL i pobierz nagrody
        try:
            player_id = player_link.strip("/").split("/")[-1]
            awards = get_player_awards(player_id)
        except:
            awards = []

        # Zbuduj strukturę danych
        player_record = {
            "player": full_name,
            # "team": team,
            # "age": age,
            # "nation": nation,
            # "position": position,
            "transfermarkt_profile": convert_transfermarkt_profile_data(profile_info),
            "transfermarkt_transfers": transfer_info,
            "transfermarkt_awards": awards
        }

        players_data.append(player_record)

        print(f"Zapisano znalezione dane dla gracza {full_name}")

        # Odczekaj, by nie zostać zablokowanym
        time.sleep(2)

    # Zapisz JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(players_data, f, indent=2, ensure_ascii=False)

    print(f"\nZapisano dane do pliku: {output_path}")


scrape_and_save_players_to_json("nominees.csv", "players.json")

driver.quit()
