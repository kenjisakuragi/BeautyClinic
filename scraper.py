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
        
        # 1. Visit Top Page to find Prefecture Links
        # For efficiency in this demo, let's target a list page directly or assume we want to crawl by prefecture.
        # Let's visit the "Search by Area" page or similar.
        base_url = "https://clinic.beauty.hotpepper.jp"
        print(f"Visiting {base_url}...")
        await page.goto(base_url)
        
        # Simple Logic: Find links that look like search results or area selections.
        # Often these are like /SC001/ (Area code) or specific search URLs.
        # For reliability, let's try to grab 'Tokyo' specifically to guarantee results in this run,
        # or iterate all 'prefecture' classes if identifiable.
        
        # Trying to find all links that match the pattern /search/
        # A safer bet for a generic scraper is to assume valid detail pages match /H\d+/
        # But we need a list source.
        
        # Let's try to navigate to 'Kanto' -> 'Tokyo' for the first batch.
        # If selectors fail, we fallback to a direct search URL for Tokyo.
        target_url = "https://clinic.beauty.hotpepper.jp/search?kodawari_condition=1&svc_cd=SC01&prefecture_cd=13" # Tokyo ID usually 13 in generic systems, let's check
        # Actually, let's use a known listing URL pattern if possible.
        # Strategy: Get valid links from the page content.
        
        # Revisiting Strategy: Just seek unique clinic links from the top page and its sub-pages.
        # But top page usually has "Recommended" sections.
        
        # Let's try to crawl the specific Tokyo Search URL to ensure volume.
        # Note: This URL structure is a hypothesis, if it fails, the script should handle it.
        # Better: Use the site's navigation.
        
        # Let's click "関東" (Kanto) if it exists, or just use a wide search.
        # We will attempt to find a "Search" button or link.
        
        # FALLBACK: Direct URL for a broad search (e.g., "All Clinics" often isn't a single page).
        # We will iterate through a hardcoded list of major prefecture area codes if dynamic fails?
        # No, let's be dynamic.
        
        links = await page.locator("a").all()
        start_urls = []
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if href and "search" in href and ("東京" in text or "関東" in text):
                full_url = base_url + href if href.startswith("/") else href
                start_urls.append(full_url)
        
        # If no specific links found, default to a known search entry
        if not start_urls:
            print("Could not find specific area links, trying default search...")
            start_urls = ["https://clinic.beauty.hotpepper.jp/search"] 

        # Limit for demo
        start_urls = list(set(start_urls))[:3]
        print(f"Found search entry points: {start_urls}")

        for search_url in start_urls:
            print(f"Processing Search URL: {search_url}")
            try:
                await page.goto(search_url)
                await page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"Failed to load {search_url}: {e}")
                continue

            # Pagination Loop
            page_count = 0
            while page_count < 3: # Limit to 3 pages per area for safety
                page_count += 1
                print(f"  Scraping page {page_count}...")
                
                # Extract Clinic Links
                # Selector: Usually links to /H00...
                # We look for anchor tags containing /H\d+/ 
                # And usually inside a result cassette.
                
                clinic_links = await page.locator("a[href*='/H']").all()
                count_in_page = 0
                
                for link in clinic_links:
                    href = await link.get_attribute("href")
                    # Check if it looks like a clinic ID (H followed by digits)
                    match = re.search(r'/(H\d+)/', href)
                    if match:
                        hp_id = match.group(1)
                        if href.startswith("/"):
                            href = base_url + href
                        
                        # Try to get name
                        # This selector might need adjustment based on valid HTML
                        # Often the name is inside the <a> or a specific <h3> parent
                        name = await link.inner_text()
                        name = name.strip()
                        if not name:
                            continue # Skip empty or image links if no alt text

                        # Simple clean up of Name (remove newlines etc)
                        name = name.split('\n')[0]

                        clinic_data = {
                            "hp_id": hp_id,
                            "name": name,
                            "url": href,
                            "prefecture": "Unknown", # Todo: extract from breadcrumb
                            "area": "Unknown"
                        }
                        
                        upsert_clinic(conn, clinic_data)
                        count_in_page += 1
                
                print(f"    Found {count_in_page} clinics on this page.")
                
                # Check for "Next Page"
                # Class often 'paging-next' or text '次へ'
                next_buttons = await page.locator("a:has-text('次へ')").all()
                if next_buttons:
                    try:
                        next_url = await next_buttons[0].get_attribute("href")
                        if next_url:
                            if next_url.startswith("/"):
                                next_url = base_url + next_url
                            await page.goto(next_url)
                            await page.wait_for_load_state("networkidle")
                        else:
                            break
                    except:
                        break
                else:
                    break

    conn.close()
    print("Scrape job finished.")

if __name__ == "__main__":
    asyncio.run(scrape_clinics())
