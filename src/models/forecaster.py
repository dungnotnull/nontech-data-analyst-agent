from typing import Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json


class Forecaster:
    def __init__(self):
        self._prophet_available = None
        self._statsforecast_available = None

    def forecast(
        self,
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        periods: int = 30,
        freq: str = "D",
        method: str = "auto",
        include_history: bool = True,
    ) -> dict[str, Any]:
        if date_col not in df.columns:
            date_col = self._find_date_column(df)
        if target_col not in df.columns:
            target_col = self._find_numeric_column(df, exclude=date_col)

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col, target_col])
        df = df.sort_values(date_col)

        if len(df) < 3:
            return self._simple_forecast(df, target_col, periods)

        if method == "auto":
            if len(df) >= 10:
                return self._prophet_forecast(df, date_col, target_col, periods, freq, include_history)
            else:
                return self._stats_forecast(df, date_col, target_col, periods, freq, include_history)
        elif method == "prophet":
            return self._prophet_forecast(df, date_col, target_col, periods, freq, include_history)
        elif method == "stats":
            return self._stats_forecast(df, date_col, target_col, periods, freq, include_history)
        elif method == "simple":
            return self._simple_forecast(df, target_col, periods)
        else:
            return self._simple_forecast(df, target_col, periods)

    def evaluate(
        self,
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        holdout_periods: int = 7,
    ) -> dict[str, Any]:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col, target_col])
        df = df.sort_values(date_col)

        if len(df) < holdout_periods + 3:
            return {"error": "Not enough data for evaluation", "metrics": {}}

        train = df.iloc[:-holdout_periods]
        test = df.iloc[-holdout_periods:]

        result = self.forecast(
            train, date_col, target_col,
            periods=holdout_periods, method="auto", include_history=False,
        )

        forecast_vals = []
        actual_vals = []
        forecast_data = result.get("forecast", [])
        for fc in forecast_data:
            fc_date = fc.get("date")
            if fc_date:
                actual = test[test[date_col] == fc_date][target_col]
                if len(actual) > 0:
                    forecast_vals.append(fc.get("predicted", fc.get("yhat", 0)))
                    actual_vals.append(actual.iloc[0])

        if not forecast_vals:
            return {"error": "Could not align forecast with test data", "metrics": {}}

        forecast_arr = np.array(forecast_vals)
        actual_arr = np.array(actual_vals)

        mape = np.mean(np.abs((actual_arr - forecast_arr) / np.where(actual_arr != 0, actual_arr, 1))) * 100
        rmse = np.sqrt(np.mean((actual_arr - forecast_arr) ** 2))
        mae = np.mean(np.abs(actual_arr - forecast_arr))
        mad = np.mean(np.abs(actual_arr - np.mean(actual_arr)))

        return {
            "metrics": {
                "mape": round(float(mape), 2),
                "rmse": round(float(rmse), 2),
                "mae": round(float(mae), 2),
                "mad": round(float(mad), 2),
                "mase": round(float(mae / max(mad, 0.0001)), 2),
            },
            "holdout_periods": holdout_periods,
            "forecast_samples": len(forecast_vals),
        }

    def add_vietnam_holidays(self) -> pd.DataFrame:
        holidays = [
            ("New Year's Day", "2025-01-01"),
            ("Vietnamese New Year's Eve", "2025-01-28"),
            ("Vietnamese New Year", "2025-01-29"),
            ("Vietnamese New Year Holiday", "2025-01-30"),
            ("Vietnamese New Year Holiday", "2025-01-31"),
            ("Vietnamese New Year Holiday", "2025-02-01"),
            ("Vietnamese New Year Holiday", "2025-02-02"),
            ("Hung Kings' Festival", "2025-04-07"),
            ("Reunification Day", "2025-04-30"),
            ("International Workers' Day", "2025-05-01"),
            ("National Day", "2025-09-02"),
            ("New Year's Day", "2026-01-01"),
            ("Vietnamese New Year's Eve", "2026-02-16"),
            ("Vietnamese New Year", "2026-02-17"),
            ("Vietnamese New Year Holiday", "2026-02-18"),
            ("Vietnamese New Year Holiday", "2026-02-19"),
            ("Vietnamese New Year Holiday", "2026-02-20"),
            ("Vietnamese New Year Holiday", "2026-02-21"),
            ("Hung Kings' Festival", "2026-04-26"),
            ("Reunification Day", "2026-04-30"),
            ("International Workers' Day", "2026-05-01"),
            ("National Day", "2026-09-02"),
        ]
        return pd.DataFrame(holidays, columns=["holiday", "ds"])

    def _prophet_forecast(
        self, df: pd.DataFrame, date_col: str, target_col: str,
        periods: int, freq: str, include_history: bool,
    ) -> dict[str, Any]:
        try:
            from prophet import Prophet

            prophet_df = df[[date_col, target_col]].rename(columns={date_col: "ds", target_col: "y"})
            prophet_df = prophet_df.dropna()

            if len(prophet_df) < 5:
                return self._stats_forecast(df, date_col, target_col, periods, freq, include_history)

            model = Prophet(
                weekly_seasonality=True,
                yearly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
            )

            holidays_df = self.add_vietnam_holidays()
            model.add_country_holidays(country_name="VN")

            model.fit(prophet_df)

            future = model.make_future_dataframe(periods=periods, freq=freq)
            forecast = model.predict(future)

            forecast_result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)
            forecast_list = []
            for _, row in forecast_result.iterrows():
                forecast_list.append({
                    "date": row["ds"].isoformat() if hasattr(row["ds"], "isoformat") else str(row["ds"]),
                    "predicted": round(float(row["yhat"]), 2),
                    "lower": round(float(row["yhat_lower"]), 2),
                    "upper": round(float(row["yhat_upper"]), 2),
                })

            historical_list = []
            if include_history:
                hist_data = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].head(len(prophet_df))
                for _, row in hist_data.iterrows():
                    historical_list.append({
                        "date": row["ds"].isoformat() if hasattr(row["ds"], "isoformat") else str(row["ds"]),
                        "total": round(float(row["yhat"]), 2),
                        "avg": round(float(row["yhat"]), 2),
                    })

            return {
                "model": "prophet",
                "forecast": forecast_list,
                "historical": historical_list,
                "forecast_periods": periods,
            }

        except Exception as e:
            return self._stats_forecast(df, date_col, target_col, periods, freq, include_history)

    def _stats_forecast(
        self, df: pd.DataFrame, date_col: str, target_col: str,
        periods: int, freq: str, include_history: bool,
    ) -> dict[str, Any]:
        try:
            from statsforecast import StatsForecast
            from statsforecast.models import AutoARIMA, AutoETS

            series = df.groupby(pd.Grouper(key=date_col, freq="D"))[target_col].sum().reset_index()
            series = series.dropna()
            series["unique_id"] = "series_1"
            series = series.rename(columns={date_col: "ds", target_col: "y"})

            if len(series) < 5:
                return self._simple_forecast(df, target_col, periods)

            model = StatsForecast(
                models=[AutoARIMA(season_length=7), AutoETS(season_length=7)],
                freq="D",
                n_jobs=1,
            )

            model.fit(series)
            forecast = model.predict(h=periods)

            forecast_list = []
            for _, row in forecast.iterrows():
                forecast_list.append({
                    "date": str(row["ds"]),
                    "predicted": round(float(row.get("AutoARIMA", row.get("AutoETS", 0))), 2),
                    "lower": round(float(row.get("AutoARIMA-lo-95", row.get("AutoETS-lo-95", 0))), 2),
                    "upper": round(float(row.get("AutoARIMA-hi-95", row.get("AutoETS-hi-95", 0))), 2),
                })

            return {
                "model": "statsforecast",
                "forecast": forecast_list,
                "historical": series.to_dict(orient="records") if include_history else [],
                "forecast_periods": periods,
            }

        except Exception:
            return self._simple_forecast(df, target_col, periods)

    def _simple_forecast(
        self, df: pd.DataFrame, target_col: str, periods: int,
    ) -> dict[str, Any]:
        values = df[target_col].dropna()
        if len(values) == 0:
            return {"model": "simple", "forecast": [], "error": "No numeric data for forecasting"}

        last_val = float(values.iloc[-1])
        mean_val = float(values.mean())
        std_val = float(values.std()) if len(values) > 1 else last_val * 0.1

        sma_window = min(3, len(values))
        sma_vals = values.rolling(window=sma_window, min_periods=1).mean()
        sma_last = float(sma_vals.iloc[-1])

        ewma = values.ewm(span=min(3, len(values)), adjust=False).mean()
        ewma_last = float(ewma.iloc[-1])

        recent_trend = 0.0
        if len(values) >= 3:
            recent = values.iloc[-3:]
            x = np.arange(len(recent))
            slope, _ = np.polyfit(x, recent.values, 1)
            recent_trend = float(slope)

        forecast_list = []
        last_date = datetime.now()
        for i in range(periods):
            pred = sma_last * (1 + 0.02 * (i + 1)) if recent_trend > 0 else sma_last * (1 - 0.01 * (i + 1))
            fc_date = last_date + timedelta(days=i + 1)
            forecast_list.append({
                "date": fc_date.strftime("%Y-%m-%d"),
                "predicted": round(pred, 2),
                "lower": round(pred - std_val * 1.5, 2),
                "upper": round(pred + std_val * 1.5, 2),
            })

        return {
            "model": "simple_moving_average",
            "last_value": round(last_val, 2),
            "sma_3": round(sma_last, 2),
            "ewma": round(ewma_last, 2),
            "recent_trend": round(recent_trend, 2),
            "forecast": forecast_list,
            "forecast_periods": periods,
        }

    def _find_date_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            cl = str(col).lower()
            if any(kw in cl for kw in ("date", "time", "ngày", "tháng")):
                return col
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                return col
        return df.columns[0]

    def _find_numeric_column(self, df: pd.DataFrame, exclude: str = "") -> str:
        for col in df.columns:
            if col == exclude:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                return col
        return df.columns[1] if len(df.columns) > 1 else df.columns[0]
