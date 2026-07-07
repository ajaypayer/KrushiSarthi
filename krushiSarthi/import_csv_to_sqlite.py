import os
import csv
import sqlite3

def import_csvs():
    db_path = 'db.sqlite3'
    app_dir = 'krushiApp'
    data_dir = os.path.join(app_dir, 'data')

    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Import Government Schemes
    gov_csv = os.path.join(data_dir, 'government_schemes.csv')
    if os.path.exists(gov_csv):
        print(f"Importing {gov_csv}...")
        cursor.execute("DROP TABLE IF EXISTS csv_government_schemes;")
        cursor.execute("""
            CREATE TABLE csv_government_schemes (
                id INTEGER PRIMARY KEY,
                scheme_name TEXT,
                category TEXT,
                eligibility TEXT,
                benefits TEXT,
                documents_required TEXT,
                official_website TEXT
            );
        """)
        with open(gov_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute("""
                    INSERT INTO csv_government_schemes 
                    (id, scheme_name, category, eligibility, benefits, documents_required, official_website)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    int(row['id']),
                    row['scheme_name'],
                    row['category'],
                    row['eligibility'],
                    row['benefits'],
                    row['documents_required'],
                    row['official_website']
                ))
        print("Government schemes imported successfully.")

    # 2. Import MSP Rates
    msp_csv = os.path.join(data_dir, 'msp_rates.csv')
    if os.path.exists(msp_csv):
        print(f"Importing {msp_csv}...")
        cursor.execute("DROP TABLE IF EXISTS csv_msp_rates;")
        cursor.execute("""
            CREATE TABLE csv_msp_rates (
                id INTEGER PRIMARY KEY,
                crop TEXT,
                variety TEXT,
                season TEXT,
                marketing_year TEXT,
                msp_rupees_per_quintal REAL,
                unit TEXT
            );
        """)
        with open(msp_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute("""
                    INSERT INTO csv_msp_rates 
                    (id, crop, variety, season, marketing_year, msp_rupees_per_quintal, unit)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    int(row['id']),
                    row['crop'],
                    row['variety'],
                    row['season'],
                    row['marketing_year'],
                    float(row['msp_rupees_per_quintal']) if row['msp_rupees_per_quintal'] else None,
                    row['unit']
                ))
        print("MSP rates imported successfully.")

    # 3. Import Agriculture Loans
    loans_csv = os.path.join(data_dir, 'agriculture_loans.csv')
    if os.path.exists(loans_csv):
        print(f"Importing {loans_csv}...")
        cursor.execute("DROP TABLE IF EXISTS csv_agriculture_loans;")
        cursor.execute("""
            CREATE TABLE csv_agriculture_loans (
                id INTEGER PRIMARY KEY,
                loan_name TEXT,
                category TEXT,
                eligibility TEXT,
                purpose TEXT,
                documents_required TEXT,
                repayment_period TEXT,
                official_source TEXT
            );
        """)
        with open(loans_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute("""
                    INSERT INTO csv_agriculture_loans 
                    (id, loan_name, category, eligibility, purpose, documents_required, repayment_period, official_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    int(row['id']),
                    row['loan_name'],
                    row['category'],
                    row['eligibility'],
                    row['purpose'],
                    row['documents_required'],
                    row['repayment_period'],
                    row['official_source']
                ))
        print("Agriculture loans imported successfully.")

    # 4. Import Agriculture Q&A
    qa_csv = os.path.join(data_dir, 'agriculture_qa.csv')
    if os.path.exists(qa_csv):
        print(f"Importing {qa_csv} (this may take a few seconds)...")
        
        # Try to use FTS5 virtual table for faster searching
        use_fts5 = True
        cursor.execute("DROP TABLE IF EXISTS csv_agriculture_qa;")
        try:
            cursor.execute("CREATE VIRTUAL TABLE csv_agriculture_qa USING fts5(question, answers);")
            print("Using SQLite FTS5 Virtual Table for Q&A.")
        except sqlite3.OperationalError:
            use_fts5 = False
            cursor.execute("""
                CREATE TABLE csv_agriculture_qa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    answers TEXT
                );
            """)
            print("FTS5 not supported. Using standard table for Q&A.")

        with open(qa_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Batch inserts for speed
            batch = []
            if use_fts5:
                insert_query = "INSERT INTO csv_agriculture_qa (question, answers) VALUES (?, ?);"
            else:
                insert_query = "INSERT INTO csv_agriculture_qa (question, answers) VALUES (?, ?);"

            for row in reader:
                batch.append((row['question'], row['answers']))
                if len(batch) >= 1000:
                    cursor.executemany(insert_query, batch)
                    batch = []
            if batch:
                cursor.executemany(insert_query, batch)

        if not use_fts5:
            # Create standard index on question column if not FTS5
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_question ON csv_agriculture_qa(question);")
        
        print("Agriculture Q&A imported successfully.")

    conn.commit()
    conn.close()
    print("All CSV datasets imported successfully!")

if __name__ == '__main__':
    import_csvs()
