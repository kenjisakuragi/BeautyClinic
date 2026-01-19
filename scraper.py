import asyncio
import os
import sys
import psycopg2
from psycopg2.extras import execute_values
from playwright.async_api import async_playwright

# Database Connection
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable is not set.")
        sys.exit(1)
    return psycopg2.connect(db_url)

async def scrape_clinics():
    print("Starting scrape job...")
    
    # 1. Connect to DB to ensure it works
    conn = get_db_connection()
    cur = conn.cursor()
    print("Connected to Database.")
    
    # TODO: Implement the actual scraping logic here based on the phases:
    # Phase 1: Iterate Prefectures -> Areas -> Clinic List
    # Phase 2: Upsert Clinic URLs to 'clinics' table
    # Phase 3: Loop through 'clinics', visit details, and populate other tables.
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Example: Visit Top Page (just a smoke test for now)
        url = "https://clinic.beauty.hotpepper.jp/"
        print(f"Visiting {url}...")
        await page.goto(url)
        title = await page.title()
        print(f"Page Title: {title}")
        
        await browser.close()

    cur.close()
    conn.close()
    print("Scrape job finished.")

if __name__ == "__main__":
    asyncio.run(scrape_clinics())
