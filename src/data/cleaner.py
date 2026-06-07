import re
from typing import Any, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler


class DataCleaner:
    def __init__(self, strategy: str = "auto"):
        self.strategy = strategy
        self._operations_log: list[str] = []

    def clean(self, df: pd.DataFrame, remove_duplicates: bool = True) -> pd.DataFrame:
        self._operations_log = []
        df = df.copy()
        df = self._rename_unnamed_columns(df)
        df = self._handle_whitespace_columns(df)
        df = self._normalize_column_names(df)
        df = self._strip_strings(df)
        if remove_duplicates:
            before = len(df)
            df = df.drop_duplicates()
            removed = before - len(df)
            if removed > 0:
                self._operations_log.append(f"Removed {removed} duplicate rows")
        df = df.reset_index(drop=True)
        return df

    def handle_missing_values(
        self,
        df: pd.DataFrame,
        numeric_strategy: str = "median",
        categorical_strategy: str = "mode",
        drop_threshold: float = 0.5,
    ) -> pd.DataFrame:
        df = df.copy()

        cols_to_drop = []
        for col in df.columns:
            missing_pct = df[col].isnull().mean()
            if missing_pct >= drop_threshold:
                cols_to_drop.append(col)
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            self._operations_log.append(
                f"Dropped columns with >= {drop_threshold*100:.0f}% missing: {cols_to_drop}"
            )

        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count == 0:
                continue

            if pd.api.types.is_numeric_dtype(df[col]):
                if numeric_strategy == "median":
                    fill_val = df[col].median()
                elif numeric_strategy == "mean":
                    fill_val = df[col].mean()
                elif numeric_strategy == "zero":
                    fill_val = 0
                elif numeric_strategy == "interpolate":
                    df[col] = df[col].interpolate(method="linear").fillna(method="bfill").fillna(method="ffill")
                    self._operations_log.append(f"Interpolated {null_count} missing values in '{col}'")
                    continue
                else:
                    fill_val = df[col].median()
                df[col] = df[col].fillna(fill_val)
                self._operations_log.append(
                    f"Filled {null_count} missing values in '{col}' with {numeric_strategy}"
                )
            else:
                if categorical_strategy == "mode":
                    mode_vals = df[col].mode()
                    fill_val = mode_vals[0] if len(mode_vals) > 0 else "Unknown"
                elif categorical_strategy == "unknown":
                    fill_val = "Unknown"
                elif categorical_strategy == "forward_fill":
                    df[col] = df[col].ffill().bfill()
                    self._operations_log.append(
                        f"Forward-filled {null_count} missing values in '{col}'"
                    )
                    continue
                else:
                    fill_val = "Unknown"
                df[col] = df[col].fillna(fill_val)
                self._operations_log.append(
                    f"Filled {null_count} missing values in '{col}' with '{fill_val}'"
                )

        return df

    def normalize_numeric(
        self, df: pd.DataFrame, columns: list[str] | None = None, method: str = "standard"
    ) -> pd.DataFrame:
        df = df.copy()
        if columns is None:
            columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

        valid_cols = [c for c in columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
        if not valid_cols:
            return df

        scaler = StandardScaler() if method == "standard" else MinMaxScaler()
        df[valid_cols] = scaler.fit_transform(df[valid_cols])
        self._operations_log.append(f"Normalized columns: {valid_cols} using {method} scaling")
        return df

    def remove_outliers(
        self, df: pd.DataFrame, columns: list[str] | None = None, method: str = "iqr", threshold: float = 1.5
    ) -> pd.DataFrame:
        df = df.copy()
        if columns is None:
            columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        valid_cols = [c for c in columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
        if not valid_cols:
            return df

        before = len(df)
        for col in valid_cols:
            if method == "iqr":
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - threshold * iqr
                upper = q3 + threshold * iqr
                df = df[(df[col] >= lower) & (df[col] <= upper)]
            elif method == "zscore":
                from scipy import stats
                z = np.abs(stats.zscore(df[col].dropna()))
                if len(z) > 0:
                    df = df[z < threshold]

        removed = before - len(df)
        if removed > 0:
            self._operations_log.append(f"Removed {removed} outlier rows using {method}")
        return df

    def parse_vn_currency_columns(self, df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        df = df.copy()
        if columns is None:
            columns = list(df.columns)

        for col in columns:
            if col in df.columns and df[col].dtype == "object":
                try:
                    cleaned = df[col].astype(str).str.replace(r"[^\d.\-,]", "", regex=True)
                    cleaned = cleaned.str.replace(r"\.(?=\d{3})", "", regex=True)
                    cleaned = cleaned.str.replace(",", ".")
                    numeric = pd.to_numeric(cleaned, errors="coerce")
                    valid_ratio = numeric.notna().sum() / max(len(df), 1)
                    if valid_ratio > 0.6:
                        df[col] = numeric
                        self._operations_log.append(f"Parsed currency column: {col}")
                except Exception:
                    continue
        return df

    def parse_date_columns(
        self, df: pd.DataFrame, columns: list[str] | None = None, fmt: str | None = None
    ) -> pd.DataFrame:
        from dateparser import parse as dp_parse

        df = df.copy()
        if columns is None:
            columns = [c for c in df.columns if df[c].dtype == "object"]

        for col in columns:
            if col not in df.columns or pd.api.types.is_datetime64_any_dtype(df[col]):
                continue
            try:
                parsed = df[col].apply(
                    lambda x: dp_parse(str(x), languages=["vi", "en"]) if pd.notna(x) else pd.NaT
                )
                success_rate = parsed.notna().sum() / max(len(df), 1)
                if success_rate > 0.5:
                    df[col] = parsed
                    self._operations_log.append(f"Parsed date column: {col}")
            except Exception:
                continue
        return df

    def get_operation_log(self) -> list[str]:
        return self._operations_log

    def _rename_unnamed_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        new_cols = []
        for i, col in enumerate(df.columns):
            col_str = str(col)
            if col_str.startswith("Unnamed:") or col_str.strip() == "":
                new_cols.append(f"column_{i}")
            else:
                new_cols.append(col_str)
        df.columns = new_cols
        return df

    def _handle_whitespace_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [str(col).strip() for col in df.columns]
        return df

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {}
        seen: set[str] = set()
        for col in df.columns:
            normalized = col.lower().strip()
            normalized = re.sub(r"[\s\-]+", "_", normalized)
            normalized = re.sub(r"[^\w]", "_", normalized)
            normalized = re.sub(r"_+", "_", normalized).strip("_")
            if not normalized:
                normalized = f"col_{len(seen)}"
            base = normalized
            counter = 1
            while normalized in seen:
                normalized = f"{base}_{counter}"
                counter += 1
            seen.add(normalized)
            if normalized != col:
                rename_map[col] = normalized
        return df.rename(columns=rename_map)

    def _strip_strings(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.strip()
        return df
