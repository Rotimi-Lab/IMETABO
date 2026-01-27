import subprocess
from io import StringIO
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


class RStatsRunner:
    def __init__(self, rscript_path: Optional[str] = None):
        """
        Initialize the RStatsRunner.

        Parameters
        ----------
        rscript_path : str, optional
            Path to the Rscript executable (default: 'Rscript')
        """
        self.rscript_path = rscript_path or "Rscript"

    def compute_cv_matrix(self, feature_table: pd.DataFrame) -> pd.DataFrame:
        """
        Compute per-feature coefficient of variation using R.
        """
        r_script = Path(__file__).resolve().parent.parent / "r" / "cv_calc.R"

        if not r_script.exists():
            raise FileNotFoundError(f"R script not found: {r_script}")

        # Convert DataFrame to CSV (in memory)
        buffer = StringIO()
        feature_table.to_csv(buffer)
        csv_input = buffer.getvalue()

        # 🔴 THIS IS THE SUBPROCESS CALL
        process = subprocess.run(
            [self.rscript_path, str(r_script)],
            input=csv_input,
            text=True,
            capture_output=True,
        )

        # If R failed, show the real error
        if process.returncode != 0:
            raise RuntimeError(
                f"R script failed:\nSTDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}"
            )

        # Convert R output back to DataFrame
        return pd.read_csv(StringIO(process.stdout), index_col=0)

    def compute_cv_matrix_python(self, feature_table: pd.DataFrame) -> pd.DataFrame:
        """
        Pure Python fallback implementation.
        Matches R's sd(x) / mean(x) behavior.
        """
        means = feature_table.mean(axis=1, skipna=True)
        stds = feature_table.std(axis=1, skipna=True, ddof=1)

        cv = stds / means
        cv.replace([np.inf, -np.inf], np.nan, inplace=True)

        return pd.DataFrame({"CV": cv})

    def compute_cv_matrix_python(self, feature_table):
        """
        Python fallback for CV computation.
        Same math as R: sd(x) / mean(x)
        """
        import numpy as np
        import pandas as pd

        means = feature_table.mean(axis=1)
        stds = feature_table.std(axis=1, ddof=1)  # same as R

        cv = stds / means
        cv.replace([np.inf, -np.inf], np.nan, inplace=True)

        return pd.DataFrame({"CV": cv})

