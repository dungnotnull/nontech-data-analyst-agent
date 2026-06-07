from typing import Any
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


class Segmenter:
    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        self._scaler = StandardScaler()

    def segment(
        self,
        df: pd.DataFrame,
        features: list[str] | None = None,
        method: str = "kmeans",
        labels: dict[int, str] | None = None,
        normalize: bool = True,
    ) -> dict[str, Any]:
        df = df.copy()

        if features is None:
            features = df.select_dtypes(include=["int64", "float64", "Int64", "Float64"]).columns.tolist()

        valid_features = [f for f in features if f in df.columns and pd.api.types.is_numeric_dtype(df[f])]
        if len(valid_features) < 2:
            return {"error": "Need at least 2 numeric features for segmentation", "segments": [], "k": 0}

        X = df[valid_features].copy()
        id_col = self._find_id_column(df, valid_features)
        ids = df[id_col].values if id_col else df.index.values

        for c in X.columns:
            X[c] = X[c].fillna(X[c].median())

        if normalize:
            X_scaled = self._scaler.fit_transform(X)
        else:
            X_scaled = X.values

        if method == "kmeans":
            result = self._kmeans_cluster(X_scaled, X, valid_features, ids, labels)
        elif method == "dbscan":
            result = self._dbscan_cluster(X_scaled, X, valid_features, ids)
        elif method == "rfm":
            result = self._rfm_cluster(df, ids)
        elif method == "auto":
            result = self._kmeans_cluster(X_scaled, X, valid_features, ids, labels)
        else:
            return {"error": f"Unknown method: {method}", "segments": [], "k": 0}

        return result

    def _kmeans_cluster(
        self, X_scaled: np.ndarray, X: pd.DataFrame,
        features: list[str], ids: np.ndarray,
        custom_labels: dict[int, str] | None,
    ) -> dict[str, Any]:
        k_candidates = list(range(2, min(9, len(X) // 2 + 1)))
        if not k_candidates:
            k_candidates = [2]

        best_k = self.n_clusters
        best_score = -1
        for k in k_candidates:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels_pred = km.fit_predict(X_scaled)
            if len(set(labels_pred)) > 1:
                score = silhouette_score(X_scaled, labels_pred)
                if score > best_score:
                    best_score = score
                    best_k = k

        final_k = min(best_k, len(X) - 1)
        final_k = max(final_k, 2)

        model = KMeans(n_clusters=final_k, random_state=42, n_init=10)
        cluster_labels = model.fit_predict(X_scaled)

        centroids = pd.DataFrame(
            self._scaler.inverse_transform(model.cluster_centers_),
            columns=features,
        )

        segments = []
        segment_sizes = pd.Series(cluster_labels).value_counts().sort_index()

        for i in range(final_k):
            size = int(segment_sizes.get(i, 0))
            centroid = {}
            for col in features:
                centroid[col] = round(float(centroids.loc[i, col]), 2)

            pct = round(float(size / len(X) * 100), 2)

            if custom_labels and i in custom_labels:
                seg_label = custom_labels[i]
            else:
                seg_label = self._auto_label_segment(i, centroid, X, cluster_labels, features)

            segments.append({
                "cluster_id": int(i),
                "label": seg_label,
                "size": size,
                "pct": pct,
                "centroid": centroid,
            })

        return {
            "model": "kmeans",
            "k": final_k,
            "silhouette_score": round(float(best_score), 4),
            "total_rows": len(X),
            "features_used": features,
            "segments": sorted(segments, key=lambda s: s["size"], reverse=True),
        }

    def _dbscan_cluster(
        self, X_scaled: np.ndarray, X: pd.DataFrame,
        features: list[str], ids: np.ndarray,
    ) -> dict[str, Any]:
        eps = np.percentile(
            np.sort(np.abs(X_scaled - X_scaled.mean(axis=0)).max(axis=1)),
            75,
        )
        eps = max(eps, 0.1)

        min_samples = max(2, min(5, len(X) // 20))

        model = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = model.fit_predict(X_scaled)

        unique_clusters = sorted(set(cluster_labels))
        noise_count = int((cluster_labels == -1).sum())

        segments = []
        for cid in unique_clusters:
            mask = cluster_labels == cid
            size = int(mask.sum())
            pct = round(float(size / len(X) * 100), 2)

            centroid = {}
            for col in features:
                centroid[col] = round(float(X.loc[mask, col].mean()), 2)

            if cid == -1:
                label = "Ngoại lệ / Noise"
            else:
                label = self._auto_label_segment(cid, centroid, X, cluster_labels, features)

            segments.append({
                "cluster_id": int(cid),
                "label": label,
                "size": size,
                "pct": pct,
                "centroid": centroid,
                "is_noise": cid == -1,
            })

        if noise_count == 0 or noise_count >= len(X):
            sil_score = 0.0
        else:
            non_noise = cluster_labels != -1
            if non_noise.sum() > 1 and len(set(cluster_labels[non_noise])) > 1:
                sil_score = silhouette_score(X_scaled[non_noise], cluster_labels[non_noise])
            else:
                sil_score = 0.0

        return {
            "model": "dbscan",
            "k": len(unique_clusters),
            "silhouette_score": round(float(sil_score), 4),
            "total_rows": len(X),
            "noise_count": noise_count,
            "eps": round(float(eps), 4),
            "features_used": features,
            "segments": sorted(segments, key=lambda s: s["size"], reverse=True),
        }

    def _rfm_cluster(
        self, df: pd.DataFrame, ids: np.ndarray,
    ) -> dict[str, Any]:
        date_col = self._find_date_col_rfm(df)
        value_col = self._find_value_col_rfm(df)
        id_col = self._find_id_column(df, [date_col, value_col] if date_col else [value_col])

        rfm = df.groupby(id_col).agg(
            recency_days=(date_col, lambda x: (pd.Timestamp.now() - pd.to_datetime(x).max()).days) if date_col else (id_col, lambda x: 0),
            frequency=(id_col, "count"),
            monetary=(value_col, "sum"),
        ).reset_index()

        rfm_cols = ["recency_days", "frequency", "monetary"]
        X = rfm[rfm_cols].copy()
        for c in X.columns:
            X[c] = X[c].fillna(X[c].median())

        X_norm = pd.DataFrame({
            "recency_score": pd.cut(X["recency_days"], bins=5, labels=[5, 4, 3, 2, 1]).astype(int),
            "frequency_score": pd.qcut(X["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int),
            "monetary_score": pd.qcut(X["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int),
        })

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_norm)

        k = min(4, len(X) - 1)
        k = max(k, 2)
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = model.fit_predict(X_scaled)

        rfm_labels = {0: "VIP/Champions", 1: "Trung thành", 2: "Có nguy cơ rời bỏ", 3: "Mới/Cần chăm sóc"}
        rfm_labels.update({i: f"Nhóm {i+1}" for i in range(4, 10)})

        segments = []
        sizes = pd.Series(cluster_labels).value_counts().sort_index()
        for i in range(k):
            mask = cluster_labels == i
            size = int(sizes.get(i, 0))
            centroid = {
                "recency_score": round(float(X_norm.loc[mask, "recency_score"].mean()), 2),
                "frequency_score": round(float(X_norm.loc[mask, "frequency_score"].mean()), 2),
                "monetary_score": round(float(X_norm.loc[mask, "monetary_score"].mean()), 2),
                "avg_recency_days": round(float(X.loc[mask, "recency_days"].mean()), 1),
                "avg_frequency": round(float(X.loc[mask, "frequency"].mean()), 1),
                "avg_monetary": round(float(X.loc[mask, "monetary"].mean()), 2),
            }
            segments.append({
                "cluster_id": int(i),
                "label": rfm_labels.get(i, f"Nhóm {i+1}"),
                "size": size,
                "pct": round(float(size / len(X) * 100), 2),
                "centroid": centroid,
            })

        return {
            "model": "rfm",
            "k": k,
            "total_rows": len(X),
            "features_used": rfm_cols,
            "segments": sorted(segments, key=lambda s: s["size"], reverse=True),
        }

    def _auto_label_segment(
        self, cid: int, centroid: dict, X: pd.DataFrame,
        labels: np.ndarray, features: list[str],
    ) -> str:
        mask = labels == cid
        if mask.sum() == 0:
            return f"Nhóm {cid + 1}"

        total_means = {col: float(X[col].mean()) for col in features}
        scores = {}
        for col in features:
            cval = centroid.get(col, 0)
            tmean = total_means.get(col, 1)
            if tmean != 0:
                scores[col] = cval / tmean

        avg_score = np.mean(list(scores.values())) if scores else 1.0
        max_col = max(scores, key=scores.get)
        min_col = min(scores, key=scores.get)

        if avg_score > 1.3:
            return f"VIP - {max_col} cao"
        elif avg_score > 1.05:
            return f"Trên trung bình"
        elif avg_score < 0.7:
            return f"Thấp - {min_col} thấp"
        elif avg_score < 0.9:
            return f"Dưới trung bình"
        return f"Nhóm {cid + 1}"

    def _find_id_column(self, df: pd.DataFrame, exclude: list[str]) -> str | None:
        for col in df.columns:
            if col in exclude:
                continue
            cl = str(col).lower()
            if any(kw in cl for kw in ("name", "id", "customer", "product", "tên", "mã", "khách", "sản phẩm")):
                return col
        for col in df.columns:
            if col in exclude:
                continue
            if df[col].dtype == "object" and df[col].nunique() > 1:
                return col
        return None

    def _find_date_col_rfm(self, df: pd.DataFrame) -> str | None:
        for col in df.columns:
            cl = str(col).lower()
            if any(kw in cl for kw in ("date", "time", "ngày", "order", "transaction")):
                return col
        return None

    def _find_value_col_rfm(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            cl = str(col).lower()
            if any(kw in cl for kw in ("revenue", "amount", "value", "doanh", "tiền", "total", "giá")):
                return col
        numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
        return numeric_cols[0] if len(numeric_cols) > 0 else df.columns[0]

    def suggest_k(self, X: np.ndarray, max_k: int = 10) -> int:
        max_k = min(max_k, len(X) - 1)
        if max_k < 2:
            return 2

        inertias = []
        sil_scores = []
        for k in range(2, max_k + 1):
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(X)
            inertias.append(km.inertia_)
            if len(set(labels)) > 1:
                sil_scores.append(silhouette_score(X, labels))
            else:
                sil_scores.append(0)

        if sil_scores:
            best_sil_k = sil_scores.index(max(sil_scores)) + 2
            return best_sil_k
        return 3
