"""
Database initialization script for the Global Disaster Database.
Uses the team's cleaned CSV (disasters_cleaned.csv) + World Bank data.

Team: Krishna Koushik Thokala, Anirudh Sukumaran, Prathima Sola
AI Assistance: Claude (Anthropic, Claude Opus 4.6), April 2026
"""
import csv, sqlite3, os

def init_db(db_path="disaster_events.db", data_dir="."):
    cleaned_csv = os.path.join(data_dir, "disasters_cleaned.csv")
    if not os.path.exists(cleaned_csv):
        cleaned_csv = os.path.join(data_dir, "disasters_raw.csv")
    gdp_csv = os.path.join(data_dir, "gdp_raw.csv")
    meta_csv = os.path.join(data_dir, "country_meta.csv")

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # -- Author: Krishna Koushik Thokala
    cur.executescript("""
    CREATE TABLE regions (
        region_id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_name TEXT NOT NULL UNIQUE, continent TEXT NOT NULL
    );
    CREATE TABLE countries (
        country_id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_name TEXT NOT NULL, iso_code TEXT NOT NULL UNIQUE,
        region_id INTEGER NOT NULL, population INTEGER,
        gdp_per_capita REAL, income_group TEXT,
        FOREIGN KEY (region_id) REFERENCES regions(region_id)
    );
    CREATE TABLE disaster_types (
        type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT NOT NULL, subtype_name TEXT NOT NULL DEFAULT 'General',
        disaster_group TEXT NOT NULL DEFAULT 'Natural',
        UNIQUE(type_name, subtype_name)
    );
    CREATE TABLE disasters (
        disaster_id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER NOT NULL, type_id INTEGER NOT NULL,
        year INTEGER NOT NULL CHECK(year >= 1900 AND year <= 2100),
        start_month INTEGER, start_day INTEGER,
        end_year INTEGER, end_month INTEGER, end_day INTEGER,
        location TEXT,
        total_deaths INTEGER DEFAULT 0, total_affected INTEGER DEFAULT 0,
        total_damage_usd REAL DEFAULT 0,
        FOREIGN KEY (country_id) REFERENCES countries(country_id),
        FOREIGN KEY (type_id) REFERENCES disaster_types(type_id)
    );
    CREATE TABLE impact_metrics (
        metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
        disaster_id INTEGER NOT NULL UNIQUE,
        no_injured INTEGER DEFAULT 0, no_affected INTEGER DEFAULT 0,
        no_homeless INTEGER DEFAULT 0,
        FOREIGN KEY (disaster_id) REFERENCES disasters(disaster_id)
    );
    CREATE INDEX idx_disasters_year ON disasters(year);
    CREATE INDEX idx_disasters_country ON disasters(country_id);
    CREATE INDEX idx_disasters_type ON disasters(type_id);
    CREATE INDEX idx_countries_region ON countries(region_id);
    """)

    def safe_int(v):
        if not v or (isinstance(v, str) and not v.strip()): return None
        try: return int(float(str(v).replace(',','')))
        except: return None

    def safe_float(v):
        if not v or (isinstance(v, str) and not v.strip()): return None
        try: return float(str(v).replace(',',''))
        except: return None

    # Load regions -- Author: Prathima Sola
    region_map = {}
    with open(cleaned_csv, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            r, c = row['Region'].strip(), row['Continent'].strip()
            if r and r not in region_map:
                cur.execute("INSERT INTO regions (region_name, continent) VALUES (?,?)", (r, c))
                region_map[r] = cur.lastrowid

    # Load GDP -- Author: Krishna Koushik Thokala
    gdp_data = {}
    if os.path.exists(gdp_csv):
        with open(gdp_csv, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            hi = next((i for i,l in enumerate(lines) if '"Country Name"' in l or l.startswith('Country Name')), None)
            if hi:
                for row in csv.DictReader(lines[hi:]):
                    iso = row.get('Country Code','').strip()
                    for yr in range(2024,1959,-1):
                        v = row.get(str(yr),'').strip()
                        if v:
                            try: gdp_data[iso] = float(v); break
                            except: continue

    # Load income groups -- Author: Prathima Sola
    income_data = {}
    if os.path.exists(meta_csv):
        with open(meta_csv, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                iso, inc = row.get('Country Code','').strip(), row.get('IncomeGroup','').strip()
                if iso and inc: income_data[iso] = inc

    # Load countries -- Author: Krishna Koushik Thokala
    country_map = {}
    with open(cleaned_csv, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            country, iso, region = row['Country'].strip(), row['ISO'].strip(), row['Region'].strip()
            if not country or not iso or not region: continue
            if iso not in country_map:
                rid = region_map.get(region)
                if not rid: continue
                cur.execute("INSERT INTO countries (country_name,iso_code,region_id,gdp_per_capita,income_group) VALUES (?,?,?,?,?)",
                    (country, iso, rid, gdp_data.get(iso), income_data.get(iso)))
                country_map[iso] = cur.lastrowid

    # Load disaster types -- Author: Prathima Sola
    type_map = {}
    with open(cleaned_csv, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            dt, ds = row['Disaster Type'].strip(), row['Disaster Subtype'].strip() or 'General'
            dg = row['Disaster Group'].strip() or 'Natural'
            if dt and (dt,ds) not in type_map:
                cur.execute("INSERT INTO disaster_types (type_name,subtype_name,disaster_group) VALUES (?,?,?)", (dt,ds,dg))
                type_map[(dt,ds)] = cur.lastrowid

    # Load disasters + impact metrics -- Author: Anirudh Sukumaran
    count = 0
    with open(cleaned_csv, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            cid = country_map.get(row['ISO'].strip())
            tid = type_map.get((row['Disaster Type'].strip(), row['Disaster Subtype'].strip() or 'General'))
            yr = safe_int(row['Year'])
            if not cid or not tid or not yr: continue
            cur.execute("""INSERT INTO disasters (country_id,type_id,year,start_month,start_day,
                end_year,end_month,end_day,location,
                total_deaths,total_affected,total_damage_usd) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cid, tid, yr, safe_int(row.get('Start Month')), safe_int(row.get('Start Day')),
                 safe_int(row.get('End Year')), safe_int(row.get('End Month')), safe_int(row.get('End Day')),
                 row.get('Location','').strip() or None,
                 safe_int(row['Total Deaths']) or 0, safe_int(row['Total Affected']) or 0,
                 safe_float(row.get("Total Damages ('000 US$)")) or 0))
            did = cur.lastrowid
            cur.execute("INSERT INTO impact_metrics (disaster_id,no_injured,no_affected,no_homeless) VALUES (?,?,?,?)",
                (did, safe_int(row['No Injured']) or 0, safe_int(row['No Affected']) or 0,
                 safe_int(row['No Homeless']) or 0))
            count += 1

    conn.commit()
    print(f"Database created: {count} disasters, {len(country_map)} countries, {len(region_map)} regions, {len(type_map)} types")
    conn.close()

if __name__ == "__main__":
    init_db()
