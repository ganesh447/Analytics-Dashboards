from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re

REGION_URLS = {
    "pacific": "https://liquipedia.net/valorant/VCT/2025/Pacific_League/Kickoff/Statistics",
    "americas": "https://liquipedia.net/valorant/VCT/2025/Americas_League/Kickoff/Statistics",
    "emea": "https://liquipedia.net/valorant/VCT/2025/EMEA_League/Kickoff/Statistics",
    "china": "https://liquipedia.net/valorant/VCT/2025/China_League/Kickoff/Statistics"
}

def table_to_df(table):
    headers = [th.text.strip() for th in table.find_elements(By.CSS_SELECTOR, "tr:first-child th")]
    rows_data = []
    for row in table.find_elements(By.CSS_SELECTOR, "tr")[1:]:
        tds = row.find_elements(By.TAG_NAME, "td")
        cols = []
        for td in enumerate(tds):
            imgs = td.find_elements(By.TAG_NAME, "img")
            if imgs:
                col_val = " | ".join([img.get_attribute("alt") for img in imgs if img.get_attribute("alt")])
                text = td.text.strip()
                col_val = (col_val + " " + text).strip() if text else col_val
                cols.append(col_val)
            else:
                cols.append(td.text.strip())
        if not cols or len(cols) != len(headers):
            continue
        rows_data.append(cols)
    df = pd.DataFrame(rows_data, columns=headers)
    return df

def get_region_stats(region, url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "table.wikitable"))
    )
    tables = driver.find_elements(By.CSS_SELECTOR, "table.wikitable")
    print(f"[{region.upper()}] Found {len(tables)} wikitable tables.")

    all_elements = driver.find_elements(By.XPATH, "//*")
    table_indices = [i for i, el in enumerate(all_elements) if el.tag_name == "table" and "wikitable" in el.get_attribute("class")]

    table_sections = []
    for idx in table_indices:
        heading = "table"
        for j in range(idx-1, -1, -1):
            tag = all_elements[j].tag_name
            if tag in ("h2", "h3", "h4"):
                heading = all_elements[j].text.strip()
                heading = re.sub(r'[\\/*?:"<>|]', "", heading)
                break
        table_sections.append(heading)

    dfs = {}
    for tbl, section in zip(tables, table_sections):
        df = table_to_df(tbl)
        if df.empty:
            continue
        key = f"{region.lower()}_{section.lower().replace(' ', '_')}"
        dfs[key] = df
        df.to_csv(f"{key}.csv", index=False)
        print(f"[{region.upper()}] Saved: {key}.csv [{df.shape[0]} rows]")

    driver.quit()
    return dfs

if __name__ == "__main__":
    all_stats = {}
    for region, url in REGION_URLS.items():
        print(f"\nScraping {region.title()}...")
        region_stats = get_region_stats(region, url)
        all_stats[region] = region_stats
    # Now all_stats contains all DataFrames by region and table
    # Optionally: print a quick preview
    for region, tables in all_stats.items():
        print(f"\nRegion: {region.title()}")
        for name, df in tables.items():
            print(f"\n--- {name} ---")
            print(df.head())
