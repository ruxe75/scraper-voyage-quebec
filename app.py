from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime
import time

# === USER PREFERENCES ===
BUDGET = 2000       # CAD per person
DEPARTURE_CITY = "Quebec City"
TRAVEL_LENGTH = 7   # nights
KEYWORDS = [
    "Breathless", "Riu", "Hard Rock", "Royalton CHIC", "Excellence",
    "TRS", "Barcel", "Temptation", "Secrets", "Hyatt Zilara"
]
EXCLUDE_COUNTRIES = ["cuba"]

# === INIT SELENIUM DRIVER ===
def init_driver():
    options = Options()
    options.add_argument("--headless=new")  # headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)  # will auto-download driver in Selenium 4.10+

# === GENERIC SCRAPER FUNCTION ===
def scrape_site(driver, provider, url, card_sel, title_sel, price_sel, dep_sel):
    matches = []
    driver.get(url)
    time.sleep(5)  # let JS load, can improve with WebDriverWait

    cards = driver.find_elements(By.CSS_SELECTOR, card_sel)
    for card in cards:
        try:
            title = card.find_element(By.CSS_SELECTOR, title_sel).text.strip()
        except:
            continue

        # Exclude Cuba
        if any(c in title.lower() for c in EXCLUDE_COUNTRIES):
            continue

        try:
            price_txt = card.find_element(By.CSS_SELECTOR, price_sel).text.strip()
            price = int(price_txt.replace('$', '').replace(',', ''))
        except:
            continue

        try:
            departure = card.find_element(By.CSS_SELECTOR, dep_sel).text.strip()
        except:
            departure = DEPARTURE_CITY

        if DEPARTURE_CITY.lower() in departure.lower() and price <= BUDGET \
                and any(k.lower() in title.lower() for k in KEYWORDS):
            matches.append((provider, title, price, departure))
    return matches

# === SPECIFIC PROVIDERS ===
def scrape_sunwing(driver):
    return scrape_site(driver, "Sunwing",
        "https://www.sunwing.ca/en/dealzone/last-minute",
        ".deal-card", ".deal-title", ".deal-price", ".deal-departure")

def scrape_airtransat(driver):
    return scrape_site(driver, "Air Transat",
        "https://www.airtransat.com/en-CA/last-minute-deals",
        ".deal-card", ".deal-title", ".deal-price", ".deal-departure")

def scrape_westjet(driver):
    return scrape_site(driver, "WestJet",
        "https://www.westjet.com/en-ca/deals-packages/vacation-deals",
        ".deal-card", ".deal-title", ".deal-price", ".deal-departure")

def scrape_aircanada(driver):
    return scrape_site(driver, "Air Canada Vacations",
        "https://vacations.aircanada.com/en/deals/last-minute",
        ".deal-card", ".deal-title", ".deal-price", ".deal-departure")

# === MAIN RUN ===
if __name__ == "__main__":
    driver = init_driver()
    try:
        all_matches = []
        all_matches.extend(scrape_sunwing(driver))
        all_matches.extend(scrape_airtransat(driver))
        all_matches.extend(scrape_westjet(driver))
        all_matches.extend(scrape_aircanada(driver))

        if not all_matches:
            print("No matching deals found.")
        else:
            print(f"Found {len(all_matches)} matching deals:\n")
            for prov, title, price, dep in all_matches:
                print(f"{prov}: {title} — ${price} — {dep}")

    finally:
        driver.quit()

