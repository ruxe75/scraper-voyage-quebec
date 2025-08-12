import sys, subprocess, os

# Auto-install if missing (for Streamlit Cloud)
for pkg in ["streamlit", "selenium", "fpdf2"]:
    try:
        __import__(pkg.split()[0])
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", pkg])

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from fpdf import FPDF
from datetime import datetime
import time

# ==== USER FILTER SETTINGS ====
BUDGET = 2000
DEPARTURE_CITY = "Quebec City"
KEYWORDS = ["Breathless", "Riu", "Hard Rock", "Royalton CHIC",
            "Excellence", "TRS", "Barcel", "Temptation", "Secrets", "Hyatt Zilara"]
EXCLUDE_COUNTRIES = ["cuba"]

# ==== DEAL DATA STRUCTURE ====
class Deal:
    def __init__(self, provider, title, price, departure_city, link=""):
        self.provider = provider
        self.title = title
        self.price = price
        self.departure_city = departure_city
        self.link = link
        self.party_score, self.food_score, self.drinks_score = self.rate()

    def rate(self):
        name = self.title.lower()
        party = food = drinks = 5
        if any(k.lower() in name for k in ["breathless", "temptation", "riu", "hard rock", "chic"]):
            party = 9
        elif "barcel" in name or "hyatt zilara" in name:
            party = 8
        elif "secrets" in name or "excellence" in name:
            party = 7
        if any(k in name for k in ["gourmet", "excellence", "royalton chic", "hyatt"]):
            food = drinks = 9
        elif "riu" in name or "hard rock" in name:
            food = drinks = 8
        else:
            food = drinks = 7
        return party, food, drinks

# ==== INIT SELENIUM DRIVER ====
def init_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Detect if running on Streamlit Cloud (Linux, no Chrome preinstalled)
    if os.path.exists("/usr/bin/chromium-browser"):
        options.binary_location = "/usr/bin/chromium-browser"
        return webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=options)
    else:
        return webdriver.Chrome(options=options)  # local run (Selenium 4.x auto driver)

# ==== GENERIC SCRAPER ====
def scrape_site(driver, name, url, card_sel, title_sel, price_sel, dep_sel, link_sel):
    deals = []
    driver.get(url)
    time.sleep(5)
    cards = driver.find_elements(By.CSS_SELECTOR, card_sel)
    for card in cards:
        try:
            title = card.find_element(By.CSS_SELECTOR, title_sel).text.strip()
            if any(c in title.lower() for c in EXCLUDE_COUNTRIES):
                continue
            price_txt = card.find_element(By.CSS_SELECTOR, price_sel).text.strip().replace("$", "").replace(",", "")
            try:
                price = int(price_txt)
            except:
                continue
            departure = card.find_element(By.CSS_SELECTOR, dep_sel).text.strip() if dep_sel else DEPARTURE_CITY
            if price > BUDGET or DEPARTURE_CITY.lower() not in departure.lower():
                continue
            if not any(k.lower() in title.lower() for k in KEYWORDS):
                continue
            link = ""
            try:
                link = card.find_element(By.CSS_SELECTOR, link_sel).get_attribute("href")
            except:
                pass
            deals.append(Deal(name, title, price, departure, link))
        except:
            continue
    return deals

# ==== SCRAPE ALL PROVIDERS ====
def get_all_deals():
    driver = init_driver()
    all_deals = []
    try:
        all_deals += scrape_site(driver, "Sunwing",
            "https://www.sunwing.ca/en/dealzone/last-minute",
            ".deal-card", ".deal-title", ".deal-price", ".deal-departure", "a")
        all_deals += scrape_site(driver, "Air Transat",
            "https://www.airtransat.com/en-CA/last-minute-deals",
            ".deal-card", ".deal-title", ".deal-price", ".deal-departure", "a")
        all_deals += scrape_site(driver, "WestJet",
            "https://www.westjet.com/en-ca/deals-packages/vacation-deals",
            ".deal-card", ".deal-title", ".deal-price", ".deal-departure", "a")
        all_deals += scrape_site(driver, "Air Canada Vacations",
            "https://vacations.aircanada.com/en/deals/last-minute",
            ".deal-card", ".deal-title", ".deal-price", ".deal-departure", "a")
        all_deals += scrape_site(driver, "RedTag",
            "https://www.redtag.ca/last-minute-vacations.php",
            ".product-listing", "h2", ".price", ".departure", "a")
        all_deals += scrape_site(driver, "TripCentral",
            "https://www.tripcentral.ca/last-minute-vacations.html",
            ".pkgBox", ".pkgTitle", ".pkgPrice", ".pkgFrom", "a")
        all_deals += scrape_site(driver, "VoyageVacances",
            "https://www.voyagevacances.com/last-minute",
            ".deal", "h3", ".price", ".departure", "a")
    finally:
        driver.quit()
    return all_deals

# ==== PDF EXPORT ====
def generate_pdf(deals):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "Quebec City Party-Friendly Last-Minute Deals", ln=True)
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 10, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(5)
    for d in deals:
        pdf.multi_cell(0, 6, f"{d.provider} — {d.title}")
        pdf.multi_cell(0, 6, f"Price: ${d.price} CAD | Departure: {d.departure_city}")
        pdf.multi_cell(0, 6, f"Party:{d.party_score}/10 | Food:{d.food_score}/10 | Drinks:{d.drinks_score}/10")
        if d.link: pdf.multi_cell(0, 6, f"Link: {d.link}")
        pdf.ln(3)
    return pdf.output(dest="S").encode("latin1")

# ==== STREAMLIT UI ====
st.set_page_config(page_title="QC All-Inclusive Deals", layout="wide")
st.title("🏝 Quebec City - Last-Minute All-Inclusive Party-Friendly Deals")

if st.button("Fetch Latest Deals"):
    with st.spinner("Scraping live sites (20-40 sec)..."):
        deals = get_all_deals()
    if not deals:
        st.error("No deals found right now.")
    else:
        deals.sort(key=lambda x: (x.party_score + x.food_score + x.drinks_score), reverse=True)
        st.success(f"Found {len(deals)} matching deals")
        st.table([[d.provider, d.title, f"${d.price}", d.departure_city,
                   d.party_score, d.food_score, d.drinks_score, d.link] for d in deals])
        st.download_button("📄 Download PDF Report", data=generate_pdf(deals),
                           file_name="vacation_deals.pdf", mime="application/pdf")
else:
    st.info("Click 'Fetch Latest Deals' to start.")
