from __future__ import annotations
from pathlib import Path
import pandas as pd


def profile_excel(path: str | Path, max_sheets: int = 20, max_rows: int = 18, max_cols: int = 16) -> dict:
    """Profile an official workbook without interpreting its semantics.

    The profile is intentionally small and text-only so a parser can be designed
    against the real workbook structure. No missing cell is converted to zero.
    """
    path = Path(path)
    xls = pd.ExcelFile(path)
    sheets = []
    for sheet in xls.sheet_names[:max_sheets]:
        df = pd.read_excel(path, sheet_name=sheet, header=None, nrows=max_rows)
        sample = []
        for row in df.iloc[:, :max_cols].itertuples(index=False, name=None):
            sample.append([None if pd.isna(v) else str(v) for v in row])
        sheets.append({
            "sheet_name": str(sheet),
            "sample_rows": sample,
            "sample_row_count": len(sample),
            "sample_col_count": min(len(df.columns), max_cols),
        })
    return {
        "workbook": path.name,
        "sheet_count": len(xls.sheet_names),
        "sheet_names": [str(x) for x in xls.sheet_names],
        "profiled_sheets": sheets,
        "profile_semantics": "STRUCTURE_ONLY_NOT_DATA_INTERPRETATION",
    }
