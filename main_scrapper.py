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

chrome_driver_path = "C:\chromedriver-win64\chromedriver.exe"

service = Service(executable_path=chrome_driver_path)
options = webdriver.ChromeOptions()

options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(service=service, options=options)
driver.switch_to.window(driver.current_window_handle)

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

clicked = False


def accept_cookies_if_present():
    global clicked
    if clicked:
        return

    iframes = driver.find_elements(By.TAG_NAME, "iframe")

    for index, iframe in enumerate(iframes):
        try:
            driver.switch_to.frame(iframe)

            button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Accept & continue')]"))
            )
            button.click()
            print("Clicked cookies in iframe!")

            clicked = True

            driver.execute_script(
                "document.body.style.overflow = 'auto';"
                "document.documentElement.style.overflow = 'auto';"
            )

            driver.switch_to.default_content()

            time.sleep(1)
            driver.refresh()
            return
        except:
            driver.switch_to.default_content()


def find_player_profile_link(player_name):
    search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={player_name.replace(' ', '+')}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(search_url, headers=headers)

    if response.status_code != 200:
        print("Error fetching search results.")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    player_list = soup.find_all('tr', class_='odd') + soup.find_all('tr', class_='even')

    if player_list:
        first_player = player_list[0]
        player_name = first_player.find('td', class_='hauptlink').text.strip()
        player_link = first_player.find('td', class_='hauptlink').find('a')['href']
        print(f'Found: {player_name} - {player_link}')
        return player_link
    else:
        print('No results found for this player.')
        return None


def parse_player_info(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")

    headline = soup.find("span", string=lambda s: s and "Facts and data" in s)
    if not headline:
        print("'Facts and data' section not found.")
        return {}

    info_block = headline.find_next("div", class_=lambda c: c and "info-table" in c)
    if not info_block:
        print("Player data block not found.")
        return {}

    rows = soup.select("div.info-table span.info-table__content--regular")
    data = {}

    for row in rows:
        key = row.text.strip().removesuffix(":")

        if (key == "Social-Media" or
                key == "Name in home country"): continue

        val_span = row.find_next_sibling("span")
        if val_span:
            links = val_span.select("a")
            if links:
                val = " ".join(link.text.strip() for link in links)
            else:
                val = val_span.get_text(strip=True)

            val = val.replace("\xa0", " ")
            data[key] = val

    return data


def parse_transfers(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    grid_rows = soup.select("div.grid.tm-player-transfer-history-grid")
    transfers = []

    for i, row in enumerate(grid_rows):
        season = row.select_one(".tm-player-transfer-history-grid__season")
        date = row.select_one(".tm-player-transfer-history-grid__date")
        old_club = row.select_one(
            ".tm-player-transfer-history-grid__old-club .tm-player-transfer-history-grid__club-link")
        new_club = row.select_one(
            ".tm-player-transfer-history-grid__new-club .tm-player-transfer-history-grid__club-link")
        market_value = row.select_one(".tm-player-transfer-history-grid__market-value")
        fee = row.select_one(".tm-player-transfer-history-grid__fee")

        if not season or not old_club or not new_club:
            continue

        transfer_data = {
            "season": season.text.strip(),
            "date": date.text.strip() if date else "-",
            "old_club": old_club.text.strip(),
            "new_club": new_club.text.strip(),
            "market_value": market_value.text.strip() if market_value else "-",
            "transfer_fee": fee.text.strip() if fee else "-"
        }

        transfers.append(transfer_data)

    return transfers


def simulate_user_scroll(driver, scroll_times=10, step=500):
    driver.execute_script("window.focus();")
    driver.execute_script("document.body.click();")
    time.sleep(1)

    for i in range(scroll_times):
        before = driver.execute_script("return window.scrollY")
        driver.execute_script(f"window.scrollBy(0, {step})")
        time.sleep(0.5)
        after = driver.execute_script("return window.scrollY")

        if before == after:
            print("No further scroll - reached end of page or scroll was blocked.")
            if before != 0:
                break


def get_player_profile(player_link):
    url = f"https://www.transfermarkt.com{player_link}"
    driver.get(url)
    accept_cookies_if_present()

    try:
        transfer_component = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "tm-transfer-history"))
        )

        simulate_user_scroll(driver)
        time.sleep(3)

        parse_player_info(driver)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tm-player-transfer-history-grid"))
        )

        parse_transfers(driver)

    except Exception as e:
        print(f"Profile loading error: {type(e).__name__} - {str(e)}")
        traceback.print_exc()


