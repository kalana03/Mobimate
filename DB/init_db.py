import sqlite3

def init_db():
    conn = sqlite3.connect("mobimate.db")
    cursor = conn.cursor()

    # 1. Packages Table (Core quantitative metrics)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        package_id INTEGER PRIMARY KEY AUTOINCREMENT,
        carrier TEXT NOT NULL,
        package_name TEXT NOT NULL,
        price REAL NOT NULL,
        validity_days INTEGER NOT NULL,
        fup_gb INTEGER DEFAULT 0,
        is_fup_per_day BOOLEAN DEFAULT 0,
        anytime_data_gb INTEGER DEFAULT 0,
        voice_mins INTEGER DEFAULT 0,
        sms_count INTEGER DEFAULT 0,
        is_data_rollover BOOLEAN DEFAULT 0,
        is_active INTEGER DEFAULT 1
    );
    """)

    # 2. Master Apps Lookup Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apps (
        app_id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_name TEXT UNIQUE NOT NULL,
        app_icon_url TEXT
    );
    """)

    # 3. Package <-> Apps Junction Table (Many-to-Many)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS package_apps (
        package_id INTEGER,
        app_id INTEGER,
        FOREIGN KEY (package_id) REFERENCES packages(package_id),
        FOREIGN KEY (app_id) REFERENCES apps(app_id),
        PRIMARY KEY (package_id, app_id)
    );
    """)

    conn.commit()
    conn.close()
    print("✅ Database 'mobimate.db' initialized successfully!")

if __name__ == "__main__":
    init_db()