import numpy as np
import pandas as pd
from pathlib import Path

from src.r_bridge import RStatsRunner


def test_r_and_python_cv_identical_on_personal_data():
    # Path to your personal dataset
    data_path = Path(__file__).parent / "data" / "DATA2.csv"

    # Load and clean the data
    feature_table = (
        pd.read_csv(data_path, index_col=0)
        .apply(pd.to_numeric, errors="coerce")
        .T
    )

    runner = RStatsRunner()

    # Compute CV using R
    cv_r = runner.compute_cv_matrix(feature_table)

    # Compute CV using Python fallback
    cv_py = runner.compute_cv_matrix_python(feature_table)

    # Compare results numerically
    assert np.allclose(
        cv_r["CV"].values,
        cv_py["CV"].values,
        rtol=1e-6,
        atol=1e-8,
        equal_nan=True,
    )