def get_player_awards(player_id):
    url = f"https://www.transfermarkt.com/-/erfolge/spieler/{player_id}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Page fetch error: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    titles_h2 = soup.find("h2", string=lambda x: x and "All titles" in x)
    if not titles_h2:
        print("'All titles' header not found")
        return []

    table = titles_h2.find_next("table")
    if not table:
        print("Awards table not found.")
        return []

    rows = table.find_all("tr")
    awards = []
    current_award = None

    try:
        for row in rows:
            if "bg_Sturm" in row.get("class", []):
                award_name = row.get_text(strip=True)
                award_name = re.sub(r'^\d+x\s+', '', award_name)

                current_award = {
                    "title": award_name,
                    "years": [],
                    "clubs": []
                }
                awards.append(current_award)
            else:
                tds = row.find_all("td")
                if len(tds) == 0 or current_award is None:
                    continue

                rok = tds[0].get_text(strip=True)
                klub = tds[-1].get_text(strip=True) if len(tds) > 2 else None
                if klub:
                    klub = re.sub(r'\s*-\s*\d+\s+[Gg]oals$', '', klub)
                    current_award["clubs"].append(klub)

                current_award["years"].append(rok)

    except ValueError as e:
        print(f"Exception occurred: {e}")

    return awards


def convert_transfermarkt_profile_data(data):
    new_dict = {}
    for key, value in data.items():
        clean_key = re.sub(r'[^a-z0-9_]', '',
                           key.strip()
                           .lower()
                           .replace(" ", "_")
                           .replace("/", "_"))

        if clean_key == "citizenship" and isinstance(value, str):
            parsed_list = re.findall(r'[A-Z][a-z]+', value)

            for i in range(len(parsed_list) - 1):
                if parsed_list[i] == "Sierra" and parsed_list[i + 1] == "Leone":
                    parsed_list[i] = "Sierra Leone"
                    del parsed_list[i + 1]
                    break
            new_dict[clean_key] = parsed_list
        elif clean_key == "player_agent" and isinstance(value, str):
            cleaned = re.sub(r'\s*\.\.\..*$', '', value).strip()
            new_dict[clean_key] = cleaned
        elif clean_key == "date_of_birth_age" and isinstance(value, str):
            cleaned = re.sub(r'\s*\([^)]*\)', '', value).strip()
            clean_key = "date_of_birth"
            new_dict[clean_key] = cleaned
        else:
            new_dict[clean_key] = value

    return new_dict


def scrape_and_save_players_to_json(csv_path: str, output_path: str, limit: int = -1):
    df = pd.read_csv(csv_path)
    players_data = []

    for index, row in df.iterrows():
        if index >= limit != -1:
            break

        full_name = row['player']
        team = row['team']
        age = row['age']

        # Fix for this player, expand his name because Transfermarkt points to incorrect profile
        if full_name == "Dani Carvajal":
            full_name = "Daniel Carvajal"

        print(f"\nSearching: {full_name} ({team}, {age} years old)")

        player_link = find_player_profile_link(full_name)
        if not player_link:
            print(f"Profile not found for: {full_name}")
            continue

        get_player_profile(player_link)
        profile_info = parse_player_info(driver)
        transfer_info = parse_transfers(driver)

        try:
            player_id = player_link.strip("/").split("/")[-1]
            awards = get_player_awards(player_id)
        except:
            awards = []
            print("Failed to retrieve player awards", full_name)

        player_record = {
            "player": full_name,
            "transfermarkt_profile": convert_transfermarkt_profile_data(profile_info),
            "transfermarkt_transfers": transfer_info,
            "transfermarkt_awards": awards
        }

        players_data.append(player_record)
        print(f"Saved found data for player {full_name}")
        time.sleep(2)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(players_data, f, indent=2, ensure_ascii=False)

    print(f"\nData saved to file: {output_path}")


scrape_and_save_players_to_json("nominees.csv", "players.json")

driver.quit()
