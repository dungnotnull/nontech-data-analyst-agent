import re
from typing import Any, Optional
import pandas as pd
import numpy as np

from src.config.llm_config import get_llm_config, sanitize_for_llm
from src.data.schema_detector import SchemaDetector


INTENT_SCHEMA_DESCRIPTION = """
Extract the structured analytical intent from a business question in Vietnamese or English.
Return ONLY a valid JSON object with these fields:
{
  "analysis_type": "ranking" | "trend" | "comparison" | "distribution" | "anomaly" | "profitability" | "segmentation" | "forecast" | "summary",
  "metric": "revenue" | "profit" | "cost" | "quantity" | "count" | "margin_pct" | "auto",
  "metric_column": null or specific column name if user mentions one,
  "dimensions": ["product", "region", "customer", "time", "category", "employee"],
  "dimension_column": null or specific column name,
  "time_filter": "last_month" | "last_3_months" | "last_6_months" | "last_year" | "ytd" | "all_time" | "custom",
  "time_column": null or column name,
  "custom_time_start": null or "YYYY-MM-DD",
  "custom_time_end": null or "YYYY-MM-DD",
  "chart_preference": "bar" | "line" | "pie" | "heatmap" | "scatter" | "box" | "histogram" | "auto",
  "top_n": 5 or 10 or 20,
  "group_by": null or column name,
  "sort_order": "desc" or "asc",
  "filters": [{"column": "name", "operator": "eq|gt|lt|gte|lte|neq|in|contains", "value": "..."}],
  "language": "vi" or "en",
  "confidence": 0.0 to 1.0,
  "original_question": "the full user question"
}

Analysis type definitions:
- ranking: "which is best/worst/top/bottom" → bar chart
- trend: "how has X changed over time" → line chart
- comparison: "compare X vs Y" or "X by region/category" → grouped bar
- distribution: "how is X distributed" or "spread of values" → histogram/box
- anomaly: "anything unusual/abnormal/unexpected" → scatter/box
- profitability: "profit/margin/loss" → bar/heatmap
- segmentation: "groups/clusters/types of" → scatter
- forecast: "predict/forecast/expect/dự báo" → line
- summary: "tell me about/overview/summary/general info" → table only

Metric definitions:
- revenue: sales, income, doanh thu, doanh số, tiền bán, tiền về
- profit: profit, margin, lợi nhuận, lãi, lời, net income
- cost: cost, expense, chi phí, giá vốn, spending
- quantity: count, volume, quantity, số lượng, pieces, items, units
- margin_pct: percentage margin, tỷ lệ lợi nhuận, profit percentage

Dimension definitions:
- product: product, item, SKU, mặt hàng, sản phẩm, hàng hóa, tên hàng
- region: region, city, area, branch, vùng, khu vực, tỉnh, thành phố, chi nhánh
- customer: customer, client, buyer, khách hàng, người mua
- time: date, time, month, year, quarterly, ngày, tháng, năm
- category: category, type, group, danh mục, loại, phân loại
- employee: employee, staff, salesperson, nhân viên, người bán

Vietnamese time expressions:
- "tháng vừa rồi" / "tháng này" → last_month
- "3 tháng qua" → last_3_months
- "6 tháng qua" / "nửa năm qua" → last_6_months
- "năm qua" / "năm vừa rồi" → last_year
- "từ đầu năm" / "năm nay" → ytd
- "tất cả" / "từ trước đến giờ" → all_time

Vietnamese analysis expressions:
- "bán chạy nhất" / "hàng chạy" / "top" → ranking
- "xu hướng" / "biến động" / "thay đổi theo thời gian" → trend
- "so sánh" / "hơn kém" / "đối chiếu" → comparison
- "phân bố" / "phân phối" / "trải rộng" → distribution
- "bất thường" / "đột biến" / "lạ" → anomaly
- "lãi lỗ" / "lợi nhuận" / "có lời không" → profitability
- "phân nhóm" / "phân khúc" / "nhóm" → segmentation
- "dự báo" / "dự đoán" → forecast
"""


