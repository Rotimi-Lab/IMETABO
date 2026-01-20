import pandas as pd
import numpy as np
from pathlib import Path

from imetabo.r_bridge import RStatsRunner


def test_r_and_python_cv_match():
    # Path to Test_Data.csv in tests/
    csv_path = Path(__file__).parent / "Test_Data.csv"

    # Explicitly read with no header, pandas will create columns 0, 1, 2, ...
    df = pd.read_csv(csv_path, header=None)
    df = df.select_dtypes(include="number")

    runner = RStatsRunner()

    r_result = (
        runner.compute_cv_matrix(df)
        .sort_values("feature")
        .reset_index(drop=True)
    )

    py_result = (
        runner.compute_cv_matrix_python(df)
        .sort_values("feature")
        .reset_index(drop=True)
    )

    # Debug: Show which features are mismatched
    diff = pd.DataFrame({
        'feature': r_result['feature'],
        'r_cv': r_result['cv'],
        'py_cv': py_result['cv'],
        'abs_diff': abs(r_result['cv'] - py_result['cv']),
        'rel_diff': abs(r_result['cv'] - py_result['cv']) / r_result['cv']
    })
    
    # Show only mismatched rows
    mismatched = diff[diff['abs_diff'] > 1e-8]
    print("\n=== Mismatched features ===")
    print(mismatched.to_string())
    
    # Show sample statistics for one mismatched feature
    if len(mismatched) > 0:
        bad_feature = mismatched.iloc[0]['feature']
        print(f"\n=== Statistics for feature: {bad_feature} ===")
        values = df[int(bad_feature)].dropna()  # Convert feature name to int
        print(f"Count: {len(values)}")
        print(f"Mean: {values.mean()}")
        print(f"Std (ddof=0): {values.std(ddof=0)}")
        print(f"Std (ddof=1): {values.std(ddof=1)}")
        print(f"CV (Python): {values.std(ddof=1) / values.mean()}")

    np.testing.assert_allclose(
        r_result["cv"].values,
        py_result["cv"].values,
        rtol=1e-6,
        atol=1e-8,
    )
