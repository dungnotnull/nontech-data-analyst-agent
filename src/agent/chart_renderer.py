from typing import Any
import json
import base64
import io
import os
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots

pio.templates.default = "plotly_white"

COLOR_PALETTE = [
    "#3366CC", "#DC3912", "#FF9900", "#109618", "#990099",
    "#0099C6", "#DD4477", "#66AA00", "#B82E2E", "#316395",
    "#994499", "#22AA99", "#AAAA11", "#6633CC", "#E67300",
]

COLORBLIND_PALETTE = [
    "#0072B2", "#E69F00", "#009E73", "#F0E442", "#56B4E9",
    "#D55E00", "#CC79A7", "#000000",
]

VIETNAM_GEOJSON_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "vietnam-provinces.geojson"


class ChartRenderer:
    def __init__(self):
        self._color_palette = COLOR_PALETTE
        self._colorblind_palette = COLORBLIND_PALETTE
        self._vietnam_geojson: dict | None = None
        self._load_geojson()

    def render(
        self,
        intent: dict,
        result: Any,
        width: int | None = None,
        height: int | None = None,
        lang: str = "vi",
    ) -> str:
        analysis_type = intent.get("analysis_type", "summary")
        chart_type = intent.get("chart_preference", "auto")
        question = intent.get("original_question", "Phân tích dữ liệu")
        lang = intent.get("language", lang)

        width = width or 800
        height = height or 450

        if analysis_type == "ranking":
            fig = self._render_ranking(result, question, lang, chart_type)
        elif analysis_type == "trend":
            fig = self._render_trend(result, question, lang)
        elif analysis_type == "comparison":
            fig = self._render_comparison(result, question, lang, chart_type)
        elif analysis_type == "distribution":
            fig = self._render_distribution(result, question, lang)
        elif analysis_type == "anomaly":
            fig = self._render_anomaly(result, question, lang)
        elif analysis_type == "profitability":
            fig = self._render_profitability(result, question, lang)
        elif analysis_type == "segmentation":
            fig = self._render_segmentation(result, question, lang)
        elif analysis_type == "forecast":
            fig = self._render_forecast(result, question, lang)
        else:
            fig = self._render_summary(result, question, lang)

        fig.update_layout(
            width=width,
            height=height,
            margin=dict(l=60, r=30, t=60, b=60),
            font=dict(family="Arial, sans-serif", size=12),
        )

        return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        })

    def render_to_image(self, fig: go.Figure, format: str = "png") -> bytes:
        img_bytes = pio.to_image(fig, format=format, width=1200, height=675, scale=2)
        return img_bytes

    def render_to_image_b64(self, fig: go.Figure, format: str = "png") -> str:
        img_bytes = self.render_to_image(fig, format)
        return base64.b64encode(img_bytes).decode("utf-8")

    def _render_ranking(self, result: Any, title: str, lang: str, chart_type: str) -> go.Figure:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return self._empty_chart(title, lang)

        if "dimension" not in df.columns and "value" not in df.columns:
            cols = df.columns.tolist()
            if len(cols) >= 1:
                df = df.rename(columns={cols[0]: "dimension", cols[1]: "value"} if len(cols) >= 2
                               else {cols[0]: "dimension"})

        label_dim = "Hạng mục" if lang == "vi" else "Category"
        label_val = "Giá trị" if lang == "vi" else "Value"

        df = df.sort_values(by="value", ascending=True).tail(15)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df["dimension"].astype(str),
            x=df["value"],
            orientation="h",
            marker=dict(color=self._color_palette[0], opacity=0.85),
            text=df["value"].apply(lambda v: f"{v:,.0f}" if isinstance(v, (int, float)) else str(v)),
            textposition="outside",
        ))
        fig.update_layout(
            title=self._title(title, lang),
            xaxis_title=label_val,
            yaxis_title=label_dim,
            yaxis=dict(autorange="reversed"),
        )
        return fig

    def _render_trend(self, result: Any, title: str, lang: str) -> go.Figure:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return self._empty_chart(title, lang)

        date_col = next((c for c in df.columns if "date" in str(c).lower() or "time" in str(c).lower()), df.columns[0])
        val_col = next((c for c in df.columns if c != date_col and "value" in str(c).lower() or "total" in str(c).lower()),
                       df.columns[1] if len(df.columns) > 1 else df.columns[0])
        label_date = "Thời gian" if lang == "vi" else "Date"
        label_val = "Giá trị" if lang == "vi" else "Value"

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[date_col], y=df[val_col],
            mode="lines+markers",
            name=label_val,
            line=dict(color=self._color_palette[0], width=2.5),
            marker=dict(size=6),
            fill="tozeroy",
            fillcolor=f"rgba({self._hex_to_rgba(self._color_palette[0], 0.15)})",
        ))
        fig.update_layout(
            title=self._title(title, lang),
            xaxis_title=label_date,
            yaxis_title=label_val,
            hovermode="x unified",
        )
        return fig

    def _render_comparison(self, result: Any, title: str, lang: str, chart_type: str) -> go.Figure:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return self._empty_chart(title, lang)

        dim_col = next((c for c in df.columns if c not in ("total", "average", "count", "value")),
                       df.columns[0])
        metric_cols = [c for c in df.columns if c != dim_col]

        label_dim = "Hạng mục" if lang == "vi" else "Category"
        label_val = "Giá trị" if lang == "vi" else "Value"

        fig = go.Figure()
        colors = self._color_palette[:len(metric_cols)]
        for i, mc in enumerate(metric_cols):
            fig.add_trace(go.Bar(
                x=df[dim_col].astype(str),
                y=df[mc],
                name=mc.replace("_", " ").title(),
                marker=dict(color=colors[i % len(colors)]),
            ))
        fig.update_layout(
            title=self._title(title, lang),
            xaxis_title=label_dim,
            yaxis_title=label_val,
            barmode="group",
        )
        return fig

    def _render_distribution(self, result: Any, title: str, lang: str) -> go.Figure:
        if isinstance(result, dict) and "mean" in result:
            stats = result
            fig = go.Figure()
            fig.add_trace(go.Indicator(
                mode="gauge+number+delta",
                value=stats.get("mean", 0),
                title={"text": "Trung bình" if lang == "vi" else "Mean"},
                delta={"reference": stats.get("median", 0)},
                gauge={
                    "axis": {"range": [stats.get("min", 0), stats.get("max", 100)]},
                    "bar": {"color": self._color_palette[0]},
                    "steps": [
                        {"range": [stats.get("min", 0), stats.get("q25", 25)], "color": "#E8F0FE"},
                        {"range": [stats.get("q25", 25), stats.get("q75", 75)], "color": "#B3D4FC"},
                        {"range": [stats.get("q75", 75), stats.get("max", 100)], "color": "#E8F0FE"},
                    ],
                },
            ))
            fig.update_layout(title=self._title(title, lang))
            return fig

        df = self._to_dataframe(result)
        if df is None or df.empty:
            return self._empty_chart(title, lang)

        val_col = df.select_dtypes(include=["int64", "float64"]).columns
        if len(val_col) == 0:
            return self._empty_chart(title, lang)

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=df[val_col[0]],
            nbinsx=30,
            marker=dict(color=self._color_palette[0], opacity=0.75),
            name="Phân bố" if lang == "vi" else "Distribution",
        ))
        fig.update_layout(
            title=self._title(title, lang),
            xaxis_title=val_col[0],
            yaxis_title="Tần suất" if lang == "vi" else "Frequency",
        )
        return fig

    def _render_anomaly(self, result: Any, title: str, lang: str) -> go.Figure:
        anomalies = []
        total = 0
        anomaly_count = 0

        if isinstance(result, dict):
            anomalies = result.get("anomalies", [])
            total = result.get("total_rows", 0)
            anomaly_count = result.get("anomaly_count", len(anomalies))

        label_title = "Phát hiện bất thường" if lang == "vi" else "Anomaly Detection"
        label_normal = "Bình thường" if lang == "vi" else "Normal"
        label_anomaly = "Bất thường" if lang == "vi" else "Anomaly"

        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="number+gauge",
            value=anomaly_count,
            title={"text": f"{label_title}: {anomaly_count}/{total}"},
            gauge={
                "axis": {"range": [0, max(total, 1)]},
                "bar": {"color": self._color_palette[1]},
                "steps": [
                    {"range": [0, total * 0.05], "color": "#E8F0FE"},
                    {"range": [total * 0.05, total * 0.15], "color": "#FFF3CD"},
                    {"range": [total * 0.15, total], "color": "#F8D7DA"},
                ],
            },
        ))
        fig.update_layout(title=self._title(title, lang))
        return fig

    def _render_profitability(self, result: Any, title: str, lang: str) -> go.Figure:
        df = self._to_dataframe(result)
        if df is None or df.empty:
            return self._empty_chart(title, lang)

        label_dim = "Hạng mục" if lang == "vi" else "Category"
        label_rev = "Doanh thu" if lang == "vi" else "Revenue"
        label_profit = "Lợi nhuận" if lang == "vi" else "Profit"

        dim_col = next((c for c in df.columns if c not in ("total_revenue", "total_cost", "profit", "margin_pct")),
                       df.columns[0])

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=df[dim_col].astype(str), y=df.get("total_revenue", df.iloc[:, 1]),
            name=label_rev, marker=dict(color=self._color_palette[0], opacity=0.7),
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=df[dim_col].astype(str), y=df.get("profit", df.iloc[:, 3]) if "profit" in df.columns else df.iloc[:, 1],
            name=label_profit, mode="lines+markers",
            line=dict(color=self._color_palette[2], width=3),
            marker=dict(size=8),
        ), secondary_y=True)
        fig.update_layout(title=self._title(title, lang), xaxis_title=label_dim)
        fig.update_yaxes(title_text=label_rev, secondary_y=False)
        fig.update_yaxes(title_text=label_profit, secondary_y=True)
        return fig

    def _render_segmentation(self, result: Any, title: str, lang: str) -> go.Figure:
        segments = []
        if isinstance(result, dict):
            segments = result.get("segments", [])

        if not segments:
            return self._empty_chart(title, lang)

        label_seg = "Phân khúc" if lang == "vi" else "Segment"
        label_size = "Kích thước" if lang == "vi" else "Size"

        labels = [f"{label_seg} {s.get('cluster_id', i)}" for i, s in enumerate(segments)]
        sizes = [s.get("size", 0) for s in segments]
        pcts = [s.get("pct", 0) for s in segments]
        colors = self._color_palette[:len(segments)]

        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=labels, values=sizes,
            marker=dict(colors=colors),
            textinfo="label+percent",
            hole=0.4,
        ))
        fig.update_layout(title=self._title(title, lang))
        return fig

    def _render_forecast(self, result: Any, title: str, lang: str) -> go.Figure:
        historical = []
        forecast = []

        if isinstance(result, dict):
            historical = result.get("historical", [])
            forecast = result.get("forecast", [])

        label_date = "Thời gian" if lang == "vi" else "Date"
        label_actual = "Thực tế" if lang == "vi" else "Actual"
        label_forecast = "Dự báo" if lang == "vi" else "Forecast"

        fig = go.Figure()
        if historical:
            hist_df = pd.DataFrame(historical)
            date_col = next((c for c in hist_df.columns if "date" in str(c).lower()), hist_df.columns[0])
            val_col = next((c for c in hist_df.columns if c != date_col and "total" in str(c).lower() or "avg" in str(c).lower()),
                           hist_df.columns[1] if len(hist_df.columns) > 1 else hist_df.columns[0])
            fig.add_trace(go.Scatter(
                x=hist_df[date_col], y=hist_df[val_col],
                mode="lines", name=label_actual,
                line=dict(color=self._color_palette[0], width=2),
            ))

        if forecast:
            fcst_df = pd.DataFrame(forecast)
            date_col = next((c for c in fcst_df.columns if "date" in str(c).lower()), fcst_df.columns[0])
            pred_col = next((c for c in fcst_df.columns if "predicted" in str(c).lower() or "yhat" in str(c).lower()),
                            fcst_df.columns[1] if len(fcst_df.columns) > 1 else fcst_df.columns[0])
            fig.add_trace(go.Scatter(
                x=fcst_df[date_col], y=fcst_df[pred_col],
                mode="lines", name=label_forecast,
                line=dict(color=self._color_palette[2], width=2.5, dash="dash"),
            ))
            lower_col = next((c for c in fcst_df.columns if "lower" in str(c).lower()), None)
            upper_col = next((c for c in fcst_df.columns if "upper" in str(c).lower()), None)
            if lower_col and upper_col:
                fig.add_trace(go.Scatter(
                    x=list(fcst_df[date_col]) + list(fcst_df[date_col][::-1]),
                    y=list(fcst_df[upper_col]) + list(fcst_df[lower_col][::-1]),
                    fill="toself", fillcolor=f"rgba({self._hex_to_rgba(self._color_palette[2], 0.15)})",
                    line=dict(color="transparent"),
                    showlegend=False, hoverinfo="skip",
                ))

        fig.update_layout(title=self._title(title, lang), hovermode="x unified")
        return fig

    def _render_summary(self, result: Any, title: str, lang: str) -> go.Figure:
        if not isinstance(result, dict) or "numeric_stats" not in result:
            return self._empty_chart(title, lang)

        stats = result.get("numeric_stats", {})
        cols = list(stats.keys())[:6]
        if not cols:
            return self._empty_chart(title, lang)

        label_col = "Cột" if lang == "vi" else "Column"
        label_sum = "Tổng" if lang == "vi" else "Sum"
        label_mean = "Trung bình" if lang == "vi" else "Mean"

        fig = make_subplots(rows=1, cols=2, subplot_titles=(label_sum, label_mean))
        sums = [stats[c].get("sum", 0) for c in cols]
        means = [stats[c].get("mean", 0) for c in cols]
        short_names = [c[:15] + "..." if len(c) > 15 else c for c in cols]

        fig.add_trace(go.Bar(
            x=short_names, y=sums,
            marker=dict(color=self._color_palette[:len(cols)]),
            showlegend=False,
        ), row=1, col=1)
        fig.add_trace(go.Bar(
            x=short_names, y=means,
            marker=dict(color=self._color_palette[:len(cols)]),
            showlegend=False,
        ), row=1, col=2)

        fig.update_layout(title=self._title(title, lang))
        return fig

    def _empty_chart(self, title: str, lang: str) -> go.Figure:
        msg = "Không đủ dữ liệu để vẽ biểu đồ" if lang == "vi" else "Not enough data to render chart"
        fig = go.Figure()
        fig.add_annotation(
            text=msg, showarrow=False,
            font=dict(size=16, color="#888"),
            xref="paper", yref="paper", x=0.5, y=0.5,
        )
        fig.update_layout(title=self._title(title, lang))
        return fig

    def _to_dataframe(self, result: Any) -> pd.DataFrame | None:
        if isinstance(result, pd.DataFrame):
            return result
        if isinstance(result, dict):
            for key in ("result", "data", "records", "anomalies", "forecast"):
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

    def _title(self, question: str, lang: str) -> str:
        prefix = "Phân tích: " if lang == "vi" else "Analysis: "
        clean = question.strip().rstrip("?").rstrip(".")
        if len(clean) > 80:
            clean = clean[:77] + "..."
        return prefix + clean

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"{r},{g},{b},{alpha}"

    def _load_geojson(self):
        if VIETNAM_GEOJSON_PATH.exists():
            import json
            with open(VIETNAM_GEOJSON_PATH, "r", encoding="utf-8") as f:
                self._vietnam_geojson = json.load(f)

    def render_vietnam_map(
        self, df: pd.DataFrame, region_col: str, value_col: str,
        title: str = "", lang: str = "vi",
    ) -> str:
        if not self._vietnam_geojson:
            return self._empty_chart(title, lang).to_html()

        fig = px.choropleth(
            df,
            geojson=self._vietnam_geojson,
            locations=region_col,
            featureidkey="properties.name",
            color=value_col,
            color_continuous_scale="Blues",
            title=self._title(title, lang) if title else "Bản đồ Việt Nam",
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
