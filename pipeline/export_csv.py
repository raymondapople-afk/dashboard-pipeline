"""Write the standard-schema, line-item-grain CSV that Looker Studio reads."""
from pathlib import Path

import pandas as pd


def write_clean_csv(df: pd.DataFrame, out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
