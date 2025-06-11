import pandas as pd
import sqlite3
from datetime import datetime

def connect_to_sqlite(db_name='data/processed/bank_reviews.db'):
    """ Connect to SQLite database """
    try:
        conn = sqlite3.connect(db_name)
        print(f"Connected to SQLite database at {db_name}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite: {e}")
        return None


def create_tables(conn):
    """ Create tables if they don't exist """
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS banks (
        bank_id INTEGER PRIMARY KEY AUTOINCREMENT,
        bank_name TEXT UNIQUE NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        bank_id INTEGER,
        review_text TEXT,
        rating INTEGER,
        review_date DATE,
        source TEXT,
        FOREIGN KEY(bank_id) REFERENCES banks(bank_id)
    )
    """)
    
    conn.commit()
    cursor.close()
    print("✅ Tables created or already exist")


def load_data(input_file):
    """ Load and validate dataset """
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} reviews from {input_file}")
        return df
    except FileNotFoundError:
        print(f"❌ Error: {input_file} not found")
        return None


def insert_banks(conn, df):
    """ Insert unique banks and return mapping of bank name to ID """
    cursor = conn.cursor()
    banks = df[['bank']].drop_duplicates().reset_index(drop=True)
    bank_ids = {}

    for _, row in banks.iterrows():
        bank_name = row['bank']
        cursor.execute("SELECT bank_id FROM banks WHERE bank_name=?", [bank_name])
        result = cursor.fetchone()

        if result:
            bank_id = result[0]
        else:
            cursor.execute("INSERT INTO banks (bank_name) VALUES (?)", [bank_name])
            bank_id = cursor.lastrowid
        
        bank_ids[bank_name] = bank_id

    conn.commit()
    cursor.close()
    print(f"✅ Inserted {len(bank_ids)} banks")
    return bank_ids


def insert_reviews(conn, df, bank_ids):
    """ Insert reviews into SQLite """
    cursor = conn.cursor()
    count = 0
    
    for _, row in df.iterrows():
        try:
            # Clean date format
            review_date = None
            if pd.notna(row['date']):
                try:
                    review_date = pd.to_datetime(row['date']).date()
                except Exception:
                    pass

            bank_id = bank_ids[row['bank']]
            review_text = row['review'][:4000] if pd.notna(row['review']) else None
            rating = row['rating'] if pd.notna(row['rating']) else None
            source = row['source'][:100] if pd.notna(row['source']) else None

            cursor.execute("""
                INSERT INTO reviews (bank_id, review_text, rating, review_date, source)
                VALUES (?, ?, ?, ?, ?)
            """, [bank_id, review_text, rating, review_date, source])

            count += 1
            if count % 100 == 0:
                conn.commit()
        except sqlite3.Error as e:
            print(f"⚠️ Error inserting review: {e}")

    conn.commit()
    cursor.close()
    print(f"✅ Total reviews inserted: {count}")
    return count


def verify_data(conn):
    """ Check if data was successfully inserted """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reviews")
    review_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM banks")
    bank_count = cursor.fetchone()[0]
    cursor.close()

    print(f"📊 Total banks in database: {bank_count}")
    print(f"📊 Total reviews in database: {review_count}")
    
    return review_count > 1000  # KPI check


def main():
    input_file = 'data/processed/bank_app_reviews_processed.csv'
    
    # Step 1: Connect to SQLite
    conn = connect_to_sqlite()
    if conn is None:
        return

    # Step 2: Create tables
    create_tables(conn)

    # Step 3: Load processed CSV
    df = load_data(input_file)
    if df is None:
        conn.close()
        return

    # Step 4: Insert banks and get IDs
    bank_ids = insert_banks(conn, df)

    # Step 5: Insert reviews
    total_reviews = insert_reviews(conn, df, bank_ids)

    # Step 6: Verify results
    if verify_data(conn):
        print("✅ KPI met: More than 1,000 reviews inserted")
    else:
        print("⚠️ KPI not met: Less than 1,000 reviews inserted")

    # Final step: Close connection
    conn.close()



if __name__ == "__main__":
    main()