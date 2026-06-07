import re
from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from dateparser import parse as dp_parse


class SchemaDetector:
    VN_DATE_PATTERNS = [
        re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$"),
        re.compile(r"^\d{1,2}-\d{1,2}-\d{4}$"),
        re.compile(r"^\d{1,2}\.\d{1,2}\.\d{4}$"),
        re.compile(r"^\d{4}/\d{1,2}/\d{1,2}$"),
        re.compile(r"^\d{4}-\d{1,2}-\d{1,2}$"),
        re.compile(r"^tháng\s+\d{1,2}\s+năm\s+\d{4}$", re.IGNORECASE),
        re.compile(r"^ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}$", re.IGNORECASE),
        re.compile(r"^[tT]\d{1,2}/\d{4}$"),
    ]

    CURRENCY_SYMBOLS = {
        "₫": "VND", "đ": "VND", "VND": "VND", "VNĐ": "VND",
        "$": "USD", "USD": "USD", "€": "EUR", "EUR": "EUR",
    }

    CURRENCY_PATTERNS = [
        re.compile(r"([\d,]+(?:\.\d+)?)\s*[₫đ]", re.IGNORECASE),
        re.compile(r"[₫đ]\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE),
        re.compile(r"([\d,]+(?:\.\d+)?)\s*VND", re.IGNORECASE),
        re.compile(r"\$\s*([\d,]+(?:\.\d+)?)"),
        re.compile(r"([\d,]+(?:\.\d+)?)\s*\€"),
    ]

    PERCENTAGE_PATTERNS = [
        re.compile(r"^[\d,]+(?:\.\d+)?\s*%$"),
        re.compile(r"^-?[\d,]+(?:\.\d+)?\s*%$"),
        re.compile(r"^\d+(?:\.\d+)?\s*percent$", re.IGNORECASE),
    ]

    def __init__(self):
        self.vn_timezone = ZoneInfo("Asia/Ho_Chi_Minh")

    def detect(self, df: pd.DataFrame) -> dict[str, Any]:
        if df.empty:
            return {
                "columns": [],
                "row_count": 0,
                "column_types": {},
                "missing_values": {},
                "suggested_roles": {},
                "statistics": {},
            }

        column_types = {}
        column_roles = {}
        statistics = {}
        missing_values = {}

        for col in df.columns:
            col_type, meta = self._detect_column_type(df[col])
            column_types[col] = col_type
            if meta:
                statistics[col] = meta
            missing_values[col] = int(df[col].isnull().sum())

        numeric_cols = [c for c, t in column_types.items() if t in ("numeric", "currency", "percentage")]
        datetime_cols = [c for c, t in column_types.items() if t == "datetime"]
        categorical_cols = [c for c, t in column_types.items() if t == "categorical"]
        text_cols = [c for c, t in column_types.items() if t == "text"]

        for col in df.columns:
            column_roles[col] = self._suggest_role(
                col, column_types[col], df[col], numeric_cols, datetime_cols, categorical_cols
            )

        return {
            "columns": list(df.columns),
            "row_count": len(df),
            "column_types": column_types,
            "missing_values": missing_values,
            "suggested_roles": column_roles,
            "statistics": statistics,
            "numeric_columns": numeric_cols,
            "datetime_columns": datetime_cols,
            "categorical_columns": categorical_cols,
        }

    def _detect_column_type(self, series: pd.Series) -> tuple[str, dict[str, Any] | None]:
        series_clean = series.dropna()
        if len(series_clean) == 0:
            return "empty", None

        if pd.api.types.is_datetime64_any_dtype(series_clean):
            meta = {
                "min": str(series_clean.min()),
                "max": str(series_clean.max()),
                "span_days": (series_clean.max() - series_clean.min()).days,
            }
            return "datetime", meta

        if pd.api.types.is_bool_dtype(series_clean):
            return "boolean", None

        if pd.api.types.is_numeric_dtype(series_clean):
            meta = {
                "min": float(series_clean.min()),
                "max": float(series_clean.max()),
                "mean": float(series_clean.mean()),
                "median": float(series_clean.median()),
                "std": float(series_clean.std()),
            }
            return "numeric", meta

        sample_values = series_clean.head(20).tolist()

        if self._looks_like_date(sample_values):
            parsed_dates = []
            for v in sample_values:
                parsed = dp_parse(str(v), languages=["vi", "en"])
                parsed_dates.append(parsed)
            valid_dates = [d for d in parsed_dates if d is not None]
            if len(valid_dates) >= len(sample_values) * 0.7:
                valid_dates_dt = pd.to_datetime(valid_dates)
                meta = {
                    "min": str(min(valid_dates_dt)),
                    "max": str(max(valid_dates_dt)),
                    "span_days": (max(valid_dates_dt) - min(valid_dates_dt)).days,
                }
                return "datetime", meta

        if self._looks_like_currency(sample_values):
            cleaned = series_clean.astype(str).str.replace(r"[^\d.\-]", "", regex=True)
            numeric = pd.to_numeric(cleaned, errors="coerce")
            numeric = numeric.dropna()
            if len(numeric) >= len(series_clean) * 0.5:
                meta = {
                    "min": float(numeric.min()),
                    "max": float(numeric.max()),
                    "mean": float(numeric.mean()),
                    "median": float(numeric.median()),
                    "currency": self._guess_currency(sample_values),
                }
                return "currency", meta

        if self._looks_like_percentage(sample_values):
            cleaned = series_clean.astype(str).str.replace(r"[%\s]", "", regex=True)
            cleaned = cleaned.str.replace(",", ".")
            numeric = pd.to_numeric(cleaned, errors="coerce").dropna()
            if len(numeric) >= len(series_clean) * 0.5:
                meta = {
                    "min": float(numeric.min()),
                    "max": float(numeric.max()),
                    "mean": float(numeric.mean()),
                }
                return "percentage", meta

        unique_count = series_clean.nunique()
        unique_ratio = unique_count / len(series_clean)

        if unique_ratio < 0.1 and len(series_clean) > 10:
            return "categorical", {"unique_values": unique_count, "top_values": series_clean.value_counts().head(10).to_dict()}

        return "text", None

    def _looks_like_date(self, sample: list) -> bool:
        matches = 0
        for val in sample:
            val_str = str(val).strip()
            for pattern in self.VN_DATE_PATTERNS:
                if pattern.search(val_str):
                    matches += 1
                    break
        return matches >= len(sample) * 0.6

    def _looks_like_currency(self, sample: list) -> bool:
        matches = 0
        for val in sample:
            val_str = str(val).strip()
            for pattern in self.CURRENCY_PATTERNS:
                if pattern.search(val_str):
                    matches += 1
                    break
        return matches >= len(sample) * 0.4

    def _looks_like_percentage(self, sample: list) -> bool:
        matches = 0
        for val in sample:
            val_str = str(val).strip()
            for pattern in self.PERCENTAGE_PATTERNS:
                if pattern.search(val_str):
                    matches += 1
                    break
        return matches >= len(sample) * 0.5

    def _guess_currency(self, sample: list) -> str:
        for val in sample:
            val_str = str(val).strip()
            if "₫" in val_str or "đ" in val_str or "VND" in val_str.upper():
                return "VND"
            if "$" in val_str:
                return "USD"
            if "€" in val_str:
                return "EUR"
        return "VND"

    def _suggest_role(
        self,
        col_name: str,
        col_type: str,
        series: pd.Series,
        numeric_cols: list[str],
        datetime_cols: list[str],
        categorical_cols: list[str],
    ) -> str:
        col_lower = col_name.lower().strip()

        date_keywords = ["date", "time", "ngày", "tháng", "năm", "thời gian", "timestamp", "created", "updated", "order_date", "sale_date", "invoice_date", "transaction_date"]
        for kw in date_keywords:
            if kw.lower() in col_lower:
                return "date"

        revenue_keywords = ["revenue", "sales", "amount", "total", "income", "doanh thu", "doanh số", "bán", "tiền", "thu nhập", "giá trị", "thanh toán", "gross"]
        for kw in revenue_keywords:
            if kw.lower() in col_lower and col_type in ("numeric", "currency"):
                return "metric_revenue"

        cost_keywords = ["cost", "expense", "chi phí", "giá vốn", "cogs", "spend", "mua", "nhập", "purchase", "spending"]
        for kw in cost_keywords:
            if kw.lower() in col_lower and col_type in ("numeric", "currency"):
                return "metric_cost"

        quantity_keywords = ["quantity", "qty", "count", "volume", "units", "số lượng", "sl", "khối lượng", "pieces", "items"]
        for kw in quantity_keywords:
            if kw.lower() in col_lower and col_type in ("numeric",):
                return "metric_quantity"

        product_keywords = ["product", "item", "sku", "brand", "category", "sản phẩm", "mặt hàng", "hàng hóa", "mã", "tên hàng", "name", "sản phẩm", "dịch vụ"]
        for kw in product_keywords:
            if kw.lower() in col_lower and col_type in ("categorical", "text"):
                return "dimension_product"

        region_keywords = ["region", "area", "city", "location", "store", "branch", "vùng", "khu vực", "tỉnh", "thành phố", "chi nhánh", "cửa hàng", "địa điểm"]
        for kw in region_keywords:
            if kw.lower() in col_lower and col_type in ("categorical", "text"):
                return "dimension_region"

        customer_keywords = ["customer", "client", "khách hàng", "khách", "buyer", "người mua", "user", "account"]
        for kw in customer_keywords:
            if kw.lower() in col_lower and col_type in ("categorical", "text"):
                return "dimension_customer"

        profit_keywords = ["profit", "margin", "lợi nhuận", "lãi", "lời", "net", "profitability"]
        for kw in profit_keywords:
            if kw.lower() in col_lower and col_type in ("numeric", "currency", "percentage"):
                return "metric_profit"

        if col_type == "numeric":
            return "metric"

        if col_type == "categorical":
            return "dimension"

        if col_type == "datetime":
            return "date"

        return "other"

    def parse_vn_date(self, value: str) -> datetime | None:
        return dp_parse(value, languages=["vi", "en"])

    def parse_currency(self, value: str) -> tuple[float, str] | None:
        for pattern in self.CURRENCY_PATTERNS:
            m = pattern.search(str(value).strip())
            if m:
                num_str = m.group(1).replace(",", "")
                try:
                    return float(num_str), self._guess_currency([str(value)])
                except ValueError:
                    return None
        return None
