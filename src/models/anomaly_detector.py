from typing import Any
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self._scaler = StandardScaler()

    def detect(
        self,
        df: pd.DataFrame,
        columns: list[str] | None = None,
        method: str = "isolation_forest",
        return_scores: bool = True,
    ) -> dict[str, Any]:
        df = df.copy()

        if columns is None:
            columns = df.select_dtypes(include=["int64", "float64", "Int64", "Float64"]).columns.tolist()

        valid_cols = [c for c in columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
        if not valid_cols:
            return {"error": "No numeric columns for anomaly detection", "anomalies": [], "anomaly_count": 0}

        X = df[valid_cols].copy()
        na_mask = X.isnull().any(axis=1)
        for c in X.columns:
            X[c] = X[c].fillna(X[c].median())

        X_scaled = self._scaler.fit_transform(X)

        if method == "isolation_forest":
            model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100,
                max_samples="auto",
            )
            predictions = model.fit_predict(X_scaled)
            scores = model.decision_function(X_scaled)
        elif method == "lof":
            n_neighbors = min(20, max(2, len(X) // 5))
            model = LocalOutlierFactor(
                contamination=self.contamination,
                n_neighbors=n_neighbors,
                novelty=False,
            )
            predictions = model.fit_predict(X_scaled)
            scores = model.negative_outlier_factor_
        elif method == "zscore":
            z_scores = np.abs((X_scaled - X_scaled.mean(axis=0)) / max(X_scaled.std(axis=0).mean(), 0.0001))
            threshold = 3.0
            predictions = np.where(z_scores.max(axis=1) > threshold, -1, 1)
            scores = -z_scores.max(axis=1)
        elif method == "iqr":
            scores = np.zeros(len(X))
            predictions = np.ones(len(X), dtype=int)
            for i, col in enumerate(valid_cols):
                q1 = X[col].quantile(0.25)
                q3 = X[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = (X[col] < lower) | (X[col] > upper)
                predictions[outliers] = -1
                scores[outliers] -= 1
        else:
            return {"error": f"Unknown method: {method}", "anomalies": [], "anomaly_count": 0}

        anomaly_mask = predictions == -1
        df["_anomaly_score"] = scores
        df["_is_anomaly"] = anomaly_mask

        anomalies_df = df[anomaly_mask].drop(columns=["_anomaly_score", "_is_anomaly"], errors="ignore")

        anomaly_explanations = []
        for idx, row in anomalies_df.head(20).iterrows():
            explanations = []
            for col in valid_cols:
                col_median = X[col].median()
                val = row[col]
                if col_median != 0 and abs(val - col_median) / abs(col_median) > 0.5:
                    pct_diff = ((val - col_median) / col_median) * 100
                    direction = "cao hơn" if pct_diff > 0 else "thấp hơn"
                    explanations.append(
                        f"{col}: {self._fmt_num(val)} ({direction} {abs(pct_diff):.0f}% so với trung vị {self._fmt_num(col_median)})"
                    )
            anomaly_explanations.append({
                "row_index": int(idx) if isinstance(idx, (int, np.integer)) else str(idx),
                "values": {c: self._fmt_num(row[c]) if isinstance(row[c], (int, float, np.number)) else row[c]
                          for c in row.index if not c.startswith("_")},
                "explanation": "; ".join(explanations) if explanations else "Phát hiện bất thường tổng hợp",
            })

        return {
            "model": method,
            "total_rows": len(df),
            "anomaly_count": int(anomaly_mask.sum()),
            "anomaly_pct": round(float(anomaly_mask.sum() / max(len(df), 1) * 100), 2),
            "anomalies": anomalies_df.head(50).to_dict(orient="records"),
            "anomaly_explanations": anomaly_explanations,
            "columns_used": valid_cols,
        }

    def detect_time_series_anomalies(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        method: str = "rolling_zscore",
        window: int = 7,
        threshold: float = 3.0,
    ) -> dict[str, Any]:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col, value_col])
        df = df.sort_values(date_col)

        if len(df) < window + 1:
            return {"error": f"Need at least {window + 1} data points", "anomalies": [], "anomaly_count": 0}

        if method == "rolling_zscore":
            rolling_mean = df[value_col].rolling(window=window, center=False).mean()
            rolling_std = df[value_col].rolling(window=window, center=False).std()
            rolling_mean = rolling_mean.fillna(df[value_col].mean())
            rolling_std = rolling_std.fillna(df[value_col].std())

            z_scores = np.abs((df[value_col] - rolling_mean) / rolling_std.replace(0, 0.0001))
            anomaly_mask = z_scores > threshold

        elif method == "rolling_iqr":
            rolling_q1 = df[value_col].rolling(window=window).quantile(0.25)
            rolling_q3 = df[value_col].rolling(window=window).quantile(0.75)
            rolling_iqr = rolling_q3 - rolling_q1
            lower = rolling_q1 - 1.5 * rolling_iqr
            upper = rolling_q3 + 1.5 * rolling_iqr
            anomaly_mask = (df[value_col] < lower) | (df[value_col] > upper)

        elif method == "pct_change":
            pct_changes = df[value_col].pct_change().abs()
            anomaly_mask = pct_changes > (threshold / 100.0)

        else:
            return {"error": f"Unknown method: {method}", "anomalies": [], "anomaly_count": 0}

        anomalies_df = df[anomaly_mask]

        anomaly_entries = []
        for _, row in anomalies_df.iterrows():
            anomaly_entries.append({
                "date": str(row[date_col]),
                "value": self._fmt_num(row[value_col]),
            })

        return {
            "model": f"timeseries_{method}",
            "total_points": len(df),
            "anomaly_count": int(anomaly_mask.sum()),
            "anomaly_pct": round(float(anomaly_mask.sum() / max(len(df), 1) * 100), 2),
            "anomalies": anomaly_entries,
            "window": window,
            "threshold": threshold,
        }

    def _fmt_num(self, val: Any) -> float:
        if isinstance(val, (np.integer,)):
            return float(val)
        if isinstance(val, (int, float)):
            return round(val, 2)
        return val
