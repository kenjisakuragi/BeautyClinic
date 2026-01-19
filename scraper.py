import asyncio
import os
import sys
import re
from datetime import datetime
import psycopg2
from playwright.async_api import async_playwright

# Database Connection
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable is not set.")
        sys.exit(1)
    return psycopg2.connect(db_url)

def upsert_clinic(conn, clinic):
    """
    Insert or Update a clinic record.
    clinic dict: hp_id, name, name_kana, url, prefecture, area
    """
    sql = """
    INSERT INTO clinics (hp_id, name, url, prefecture, area, scraped_at)
    VALUES (%s, %s, %s, %s, %s, NOW())
    ON CONFLICT (hp_id) 
    DO UPDATE SET 
        name = EXCLUDED.name,
        url = EXCLUDED.url,
        scraped_at = NOW();
    """
    cur = conn.cursor()
    try:
        cur.execute(sql, (
            clinic['hp_id'],
            clinic['name'],
            clinic['url'],
            clinic.get('prefecture'),
            clinic.get('area')
        ))
        conn.commit()
    except Exception as e:
        print(f"Error upserting clinic {clinic['hp_id']}: {e}")
        conn.rollback()
    finally:
        cur.close()

async def scrape_clinics():
    print("Starting scrape job...")
    conn = get_db_connection()
    print("Connected to Database.")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
async def scrape_clinics():
    print("Starting scrape job...")
    conn = get_db_connection()
    print("Connected to Database.")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # DEBUG: Use a direct URL for Tokyo Search Results to ensure we land on a list page.
        # This URL searches for Service Code SC01 (Esthetic/Clinic) in Prefecture 13 (Tokyo)
        start_url = "https://clinic.beauty.hotpepper.jp/search?sc_cd=SC01&prefecture_cd=13"
        print(f"Visiting Direct Search URL: {start_url}")
        
        try:
            await page.goto(start_url, timeout=60000)
            await page.wait_for_load_state("domcontentloaded")
            # Wait a bit for any dynamic content
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Error loading page: {e}")
            await browser.close()
            return

        title = await page.title()
        print(f"Page Title: {title}")

        # Debug: Check if we are on a list page by looking for common list elements
        # HotPepper Beauty usually uses 'cassette' style classes for items.
        # Let's try to grab all links and count how many look like clinic details.
        
        clinic_links = await page.locator("a").all()
        print(f"Total links on page: {len(clinic_links)}")
        
        count_in_page = 0
        
        # Capture raw HTML for debugging if we find 0 clinics
        page_content = await page.content()

        for link in clinic_links:
            href = await link.get_attribute("href")
            if not href:
                continue
            
            # Refined Pattern: Clinic DB matches typically have /H\d{9}/ or similar.
            # Example: /KR000000001/H000888888/
            # Or just /H000.../
            
            # Hotpepper Beauty often links to detail pages like: https://clinic.beauty.hotpepper.jp/H000661142/
            if "/H00" in href:
                # Extract HP_ID
                match = re.search(r'/(H\d+)/', href)
                if match:
                    hp_id = match.group(1)
                    full_url = href
                    if not href.startswith("http"):
                        full_url = "https://clinic.beauty.hotpepper.jp" + href if href.startswith("/") else "https://clinic.beauty.hotpepper.jp/" + href
                    
                    try:
                        # Attempt to get name from the text of the link
                        # If the link wraps an image, we might need to look at alt text or parent containers.
                        # For now, let's grab all text inside the anchor.
                        name = await link.inner_text()
                        name = name.strip() or "Unknown Name"
                        
                        # Sometimes multiple links point to the same clinic (image, title, button).
                        # We will just upsert them all; the latest valid name will persist or we filter by length.
                        if len(name) < 2: 
                            continue

                        print(f"  Found Clinic: {name} ({hp_id})")
                        
                        clinic_data = {
                            "hp_id": hp_id,
                            "name": name,
                            "url": full_url,
                            "prefecture": "Unknown", # Todo
                            "area": "Unknown"
                        }
                        
                        upsert_clinic(conn, clinic_data)
                        count_in_page += 1
                    except Exception as e:
                        print(f"  Error processing link {href}: {e}")

        print(f"    Found {count_in_page} clinics on this page.")
        
        if count_in_page == 0:
            print("WARNING: No clinics found. Dumping HTML snippet for debugging...")
            print(page_content[:1000]) # First 1000 chars
            # Also dump a file artifact if run locally, but for GHA we rely on stdout.

        await browser.close()

    conn.close()
    print("Scrape job finished.")
    conn.close()
    print("Scrape job finished.")

if __name__ == "__main__":
    asyncio.run(scrape_clinics())
