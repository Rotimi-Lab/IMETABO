"""
run_real_data.py
=================
WHY THIS SCRIPT EXISTS:
This script takes ALL the real metabolite names from our uploaded
CSV file and runs them through the classification engine against
our local database of 796,163 compounds.

Run with:
    python run_real_data.py
"""

import sys, os
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))

from metabolite_classifier.engine import MetaboliteClassifier

# ---------------------------------------------------------------------------
# Step 1 — Load the real metabolite names from the CSV
# ---------------------------------------------------------------------------
print("Reading metabolite names from CSV...")
df = pd.read_csv('data/metabolites.csv', low_memory=False)

# Keep only rows with real names (skip "unknown")
real_names = df[df['Title'] != 'unknown']['Title'].tolist()
print(f"Found {len(real_names):,} real metabolite names to classify")

# ---------------------------------------------------------------------------
# Step 2 — Run the classifier against the real database
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("  Running Classifier on Real Metabolite Database")
print(f"  Database: 796,163 real compounds from PubChem")
print("=" * 60)

clf = MetaboliteClassifier(
    db_path="data/metabolites.db",
    fuzzy_threshold=80,
    enable_api=False,
)

print(f"\nClassifying {len(real_names):,} metabolite names...")
print("This may take a few minutes...\n")

results = clf.classify(real_names)

# ---------------------------------------------------------------------------
# Step 3 — Show summary
# ---------------------------------------------------------------------------
print()
clf.summary()

# ---------------------------------------------------------------------------
# Step 4 — Save results
# ---------------------------------------------------------------------------
results.to_csv("data/real_results.csv", index=False)
print(f"\n✓ Results saved to data/real_results.csv")
print(f"  Open data/real_results.csv in VS Code to see all results")