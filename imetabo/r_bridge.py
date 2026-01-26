"""
R-Python Bridge for Statistical Computations
=============================================

This module provides a bridge between Python and R for statistical operations
in metabolomics pipelines, with pure Python fallbacks for reproducibility.

Usage
-----
>>> from imetabo.r_bridge import RStatsRunner
>>> import pandas as pd
>>> 
>>> # Your feature table: rows = samples, columns = features
>>> data = pd.DataFrame([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
>>> 
>>> # Compute coefficient of variation using R
>>> runner = RStatsRunner()
>>> cv_results = runner.compute_cv_matrix(data)
>>> 
>>> # Or use pure Python implementation
>>> cv_results_py = runner.compute_cv_matrix_python(data)

Requirements
------------
- R must be installed and `Rscript` must be in PATH
- cv_calc.R must be in the working directory

See Also
--------
- cv_calc.R : R script for CV computation
- tests/test_r_bridge.py : Test suite
"""

import subprocess
from io import StringIO
from typing import Optional

import pandas as pd


class RStatsRunner:
    """
    Runs statistical computations using R via subprocess,
    with a pure Python fallback for reproducibility and testing.

    Designed for metabolomics-style feature tables:
    rows = samples, columns = features.
    """

    def __init__(
        self,
        rscript_path: str = "Rscript",
        r_script_file: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        rscript_path : str
            Path to the Rscript executable.
        r_script_file : str
            Path to the R script that computes CV (default: cv_calc.R).
        """
        self.rscript_path = rscript_path
        self.r_script_file = r_script_file or "cv_calc.R"

    def compute_cv_matrix(self, feature_table: pd.DataFrame) -> pd.DataFrame:
        """
        Compute coefficient of variation (CV = sd / mean) per feature using R.

        Data is passed to R via stdin as CSV and read back from stdout.

        Parameters
        ----------
        feature_table : pd.DataFrame
            Rows = samples, Columns = features

        Returns
        -------
        pd.DataFrame
            Tidy DataFrame with columns:
            - feature
            - cv
        """
        # Include header to send column names to R
        csv_buffer = feature_table.to_csv(index=False, header=True)

        proc = subprocess.run(
            [self.rscript_path, self.r_script_file],
            input=csv_buffer,
            text=True,
            capture_output=True,
            check=True,
        )

        return pd.read_csv(StringIO(proc.stdout))

    @staticmethod
    def compute_cv_matrix_python(feature_table: pd.DataFrame) -> pd.DataFrame:
        """
        Pure Python fallback implementation.

        Mirrors R behavior:
        - numeric features only
        - sample standard deviation (ddof=1)
        - NA ignored
        - CV computed only for non-zero mean features

        Returns
        -------
        pd.DataFrame
            Tidy DataFrame with columns:
            - feature
            - cv
        """
        # Keep numeric features only
        numeric = feature_table.select_dtypes(include="number")

        # Compute means
        means = numeric.mean(axis=0, skipna=True)

        # Exclude zero-mean features (CV undefined)
        valid = means != 0
        numeric = numeric.loc[:, valid]
        means = means[valid]

        stds = numeric.std(axis=0, ddof=1, skipna=True)
        cv = stds / means

        return pd.DataFrame(
            {
                "feature": cv.index,
                "cv": cv.values,
            }
        )
