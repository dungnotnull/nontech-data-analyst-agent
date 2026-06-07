from typing import Any
import pandas as pd
import numpy as np


class NarrativeWriter:
    def __init__(self, llm_config: dict | None = None):
        self.llm_config = llm_config or {}

    def write(self, intent: dict, result: Any) -> tuple[str, str | None]:
        analysis_type = intent.get("analysis_type", "summary")
        question = intent.get("original_question", "")
        lang = intent.get("language", "vi")
        metric = intent.get("metric", "auto")

        narrative = self._build_narrative(analysis_type, result, lang, metric)
        recommendation = self._build_recommendation(analysis_type, result, lang, intent)

        return narrative, recommendation

    def _build_narrative(self, analysis_type: str, result: Any, lang: str, metric: str) -> str:
        if lang == "vi":
            return self._build_narrative_vi(analysis_type, result, metric)
        return self._build_narrative_en(analysis_type, result, metric)

    def _build_narrative_vi(self, analysis_type: str, result: Any, metric: str) -> str:
        metric_label = self._metric_label_vi(metric)

        if analysis_type == "ranking":
            return self._narrate_ranking_vi(result, metric_label)
        elif analysis_type == "trend":
            return self._narrate_trend_vi(result, metric_label)
        elif analysis_type == "comparison":
            return self._narrate_comparison_vi(result, metric_label)
        elif analysis_type == "distribution":
            return self._narrate_distribution_vi(result, metric_label)
        elif analysis_type == "anomaly":
            return self._narrate_anomaly_vi(result)
        elif analysis_type == "profitability":
            return self._narrate_profitability_vi(result)
        elif analysis_type == "segmentation":
            return self._narrate_segmentation_vi(result)
        elif analysis_type == "forecast":
            return self._narrate_forecast_vi(result, metric_label)
        else:
            return self._narrate_summary_vi(result)

    def _build_narrative_en(self, analysis_type: str, result: Any, metric: str) -> str:
        metric_label = self._metric_label_en(metric)

        if analysis_type == "ranking":
            return self._narrate_ranking_en(result, metric_label)
        elif analysis_type == "trend":
            return self._narrate_trend_en(result, metric_label)
        elif analysis_type == "comparison":
            return self._narrate_comparison_en(result, metric_label)
        elif analysis_type == "distribution":
            return self._narrate_distribution_en(result, metric_label)
        elif analysis_type == "anomaly":
            return self._narrate_anomaly_en(result)
        elif analysis_type == "profitability":
            return self._narrate_profitability_en(result)
        elif analysis_type == "segmentation":
            return self._narrate_segmentation_en(result)
        elif analysis_type == "forecast":
            return self._narrate_forecast_en(result, metric_label)
        else:
            return self._narrate_summary_en(result)

    def _narrate_ranking_vi(self, result: Any, metric_label: str) -> str:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return "Không có đủ dữ liệu để xếp hạng."

        dim_col = df.columns[0]
        val_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        top = df.head(3)
        bottom = df.tail(3)

        lines = [f"📊 **Kết quả xếp hạng theo {metric_label}:**"]
        lines.append("")
        lines.append(f"**Top {len(top)} cao nhất:**")
        for _, row in top.iterrows():
            lines.append(f"  • {row[dim_col]}: {self._fmt_number(row[val_col])}")

        if len(df) > 6:
            lines.append(f"")
            lines.append(f"**{len(bottom)} thấp nhất:**")
            bottom_rev = bottom.iloc[::-1]
            for _, row in bottom_rev.iterrows():
                lines.append(f"  • {row[dim_col]}: {self._fmt_number(row[val_col])}")

        return "\n".join(lines)

    def _narrate_trend_vi(self, result: Any, metric_label: str) -> str:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return "Không có đủ dữ liệu để phân tích xu hướng."

        val_col = next((c for c in df.columns if c not in ("date", "time", "period")), df.columns[-1])
        values = df[val_col].dropna()

        if len(values) < 2:
            return f"📈 **Xu hướng {metric_label}:** Chỉ có {len(values)} điểm dữ liệu, chưa đủ để xác định xu hướng."

        first_val = values.iloc[0]
        last_val = values.iloc[-1]
        change = last_val - first_val
        change_pct = (change / first_val * 100) if first_val != 0 else 0
        trend = "tăng" if change > 0 else "giảm"
        emoji = "📈" if change > 0 else "📉"

        lines = [
            f"{emoji} **Xu hướng {metric_label}:**",
            f"  • Giá trị đầu kỳ: **{self._fmt_number(first_val)}**",
            f"  • Giá trị cuối kỳ: **{self._fmt_number(last_val)}**",
            f"  • Thay đổi: {'+' if change >= 0 else ''}{self._fmt_number(change)} ({'+' if change_pct >= 0 else ''}{change_pct:.1f}%)",
            f"  • Xu hướng: Đang **{trend}**",
        ]

        peak_idx = values.idxmax()
        peak_val = values.max()
        trough_idx = values.idxmin()
        trough_val = values.min()
        date_col = next((c for c in df.columns if c in ("date", "time", "period")), df.columns[0])
        if peak_idx != len(values) - 1:
            lines.append(f"  • Đỉnh cao nhất: {self._fmt_number(peak_val)} (tại {df.iloc[peak_idx][date_col]})")
        if trough_idx != 0:
            lines.append(f"  • Đáy thấp nhất: {self._fmt_number(trough_val)} (tại {df.iloc[trough_idx][date_col]})")

        return "\n".join(lines)

    def _narrate_comparison_vi(self, result: Any, metric_label: str) -> str:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return "Không có đủ dữ liệu để so sánh."

        dim_col = df.columns[0]
        val_cols = [c for c in df.columns if c != dim_col]

        lines = [f"📊 **So sánh {metric_label}:**"]
        for val_col in val_cols:
            max_row = df.loc[df[val_col].idxmax()]
            min_row = df.loc[df[val_col].idxmin()]
            lines.append(f"  • **{val_col.replace('_', ' ').title()}:**")
            lines.append(f"    - Cao nhất: {max_row[dim_col]} ({self._fmt_number(max_row[val_col])})")
            lines.append(f"    - Thấp nhất: {min_row[dim_col]} ({self._fmt_number(min_row[val_col])})")
        return "\n".join(lines)

    def _narrate_distribution_vi(self, result: Any, metric_label: str) -> str:
        if isinstance(result, dict) and "mean" in result:
            stats = result
            lines = [
                f"📊 **Phân phối {metric_label}:**",
                f"  • Số lượng: {int(stats.get('count', 0)):,}",
                f"  • Trung bình: {self._fmt_number(stats.get('mean', 0))}",
                f"  • Trung vị: {self._fmt_number(stats.get('median', 0))}",
                f"  • Thấp nhất: {self._fmt_number(stats.get('min', 0))}",
                f"  • Cao nhất: {self._fmt_number(stats.get('max', 0))}",
                f"  • Độ lệch chuẩn: {self._fmt_number(stats.get('std', 0))}",
            ]
            return "\n".join(lines)
        return f"Đã phân tích phân phối của {metric_label}."

    def _narrate_anomaly_vi(self, result: Any) -> str:
        if isinstance(result, dict):
            total = result.get("total_rows", 0)
            anomaly_count = result.get("anomaly_count", 0)
            pct = result.get("anomaly_pct", 0)
            anomalies = result.get("anomalies", [])

            lines = [
                f"🔍 **Phát hiện bất thường:**",
                f"  • Tổng số dòng: {total:,}",
                f"  • Số dòng bất thường: **{anomaly_count}** ({pct:.1f}%)",
                "",
            ]

            if anomaly_count == 0:
                lines.append("✅ Không phát hiện dữ liệu bất thường.")
            elif anomaly_count <= 10:
                lines.append(f"⚠️ Phát hiện **{anomaly_count}** điểm bất thường. Bạn nên kiểm tra kỹ các điểm này:")
                for i, a in enumerate(anomalies[:5]):
                    a_str = ", ".join(f"{k}: {self._fmt_number(v) if isinstance(v, (int, float)) else v}"
                                     for k, v in a.items() if not k.startswith("_"))
                    lines.append(f"  {i+1}. {a_str}")
            else:
                lines.append(f"⚠️ Phát hiện **{anomaly_count}** điểm bất thường ({pct:.1f}%). Số lượng bất thường cao, bạn nên kiểm tra lại dữ liệu đầu vào.")

            return "\n".join(lines)
        return "Không có dữ liệu bất thường."

    def _narrate_profitability_vi(self, result: Any) -> str:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return "Không có đủ dữ liệu để phân tích lợi nhuận."

        profit_col = next((c for c in df.columns if "profit" in c.lower()), None)
        margin_col = next((c for c in df.columns if "margin" in c.lower()), None)
        rev_col = next((c for c in df.columns if "revenue" in c.lower()), None)
        cost_col = next((c for c in df.columns if "cost" in c.lower()), None)

        total_profit = df[profit_col].sum() if profit_col and profit_col in df.columns else 0
        total_rev = df[rev_col].sum() if rev_col and rev_col in df.columns else (df.iloc[:, 1].sum() if len(df.columns) > 1 else 0)
        total_cost = df[cost_col].sum() if cost_col and cost_col in df.columns else 0

        profit_status = "có lời" if total_profit > 0 else "đang lỗ"

        lines = [
            f"💰 **Phân tích lợi nhuận:**",
            f"  • Tổng doanh thu: **{self._fmt_number(total_rev)}**",
            f"  • Tổng chi phí: **{self._fmt_number(total_cost)}**",
            f"  • Lợi nhuận: **{self._fmt_number(total_profit)}** ({profit_status})",
        ]

        if margin_col and margin_col in df.columns:
            avg_margin = df[margin_col].mean()
            lines.append(f"  • Biên lợi nhuận trung bình: **{avg_margin:.1f}%**")

        if profit_col and len(df) > 1:
            max_profit_row = df.loc[df[profit_col].idxmax()]
            min_profit_row = df.loc[df[profit_col].idxmin()]
            dim_col = df.columns[0]
            lines.append(f"  • {'Có lời nhất' if total_profit >= 0 else 'Lỗ ít nhất'}: {max_profit_row[dim_col]} ({self._fmt_number(max_profit_row[profit_col])})")
            lines.append(f"  • {'Lỗ nhiều nhất' if total_profit >= 0 else 'Lỗ nặng nhất'}: {min_profit_row[dim_col]} ({self._fmt_number(min_profit_row[profit_col])})")

        return "\n".join(lines)

    def _narrate_segmentation_vi(self, result: Any) -> str:
        if isinstance(result, dict):
            segments = result.get("segments", [])
            if not segments:
                return "Không tìm thấy phân khúc rõ ràng trong dữ liệu."

            lines = [f"👥 **Phân khúc khách hàng/sản phẩm:**", f"  • Tìm thấy **{len(segments)}** phân khúc:", ""]
            for i, seg in enumerate(segments):
                cid = seg.get("cluster_id", i)
                size = seg.get("size", 0)
                pct = seg.get("pct", 0)
                centroid = seg.get("centroid", {})
                centroid_str = ", ".join(f"{k}: {self._fmt_number(v)}" for k, v in centroid.items())
                label = self._name_segment(cid, centroid)
                lines.append(f"  **Phân khúc {cid + 1}: {label}**")
                lines.append(f"    - Số lượng: {size:,} ({pct:.1f}%)")
                if centroid_str:
                    lines.append(f"    - Đặc trưng: {centroid_str}")
                lines.append("")
            return "\n".join(lines)
        return "Không có dữ liệu phân khúc."

    def _narrate_forecast_vi(self, result: Any, metric_label: str) -> str:
        if not isinstance(result, dict):
            return "Không có đủ dữ liệu để dự báo."

        model = result.get("model", "unknown")
        forecast = result.get("forecast", [])
        historical = result.get("historical", [])

        if model == "simple_moving_average":
            last = result.get("last_value", 0)
            sma = result.get("sma_3", 0)
            return (
                f"🔮 **Dự báo {metric_label}:**\n"
                f"  • Giá trị hiện tại: **{self._fmt_number(last)}**\n"
                f"  • Dự báo (trung bình động 3 kỳ): **{self._fmt_number(sma)}**\n"
                f"  ⚠️ Dữ liệu chưa đủ dài để dùng mô hình nâng cao."
            )

        if forecast:
            last_fc = forecast[-1] if forecast else {}
            fc_val = last_fc.get("predicted", last_fc.get("yhat", 0))
            lower = last_fc.get("lower", 0)
            upper = last_fc.get("upper", 0)
            return (
                f"🔮 **Dự báo {metric_label} (Prophet):**\n"
                f"  • Dự báo cuối kỳ: **{self._fmt_number(fc_val)}**\n"
                f"  • Khoảng tin cậy: {self._fmt_number(lower)} – {self._fmt_number(upper)}\n"
                f"  • Dựa trên {len(historical)} điểm dữ liệu lịch sử."
            )

        return f"🔮 Đã thực hiện dự báo {metric_label} bằng mô hình {model}."

    def _narrate_summary_vi(self, result: Any) -> str:
        if not isinstance(result, dict):
            return "Đã phân tích dữ liệu thành công."

        total_rows = result.get("total_rows", 0)
        total_cols = result.get("total_columns", 0)
        numeric_cols = result.get("numeric_columns", [])
        text_cols = result.get("text_columns", [])
        date_range = result.get("date_range", {})
        numeric_stats = result.get("numeric_stats", {})

        lines = [
            f"📋 **Tổng quan dữ liệu:**",
            f"  • Kích thước: **{total_rows:,}** dòng × **{total_cols}** cột",
            f"  • Cột số: {len(numeric_cols)} ({', '.join(numeric_cols[:5])}{'...' if len(numeric_cols) > 5 else ''})",
        ]

        if date_range:
            lines.append(f"  • Thời gian: {date_range.get('min', 'N/A')} → {date_range.get('max', 'N/A')} ({date_range.get('span_days', 0)} ngày)")

        lines.append("")
        if numeric_stats:
            lines.append("**Thống kê các cột chính:**")
            for col, stats in list(numeric_stats.items())[:5]:
                lines.append(f"  • {col}: Tổng {self._fmt_number(stats.get('sum', 0))}, "
                            f"TB {self._fmt_number(stats.get('mean', 0))}, "
                            f"Min {self._fmt_number(stats.get('min', 0))}, "
                            f"Max {self._fmt_number(stats.get('max', 0))}")

        return "\n".join(lines)

    def _narrate_ranking_en(self, result: Any, metric_label: str) -> str:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return "Not enough data to rank."
        dim_col = df.columns[0]
        val_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        top = df.head(3)
        lines = [f"📊 **{metric_label} Ranking:**"]
        for _, row in top.iterrows():
            lines.append(f"  • {row[dim_col]}: {self._fmt_number(row[val_col])}")
        return "\n".join(lines)

    def _narrate_trend_en(self, result: Any, metric_label: str) -> str:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return "Not enough data for trend analysis."
        val_col = next((c for c in df.columns if c not in ("date", "time", "period")), df.columns[-1])
        values = df[val_col].dropna()
        if len(values) < 2:
            return f"📈 Only {len(values)} data points, not enough for trend."
        first_val, last_val = values.iloc[0], values.iloc[-1]
        change = last_val - first_val
        change_pct = (change / first_val * 100) if first_val != 0 else 0
        trend = "up" if change > 0 else "down"
        return (
            f"📈 **{metric_label} Trend:**\n"
            f"  • First: {self._fmt_number(first_val)} → Last: {self._fmt_number(last_val)}\n"
            f"  • Change: {'+' if change >= 0 else ''}{self._fmt_number(change)} ({'+' if change_pct >= 0 else ''}{change_pct:.1f}%) — Trending **{trend}**"
        )

    def _narrate_comparison_en(self, result: Any, metric_label: str) -> str:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return "Not enough data to compare."
        dim_col = df.columns[0]
        val_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        max_row = df.loc[df[val_col].idxmax()]
        min_row = df.loc[df[val_col].idxmin()]
        return (
            f"📊 **{metric_label} Comparison:**\n"
            f"  • Highest: {max_row[dim_col]} ({self._fmt_number(max_row[val_col])})\n"
            f"  • Lowest: {min_row[dim_col]} ({self._fmt_number(min_row[val_col])})"
        )

    def _narrate_distribution_en(self, result: Any, metric_label: str) -> str:
        if isinstance(result, dict) and "mean" in result:
            s = result
            return (
                f"📊 **{metric_label} Distribution:**\n"
                f"  • Count: {int(s.get('count', 0)):,} | Mean: {self._fmt_number(s.get('mean', 0))}\n"
                f"  • Median: {self._fmt_number(s.get('median', 0))} | Std: {self._fmt_number(s.get('std', 0))}\n"
                f"  • Min: {self._fmt_number(s.get('min', 0))} | Max: {self._fmt_number(s.get('max', 0))}"
            )
        return f"Analyzed {metric_label} distribution."

    def _narrate_anomaly_en(self, result: Any) -> str:
        if isinstance(result, dict):
            total = result.get("total_rows", 0)
            anomaly_count = result.get("anomaly_count", 0)
            pct = result.get("anomaly_pct", 0)
            return (
                f"🔍 **Anomaly Detection:**\n"
                f"  • Total rows: {total:,}\n"
                f"  • Anomalies: **{anomaly_count}** ({pct:.1f}%)\n"
                f"  • {'⚠️ Review recommended' if anomaly_count > 0 else '✅ No unusual data detected.'}"
            )
        return "No anomaly data."

    def _narrate_profitability_en(self, result: Any) -> str:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return "Not enough data for profitability."
        profit_col = next((c for c in df.columns if "profit" in c.lower()), None)
        rev_col = next((c for c in df.columns if "revenue" in c.lower()), None)
        total_profit = df[profit_col].sum() if profit_col and profit_col in df.columns else 0
        status = "profitable" if total_profit > 0 else "at a loss"
        return (
            f"💰 **Profitability:**\n"
            f"  • Total Profit: **{self._fmt_number(total_profit)}** — {status}"
        )

    def _narrate_segmentation_en(self, result: Any) -> str:
        if isinstance(result, dict):
            segments = result.get("segments", [])
            if not segments:
                return "No clear segments found."
            lines = [f"👥 **Segments Found: {len(segments)}**"]
            for i, seg in enumerate(segments):
                lines.append(f"  • Segment {seg.get('cluster_id', i)+1}: {seg.get('size', 0):,} items ({seg.get('pct', 0):.1f}%)")
            return "\n".join(lines)
        return "No segment data."

    def _narrate_forecast_en(self, result: Any, metric_label: str) -> str:
        if not isinstance(result, dict):
            return "Not enough data to forecast."
        model = result.get("model", "unknown")
        forecast = result.get("forecast", [])
        if forecast:
            last = forecast[-1]
            fc_val = last.get("predicted", last.get("yhat", 0))
            return f"🔮 **{metric_label} Forecast ({model}):** Final prediction: **{self._fmt_number(fc_val)}**"
        return f"🔮 Forecasted {metric_label} using {model}."

    def _narrate_summary_en(self, result: Any) -> str:
        if not isinstance(result, dict):
            return "Data analyzed successfully."
        total_rows = result.get("total_rows", 0)
        total_cols = result.get("total_columns", 0)
        date_range = result.get("date_range", {})
        lines = [f"📋 **Data Overview:** {total_rows:,} rows × {total_cols} columns"]
        if date_range:
            lines.append(f"  • Date range: {date_range.get('min', 'N/A')} → {date_range.get('max', 'N/A')} ({date_range.get('span_days', 0)} days)")
        return "\n".join(lines)

    def _build_recommendation(self, analysis_type: str, result: Any, lang: str, intent: dict) -> str | None:
        if lang == "vi":
            return self._build_recommendation_vi(analysis_type, result, intent)
        return self._build_recommendation_en(analysis_type, result, intent)

    def _build_recommendation_vi(self, analysis_type: str, result: Any, intent: dict) -> str | None:
        if analysis_type == "ranking":
            df = self._to_dataframe(result)
            if df is not None and len(df) > 0:
                return (
                    "💡 **Gợi ý:** Tập trung nguồn lực vào các mặt hàng dẫn đầu. "
                    "Đối với các mặt hàng cuối bảng, cân nhắc giảm tồn kho hoặc ngừng nhập."
                )

        if analysis_type == "trend":
            df = self._to_dataframe(result)
            if df is not None and len(df) >= 2:
                val_col = next((c for c in df.columns if c not in ("date", "time", "period")), df.columns[-1])
                values = df[val_col].dropna()
                if len(values) >= 2 and values.iloc[-1] < values.iloc[0]:
                    return (
                        "⚠️ **Cảnh báo:** Xu hướng đang giảm. Bạn nên tìm hiểu nguyên nhân (mùa vụ, "
                        "cạnh tranh, giá cả) và có biện pháp điều chỉnh kịp thời."
                    )
                return (
                    "💡 **Gợi ý:** Nếu xu hướng tăng là do mùa vụ, hãy lên kế hoạch tồn kho "
                    "trước mùa cao điểm để tối ưu lợi nhuận."
                )

        if analysis_type == "anomaly":
            if isinstance(result, dict):
                count = result.get("anomaly_count", 0)
                if count > 0:
                    return (
                        f"⚠️ **Cảnh báo:** Phát hiện {count} điểm bất thường. "
                        "Kiểm tra: (1) lỗi nhập liệu, (2) gian lận, (3) sự kiện đặc biệt (khuyến mãi, thiên tai)."
                    )

        if analysis_type == "profitability":
            if isinstance(result, dict) or self._to_dataframe(result) is not None:
                return (
                    "💡 **Gợi ý:** Xem xét cắt giảm các mặt hàng/khu vực có biên lợi nhuận âm. "
                    "Đàm phán lại giá với nhà cung cấp cho các mặt hàng có biên lợi nhuận thấp."
                )

        if analysis_type == "segmentation":
            return (
                "💡 **Gợi ý:** Với khách hàng VIP: chăm sóc đặc biệt, ưu đãi riêng. "
                "Với khách hàng mới: chương trình welcome, giảm giá lần đầu."
            )

        if analysis_type == "forecast":
            return (
                "💡 **Gợi ý:** Dự báo chỉ mang tính tham khảo. Nên kết hợp với kế hoạch kinh doanh "
                "và các yếu tố mùa vụ, thị trường để ra quyết định chính xác hơn."
            )

        return None

    def _build_recommendation_en(self, analysis_type: str, result: Any, intent: dict) -> str | None:
        if analysis_type == "anomaly":
            if isinstance(result, dict):
                count = result.get("anomaly_count", 0)
                if count > 0:
                    return f"⚠️ Detected {count} anomalies. Check for data entry errors, fraud, or special events."
        if analysis_type == "profitability":
            return "💡 Consider cutting products/regions with negative margins."
        return "💡 Review the data carefully before making business decisions."

    def _name_segment(self, cluster_id: int, centroid: dict) -> str:
        if not centroid:
            return f"Nhóm {cluster_id + 1}"

        mean_val = np.mean(list(centroid.values()))
        max_key = max(centroid, key=centroid.get)
        max_val = centroid[max_key]

        if max_val > mean_val * 1.5:
            return "VIP / Cao cấp"
        elif max_val < mean_val * 0.5:
            return "Thấp / Cơ bản"
        return "Trung bình"

    def _to_dataframe(self, result: Any) -> pd.DataFrame | None:
        if isinstance(result, pd.DataFrame):
            return result
        if isinstance(result, dict):
            for key in ("result", "data", "records"):
                val = result.get(key)
                if isinstance(val, pd.DataFrame):
                    return val
                if isinstance(val, list) and len(val) > 0:
                    return pd.DataFrame(val)
            try:
                return pd.DataFrame([result])
            except Exception:
                return None
        if isinstance(result, list):
            try:
                return pd.DataFrame(result)
            except Exception:
                return None
        return None

    def _fmt_number(self, val: Any) -> str:
        if isinstance(val, float):
            if abs(val) >= 1_000_000:
                return f"{val:,.0f}"
            elif abs(val) >= 1:
                return f"{val:,.2f}"
            elif abs(val) >= 0.01:
                return f"{val:.3f}"
            return f"{val:.4f}"
        if isinstance(val, (int, np.integer)):
            return f"{val:,}"
        return str(val)

    def _metric_label_vi(self, metric: str) -> str:
        labels = {
            "revenue": "doanh thu", "profit": "lợi nhuận", "cost": "chi phí",
            "quantity": "số lượng", "margin_pct": "biên lợi nhuận", "auto": "giá trị",
        }
        return labels.get(metric, "giá trị")

    def _metric_label_en(self, metric: str) -> str:
        labels = {
            "revenue": "Revenue", "profit": "Profit", "cost": "Cost",
            "quantity": "Quantity", "margin_pct": "Margin %", "auto": "Value",
        }
        return labels.get(metric, "Value")