class IntentParser:
    def __init__(self, schema_context: dict[str, Any] | None = None):
        self.llm_config = get_llm_config()
        self.schema_context = schema_context or {}
        self._synonym_map = self._build_synonym_map()

    def parse(self, question: str) -> dict[str, Any]:
        result = self._rule_based_parse(question)
        if result.get("confidence", 0) < 0.6:
            llm_result = self._llm_parse(question)
            if llm_result and llm_result.get("confidence", 0) > result.get("confidence", 0):
                result = llm_result

        result["original_question"] = question
        return result

    def parse_with_schema(
        self, question: str, df: pd.DataFrame, df_name: str = "data"
    ) -> dict[str, Any]:
        detector = SchemaDetector()
        schema = detector.detect(df)
        self.schema_context = schema

        intent = self.parse(question)
        intent["schema_context"] = schema

        if not intent.get("metric_column") and schema.get("suggested_roles"):
            intent["metric_column"] = self._find_role_column(schema, "metric_revenue", "metric_profit", "metric", "numeric")
        if not intent.get("time_column") and schema.get("suggested_roles"):
            intent["time_column"] = self._find_role_column(schema, "date")
        if not intent.get("dimension_column") and schema.get("suggested_roles"):
            intent["dimension_column"] = self._find_role_column(
                schema, "dimension_product", "dimension_region", "dimension", "categorical"
            )

        return intent

    def _rule_based_parse(self, question: str) -> dict[str, Any]:
        q = question.lower().strip()
        intent: dict[str, Any] = {
            "analysis_type": "summary",
            "metric": "auto",
            "metric_column": None,
            "dimensions": [],
            "dimension_column": None,
            "time_filter": "all_time",
            "time_column": None,
            "custom_time_start": None,
            "custom_time_end": None,
            "chart_preference": "auto",
            "top_n": 10,
            "group_by": None,
            "sort_order": "desc",
            "filters": [],
            "language": "vi" if self._contains_vietnamese(q) else "en",
            "confidence": 0.0,
        }

        confidence_score = 0.0

        analysis_rules = [
            (r"\b(ban chay|ban chạy|bán chạy|chay nhat|chạy nhất|top|tot nhat|tốt nhất|cao nhat|cao nhất|nhieu nhat|nhiều nhất|best|highest|most|bestseller)\b", "ranking", 0.6),
            (r"\b(thap nhat|thấp nhất|it nhat|ít nhất|kem nhat|kém nhất|te nhat|tệ nhất|worst|lowest|least|bottom)\b", "ranking", 0.6),
            (r"\b(xu huong|xu hướng|trend|bien dong|biến động|thay doi|thay đổi|tang truong|tăng trưởng|growth|over time|theo thoi gian|theo thời gian|dien bien|diễn biến)\b", "trend", 0.7),
            (r"\b(so sanh|so sánh|compare|comparison|doi chieu|đối chiếu|hon kem|hơn kém|versus|vs\.?)\b", "comparison", 0.6),
            (r"\b(phan bo|phân bố|phan phoi|phân phối|distribution|spread|trai|trải|phan tan|phân tán|histogram)\b", "distribution", 0.7),
            (r"\b(bat thuong|bất thường|dot bien|đột biến|la|lạ|anomaly|outlier|unusual|dang ngo|đáng ngờ)\b", "anomaly", 0.83),
            (r"\b(lai lo|lãi lỗ|loi nhuan|lợi nhuận|profit|loi lo|lời lỗ|margin|co loi|có lời|sinh loi|sinh lời|lo von|lỗ vốn)\b", "profitability", 0.75),
            (r"\b(phan nhom|phân nhóm|nhom|nhóm|phan khuc|phân khúc|segment|cluster|group|customer type|loai khach|loại khách)\b", "segmentation", 0.78),
            (r"\b(du bao|dự báo|du doan|dự đoán|forecast|predict|uoc tinh|ước tính|estimate future|se|sẽ|toi|tới|sap toi|sắp tới)\b", "forecast", 0.82),
            (r"\b(tong quan|tổng quan|tom tat|tóm tắt|overview|summary|cho biet|cho biết|thong tin|thông tin|mo ta|mô tả|describe|tell me about)\b", "summary", 0.55),
        ]

        for pattern, atype, conf in analysis_rules:
            if re.search(pattern, q):
                intent["analysis_type"] = atype
                confidence_score = max(confidence_score, conf)
                break

        metric_rules = [
            (r"\b(doanh thu|doanh số|tiền bán|tiền về|revenue|sales|income)\b", "revenue", 0.6),
            (r"\b(lợi nhuận|lãi|lời|profit|margin|net income)\b", "profit", 0.6),
            (r"\b(chi phí|phí|cost|expense|spending|giá vốn|cogs)\b", "cost", 0.6),
            (r"\b(số lượng|số cái|số ly|quantity|count|volume|pieces|units|items)\b", "quantity", 0.55),
            (r"\b(tỷ lệ lợi nhuận|biên lợi nhuận|margin pct|profit percentage|%)\b", "margin_pct", 0.55),
        ]

        for pattern, metric, conf in metric_rules:
            if re.search(pattern, q):
                intent["metric"] = metric
                confidence_score = max(confidence_score, conf)
                break

        time_rules = [
            (r"\b(tháng này|tháng vừa rồi|tháng qua|this month|last month)\b", "last_month", 0.5),
            (r"\b(3 tháng|quý|quarter|3 months|three months)\b", "last_3_months", 0.5),
            (r"\b(6 tháng|nửa năm|half year|6 months|six months)\b", "last_6_months", 0.5),
            (r"\b(năm qua|năm vừa rồi|năm ngoái|last year|past year|previous year)\b", "last_year", 0.55),
            (r"\b(năm nay|từ đầu năm|this year|ytd|year to date)\b", "ytd", 0.55),
        ]

        for pattern, tfilter, conf in time_rules:
            if re.search(pattern, q):
                intent["time_filter"] = tfilter
                confidence_score = max(confidence_score, conf)
                break

        chart_rules = [
            (r"\b(biểu đồ cột|bar chart|bar|column chart|cột)\b", "bar", 0.4),
            (r"\b(biểu đồ đường|line chart|line|đường|trend line)\b", "line", 0.4),
            (r"\b(biểu đồ tròn|pie chart|pie|tròn)\b", "pie", 0.4),
            (r"\b(scatter|phân tán|scatter plot|scatterplot)\b", "scatter", 0.4),
            (r"\b(heatmap|bản đồ nhiệt|nhiệt)\b", "heatmap", 0.4),
        ]

        for pattern, chart, conf in chart_rules:
            if re.search(pattern, q):
                intent["chart_preference"] = chart
                break

        top_n_match = re.search(r"\b(top|trên)\s*(\d+)\b", q)
        if top_n_match:
            intent["top_n"] = int(top_n_match.group(2))

        dim_rules = [
            (r"\b(theo (mặt hàng|sản phẩm|hàng hóa|hàng)|by product|by item)\b", "product"),
            (r"\b(theo (vùng|khu vực|tỉnh|thành phố|chi nhánh|cửa hàng)|by region|by city|by area|by store|by branch)\b", "region"),
            (r"\b(theo (khách hàng|khách)|by customer|by client)\b", "customer"),
            (r"\b(theo (tháng|quý|năm|tuần|ngày)|by month|by quarter|by year|by week|by day)\b", "time"),
            (r"\b(theo (danh mục|loại|phân loại)|by category|by type)\b", "category"),
            (r"\b(theo (nhân viên|người bán|staff)|by employee|by staff|by salesperson)\b", "employee"),
        ]

        for pattern, dim in dim_rules:
            if re.search(pattern, q) and dim not in intent["dimensions"]:
                intent["dimensions"].append(dim)
                confidence_score = max(confidence_score, 0.4)

        intent["confidence"] = min(confidence_score, 1.0)
        if intent["analysis_type"] == "summary" and confidence_score < 0.3:
            intent["confidence"] = 0.15

        return intent

    def _llm_parse(self, question: str) -> dict[str, Any] | None:
        provider = self.llm_config.get("provider", "local")
        api_key = self.llm_config.get("api_key")
        model = self.llm_config.get("model")

        if provider == "local" or not api_key:
            return None

        try:
            import litellm
            litellm.suppress_debug_info = True

            messages = [
                {"role": "system", "content": INTENT_SCHEMA_DESCRIPTION},
                {"role": "user", "content": f"Question: {question}\n\nReturn ONLY the JSON. No explanation."},
            ]

            response = litellm.completion(
                model=f"{provider}/{model}" if provider != "openai" else model,
                messages=messages,
                api_key=api_key,
                max_tokens=500,
                temperature=0.0,
            )

            content = response.choices[0].message.content
            import json
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(content[json_start:json_end])
                parsed["original_question"] = question
                if "confidence" not in parsed:
                    parsed["confidence"] = 0.85
                return parsed
        except Exception:
            pass

        return None

    def _contains_vietnamese(self, text: str) -> bool:
        vi_chars = set("àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")
        text_lower = text.lower()
        if any(c in vi_chars for c in text_lower):
            return True
        vi_no_tone_words = {
            "pham", "nao", "chay", "nhieu", "nhieu nhat", "khong", "co", "khach",
            "hang", "mat hang", "san pham", "doanh thu", "doanh so", "loi nhuan",
            "chi phi", "ban hang", "thang", "nam", "tuan", "hom nay", "hom qua",
            "vui long", "cho toi", "giup toi", "lam on", "cua toi", "du lieu",
            "so lieu", "phan tich", "bao cao", "kiem tra", "xem xet", "tinh hinh",
            "ket qua", "thong ke", "du bao", "so sanh", "danh gia", "de xuat",
            "cai nay", "cai kia", "nhu the nao", "tai sao", "vi sao", "may",
            "cai gi", "gi", "la", "cua", "cho", "voi", "tren", "duoi", "rat",
            "qua", "lam", "bi", "duoc", "se", "dang", "da", "chua", "moi",
            "cu", "hon", "nhat", "nua", "roi", "nhe", "nha", "di", "ra",
            "vao", "len", "xuong", "toi", "minh", "ban", "anh", "chi", "em",
            "ong", "ba", "co", "chu", "bac", "nhan vien", "chu cua hang",
        }
        words = set(text_lower.split())
        overlap = words & vi_no_tone_words
        return len(overlap) >= 2 or (len(words) <= 3 and len(overlap) >= 1)

    def _find_role_column(self, schema: dict, *roles: str) -> str | None:
        suggested = schema.get("suggested_roles", {})
        columns = schema.get("columns", [])
        for role in roles:
            for col, crole in suggested.items():
                if crole == role and col in columns:
                    return col
        for role in roles:
            for col, crole in suggested.items():
                if crole.startswith(role) and col in columns:
                    return col
        if roles and columns:
            for col, ctype in schema.get("column_types", {}).items():
                if roles[-1] == "numeric" and ctype in ("numeric", "currency"):
                    return col
                if roles[-1] == "categorical" and ctype == "categorical":
                    return col
        return columns[0] if columns else None

    def _build_synonym_map(self) -> dict[str, list[str]]:
        return {
            "revenue": ["doanh thu", "doanh số", "tiền bán", "tiền về", "thu nhập", "sales", "income", "revenue", "doanh thu bán hàng"],
            "profit": ["lợi nhuận", "lãi", "lời", "profit", "margin", "net income", "lợi nhuận ròng"],
            "cost": ["chi phí", "phí", "cost", "expense", "spending", "giá vốn", "cogs", "chi tiêu"],
            "quantity": ["số lượng", "sl", "quantity", "count", "volume", "pieces", "units", "items", "số cái"],
            "product": ["sản phẩm", "mặt hàng", "hàng hóa", "product", "item", "sku", "tên hàng", "hàng"],
            "region": ["vùng", "khu vực", "tỉnh", "thành phố", "chi nhánh", "cửa hàng", "region", "city", "store", "branch", "location"],
            "customer": ["khách hàng", "khách", "customer", "client", "buyer", "người mua"],
            "month": ["tháng", "month"],
            "year": ["năm", "year"],
        }
