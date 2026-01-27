import pandas as pd
import numpy as np
from src.r_bridge import RStatsRunner

# Sample feature table
np.random.seed(0)
df = pd.DataFrame(
    np.random.rand(4, 5),
    index=["gene1", "gene2", "gene3", "gene4"],
    columns=[f"sample{i}" for i in range(5)],
)

runner = RStatsRunner()
cv = runner.compute_cv_matrix(df)

print(cv)

