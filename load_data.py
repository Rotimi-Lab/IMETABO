"""
load_data.py
=============
WHY THIS SCRIPT EXISTS:
Our engine needs a local database to match against. This script reads
the real metabolite data from the CSV file and loads it into our
SQLite database so the classifier can work with real research data.

Run with:
    python load_data.py
"""

import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from metabolite_classifier.engine import DatabaseManager, Sanitizer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CSV_PATH = "data/metabolites.csv"
DB_PATH = "data/metabolites.db"
BATCH_SIZE = 1000  # process 1000 rows at a time

# ---------------------------------------------------------------------------
# Load the CSV
# ---------------------------------------------------------------------------
print("Reading CSV file...")
df = pd.read_csv(CSV_PATH, low_memory=False)
print(f"Total rows: {len(df)}")

# Keep only rows with real names
df = df[df['Title'] != 'unknown'].copy()
print(f"Rows with real names: {len(df)}")

# ---------------------------------------------------------------------------
# Connect to database
# ---------------------------------------------------------------------------
print(f"\nInitialising database at {DB_PATH}...")
db = DatabaseManager(DB_PATH)
db.connect()

# ---------------------------------------------------------------------------
# Load metabolites into database
# ---------------------------------------------------------------------------
print("Loading metabolites into database...")
print("This may take a few minutes for 796,000 records...\n")

loaded = 0
skipped = 0

for i, row in df.iterrows():
    name = str(row['Title']).strip()
    
    if not name or name == 'unknown' or name == 'nan':
        skipped += 1
        continue

    # Get optional fields safely
    cid = str(row.get('CID', '')) if str(row.get('CID', '')) != 'unknown' else None
    formula = str(row.get('MolecularFormula', ''))
    
    # We don't have category info in this dataset
    # so we'll mark everything as "unknown" for now
    # — the engine will still match names correctly
    category = "unknown"

    try:
        db.insert_metabolite(
            canonical_name=name,
            primary_category=category,
            pubchem_cid=cid,
            synonyms=[name],
        )
        loaded += 1
    except Exception as e:
        skipped += 1

    # Show progress every 10,000 records
    if loaded % 10000 == 0 and loaded > 0:
        print(f"  Loaded {loaded:,} metabolites so far...")

db.close()

print(f"\n✓ Done!")
print(f"  Loaded:  {loaded:,} metabolites")
print(f"  Skipped: {skipped:,} rows")
print(f"  Database saved to: {DB_PATH}")
print(f"\nYou can now run the classifier using:")
print(f"  clf = MetaboliteClassifier(db_path='data/metabolites.db')")