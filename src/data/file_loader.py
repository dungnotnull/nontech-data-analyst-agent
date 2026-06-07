from pathlib import Path
from typing import Any, Optional
import chardet
import pandas as pd
import numpy as np
import io


class FileLoader:
    SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".tsv", ".txt", ".ods"}
    MAX_PREVIEW_ROWS = 1000
    CHUNK_SIZE = 50000

    def __init__(self):
        self._encoding_cache: dict[str, str] = {}

    def load(
        self,
        file_path: str,
        sheet_name: str | int | None = None,
        max_rows: int | None = None,
        sample_only: bool = False,
    ) -> dict[str, pd.DataFrame]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {ext}. Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        if ext in (".xlsx", ".xls", ".ods"):
            return self._load_excel(path, sheet_name, max_rows, sample_only)
        elif ext in (".csv", ".tsv", ".txt"):
            sep = "\t" if ext == ".tsv" else ","
            return {"data": self._load_delimited(path, sep, max_rows, sample_only)}

        return {}

    def list_sheets(self, file_path: str) -> list[str]:
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext in (".xlsx", ".xls", ".ods"):
            if ext == ".ods":
                engine = "odf"
            else:
                engine = "openpyxl" if ext == ".xlsx" else "xlrd"
            xls = pd.ExcelFile(path, engine=engine)
            return xls.sheet_names
        return ["data"]

    def preview(self, file_path: str, sheet_name: str | int = 0, rows: int = 20) -> dict[str, Any]:
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext in (".xlsx", ".xls", ".ods"):
            engine = "openpyxl" if ext in (".xlsx", ".xls") else "odf"
            df = pd.read_excel(path, sheet_name=sheet_name, nrows=rows, engine=engine)
        else:
            sep = "\t" if ext == ".tsv" else ","
            encoding = self._detect_encoding(path)
            df = pd.read_csv(path, sep=sep, encoding=encoding, nrows=rows)

        df = self._unmerge_cells(df)
        return {
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "preview": df.head(rows).to_dict(orient="records"),
            "shape": df.shape,
        }

    def _load_excel(
        self,
        path: Path,
        sheet_name: str | int | None = None,
        max_rows: int | None = None,
        sample_only: bool = False,
    ) -> dict[str, pd.DataFrame]:
        engine = "openpyxl" if path.suffix in (".xlsx", ".xls") else "odf"
        if path.suffix == ".xls":
            engine = "xlrd"

        xls = pd.ExcelFile(path, engine=engine)
        sheets_to_load = [sheet_name] if sheet_name is not None else xls.sheet_names

        dfs = {}
        for sname in sheets_to_load:
            nrows = None
            if sample_only:
                nrows = self.MAX_PREVIEW_ROWS
            elif max_rows:
                nrows = max_rows

            df = pd.read_excel(xls, sheet_name=sname, nrows=nrows)
            if len(df) > 0:
                df = self._unmerge_cells(df)
                df = self._detect_and_convert_numeric(df)
                df = self._detect_and_parse_dates(df)
            dfs[str(sname)] = df

        return dfs

    def _load_delimited(
        self,
        path: Path,
        sep: str,
        max_rows: int | None = None,
        sample_only: bool = False,
    ) -> pd.DataFrame:
        encoding = self._detect_encoding(path)
        nrows = self.MAX_PREVIEW_ROWS if sample_only else max_rows

        try:
            df = pd.read_csv(path, sep=sep, encoding=encoding, nrows=nrows, on_bad_lines="warn")
        except Exception:
            df = pd.read_csv(
                path, sep=None, engine="python", encoding=encoding,
                nrows=nrows, on_bad_lines="skip",
            )

        if len(df) > 0:
            df = self._unmerge_cells(df)
            df = self._detect_and_convert_numeric(df)
            df = self._detect_and_parse_dates(df)

        return df

    def _detect_encoding(self, path: Path) -> str:
        cache_key = str(path)
        if cache_key in self._encoding_cache:
            return self._encoding_cache[cache_key]

        with open(path, "rb") as f:
            raw_data = f.read(50000)
        result = chardet.detect(raw_data)
        encoding = result.get("encoding", "utf-8")
        if encoding and encoding.lower() in ("ascii", "utf-8", "utf-16", "latin-1", "cp1252", "cp1258"):
            pass
        else:
            encoding = "utf-8"

        self._encoding_cache[cache_key] = encoding
        return encoding

    def _unmerge_cells(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.ffill()

    def _detect_and_convert_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if df[col].dtype != "object":
                continue
            col_str = df[col].astype(str).str.replace(r"[^\d.,\-]", "", regex=True)
            col_str = col_str.str.replace(r"\.(?=\d{3})", "", regex=True)
            col_str = col_str.str.replace(",", ".")
            converted = pd.to_numeric(col_str, errors="coerce")
            valid_ratio = converted.notna().sum() / max(len(df), 1)
            if valid_ratio > 0.8:
                df[col] = converted
        return df

    def _detect_and_parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        from dateparser import parse as dp_parse

        for col in df.columns:
            if df[col].dtype != "object":
                continue
            sample = df[col].dropna().head(5)
            parsed_count = 0
            for val in sample:
                parsed = dp_parse(str(val), languages=["vi", "en"])
                if parsed is not None:
                    parsed_count += 1
            if parsed_count >= len(sample) * 0.6:
                df[col] = df[col].apply(
                    lambda x: dp_parse(str(x), languages=["vi", "en"]) if pd.notna(x) else pd.NaT
                )
        return df

    def load_chunked(self, file_path: str, chunk_size: int | None = None):
        path = Path(file_path)
        ext = path.suffix.lower()
        chunk_size = chunk_size or self.CHUNK_SIZE

        if ext in (".csv", ".tsv"):
            sep = "\t" if ext == ".tsv" else ","
            encoding = self._detect_encoding(path)
            for chunk in pd.read_csv(path, sep=sep, encoding=encoding, chunksize=chunk_size):
                yield {"data": chunk}
        elif ext in (".xlsx", ".xls"):
            dfs = self._load_excel(path, sample_only=False)
            for sheet_name, df in dfs.items():
                for start in range(0, len(df), chunk_size):
                    chunk = df.iloc[start : start + chunk_size]
                    yield {sheet_name: chunk}
        else:
            yield self.load(file_path)
