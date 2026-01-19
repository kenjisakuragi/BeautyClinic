# Hot Pepper Beauty Clinic Scraper - Implementation Plan (GitHub Actions + Supabase)

## 1. System Overview
This system scrapes beauty clinic information from [Hot Pepper Beauty](https://clinic.beauty.hotpepper.jp/) and stores it in a **Supabase (PostgreSQL)** database. The scraping process is automated using **GitHub Actions**.

## 2. Technology Stack
-   **Execution Environment**: GitHub Actions (Scheduled workflow / Manual trigger)
-   **Language**: Python 3.9+
-   **Scraping Library**: `playwright` (Headless browser)
-   **Database**: Supabase (PostgreSQL)
-   **DB Access**: `psycopg2` (standard PostgreSQL adapter) or `supabase` client.

## 3. Database Schema (PostgreSQL)

You will run a SQL script in the Supabase SQL Editor to create these tables.

### Table: `clinics`
Master table for clinics.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | BIGINT PK | Identity (Auto-increment) |
| `hp_id` | TEXT UNIQUE | HotPepper ID (e.g., H000587862) |
| `name` | TEXT | Clinic Name |
| `name_kana` | TEXT | Name Kana |
| `prefecture` | TEXT | Prefecture Name |
| `area` | TEXT | Area Name |
| `url` | TEXT | Detail Page URL |
| `scraped_at` | TIMESTAMPTZ | Last scraped timestamp |
| `created_at` | TIMESTAMPTZ | Default: NOW() |

### Table: `clinic_details`
Detailed information 1:1 with clinics.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | BIGINT PK | Identity |
| `clinic_id` | BIGINT FK | Ref `clinics.id` |
| `postal_code` | TEXT | |
| `address` | TEXT | Full address |
| `access` | TEXT | Access info |
| `phone_number` | TEXT | |
| `opening_hours` | TEXT | |
| `close_days` | TEXT | |
| `credit_cards` | TEXT | |
| `description` | TEXT | |
| `catch_copy` | TEXT | |
| `staff_count` | TEXT | |
| `num_rooms` | TEXT | |
| `image_url` | TEXT | Main image URL |

### Table: `menus`
Treatment menus.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | BIGINT PK | Identity |
| `clinic_id` | BIGINT FK | Ref `clinics.id` |
| `category` | TEXT | |
| `name` | TEXT | |
| `price` | TEXT | Raw string |
| `price_value` | INTEGER | Parsed value |
| `description` | TEXT | |

### Table: `doctors`
Doctor profiles.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | BIGINT PK | Identity |
| `clinic_id` | BIGINT FK | Ref `clinics.id` |
| `name` | TEXT | |
| `job_title` | TEXT | |
| `profile` | TEXT | |
| `image_url` | TEXT | |

### Table: `cases`
Case studies.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | BIGINT PK | Identity |
| `clinic_id` | BIGINT FK | Ref `clinics.id` |
| `title` | TEXT | |
| `price` | TEXT | |
| `before_image` | TEXT | |
| `after_image` | TEXT | |
| `description` | TEXT | |

## 4. Setup & Deployment Workflow

### Phase 1: Supabase Setup (User Action)
1.  Create a Supabase project.
2.  Run the provided `schema.sql` in the Supabase SQL Editor to create tables.
3.  Get **Connection String** (URI) (e.g., `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`).

### Phase 2: GitHub Repository Setup (User Action)
1.  Push this code to a GitHub repository.
2.  Go to **Settings > Secrets and variables > Actions**.
3.  Add Repository Secret:
    -   `DATABASE_URL`: The connection string from Supabase.

### Phase 3: Code Implementation (Agent Action)
-   `requirements.txt`: Add `playwright`, `psycopg2-binary`.
-   `scraper.py`: Main logic handling DB connection and Playwright.
-   `.github/workflows/scrape.yml`: Workflow definition.

### Phase 4: Execution
-   The workflow will run on schedule (e.g., weekly) or manually.
-   Artifacts/Logs can be viewed in GitHub Actions tab.
## 1. System Overview
This system scrapes beauty clinic information from [Hot Pepper Beauty](https://clinic.beauty.hotpepper.jp/) and stores it in a local SQLite database.

## 2. Technology Stack
-   **Language**: Python 3.9+
-   **Scraping Library**: Playwright (for reliable dynamic content handling) or Requests/BeautifulSoup (if speed is prioritized and pages are static enough). *Decision: Playwright for robustness against potential JS rendering.*
-   **Database**: SQLite (File-based, easy to transport)
-   **ORM/DB Access**: Standard `sqlite3` library or reliable wrapper.

## 3. Database Schema

### Table: `clinics`
Master table for clinics.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK | Auto-increment ID |
| `hp_id` | TEXT | HotPepper ID (e.g., H000587862) - Unique |
| `name` | TEXT | Clinic Name |
| `name_kana` | TEXT | Name Kana |
| `prefecture` | TEXT | Prefecture Name |
| `area` | TEXT | Area Name |
| `url` | TEXT | Detail Page URL |
| `scraped_at` | DATETIME | Last scraped timestamp |

### Table: `clinic_details`
Detailed information 1:1 with clinics.
| Column | Type | Description |
| :--- | :--- | :--- |
| `clinic_id` | INTEGER FK | Ref `clinics.id` |
| `postal_code` | TEXT | |
| `address` | TEXT | Full address |
| `access` | TEXT | Access info |
| `phone_number` | TEXT | |
| `opening_hours` | TEXT | |
| `close_days` | TEXT | |
| `credit_cards` | TEXT | |
| `description` | TEXT | Introduction text |
| `catch_copy` | TEXT | |
| `staff_count` | TEXT | |
| `num_rooms` | TEXT | |
| `image_url` | TEXT | Main image URL |

### Table: `features`
Many-to-Many or specific flags for clinics (optional, or store as JSON in details).

### Table: `menus`
Treatment menus.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK | |
| `clinic_id` | INTEGER FK | |
| `category` | TEXT | e.g., "二重整形" |
| `name` | TEXT | Menu name |
| `price` | TEXT | Raw price string |
| `price_value` | INTEGER | Parsed integer price (for sorting) |
| `description` | TEXT | |

### Table: `doctors`
Doctor profiles.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK | |
| `clinic_id` | INTEGER FK | |
| `name` | TEXT | |
| `name_kana` | TEXT | |
| `job_title` | TEXT | |
| `profile` | TEXT | Biography/Profile text |
| `image_url` | TEXT | |

### Table: `cases`
Case studies (Before/After).
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK | |
| `clinic_id` | INTEGER FK | |
| `title` | TEXT | |
| `category` | TEXT | |
| `price` | TEXT | |
| `before_image` | TEXT | URL |
| `after_image` | TEXT | URL |
| `description` | TEXT | |

## 4. Work Process

### Phase 1: Setup
-   Initialize `beauty_clinic.db`.
-   Install dependencies (`playwright`, `lxml` etc).

### Phase 2: Crawler (List Collection)
-   Iterate through all 47 Prefectures.
-   Handle pagination to collect ALL clinic URLs.
-   Store initial data into `clinics` table (ID, Name, URL) to allow resuming.

### Phase 3: Scraper (Detail Collection)
-   Iterate through `clinics` rows where `scraped_at` is NULL or old.
-   For each clinic, visit the URL.
-   Parse "Top", "Menu", "Doctor", "Case" tabs (HotPepper often puts these on separate sub-pages or tabs).
-   Upsert data into child tables (`clinic_details`, `menus`, etc.).
-   Update `scraped_at`.

### Phase 4: Output/Validation
-   Export to CSV/Excel for user verification if needed.

