from typing import Any
import pandas as pd
import numpy as np


ANALYSIS_TEMPLATES: dict[str, str] = {
    "ranking": """
import pandas as pd
import numpy as np

_df = df.copy()
_metric_col = '{metric_col}'
_dim_col = '{dimension_col}'
_top_n = {top_n}
_sort_order = '{sort_order}'

_dates_parsed = False
for _col in _df.columns:
    if 'date' in str(_col).lower() or 'time' in str(_col).lower() or 'ngày' in str(_col).lower() or 'tháng' in str(_col).lower():
        try:
            _df[_col] = pd.to_datetime(_df[_col], errors='coerce')
            _dates_parsed = True
        except Exception:
            pass

_numeric_cols = _df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64']).columns.tolist()
if _metric_col not in _numeric_cols:
    for _nc in _numeric_cols:
        if _nc not in ('Unnamed',) and not _nc.startswith('Unnamed'):
            _metric_col = _nc
            break

if _dim_col is None or _dim_col == '' or _dim_col not in _df.columns:
    _text_cols = _df.select_dtypes(include=['object']).columns.tolist()
    if _text_cols:
        _dim_col = _text_cols[0]
    else:
        _dim_col = _df.columns[0]

_df = _df.dropna(subset=[_metric_col])
_agg = _df.groupby(_dim_col)[_metric_col].sum().reset_index()
_ascending = _sort_order == 'asc'
_result = _agg.sort_values(by=_metric_col, ascending=_ascending).head(_top_n)
_result.columns = ['dimension', 'value']
result = __result__ = _result
""",
    "trend": """
import pandas as pd
import numpy as np

_df = df.copy()
_metric_col = '{metric_col}'
_date_col = '{time_column}'

if _date_col is None or _date_col == '' or _date_col not in _df.columns:
    for _col in _df.columns:
        _cl = str(_col).lower()
        if 'date' in _cl or 'time' in _cl or 'ngày' in _cl or 'tháng' in _cl:
            _date_col = _col
            break
    if _date_col is None or _date_col not in _df.columns:
        _date_col = _df.columns[0]

_df[_date_col] = pd.to_datetime(_df[_date_col], errors='coerce')
_df = _df.dropna(subset=[_date_col])

_numeric_cols = _df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64']).columns.tolist()
if _metric_col not in _numeric_cols:
    for _nc in _numeric_cols:
        _metric_col = _nc
        break

_df = _df.dropna(subset=[_metric_col])

_timespan = (_df[_date_col].max() - _df[_date_col].min()).days
if _timespan > 365 * 2:
    _freq = 'Q'
elif _timespan > 180:
    _freq = 'M'
elif _timespan > 60:
    _freq = 'W'
else:
    _freq = 'D'

_result = _df.set_index(_date_col).resample(_freq)[_metric_col].sum().reset_index()
_result.columns = ['date', 'value']
result = __result__ = _result
""",
    "comparison": """
import pandas as pd
import numpy as np

_df = df.copy()
_metric_col = '{metric_col}'
_dim_col = '{dimension_col}'

_numeric_cols = _df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64']).columns.tolist()
if _metric_col not in _numeric_cols:
    for _nc in _numeric_cols:
        _metric_col = _nc
        break

if _dim_col is None or _dim_col == '' or _dim_col not in _df.columns:
    _text_cols = _df.select_dtypes(include=['object']).columns.tolist()
    _dim_col = _text_cols[0] if _text_cols else _df.columns[0]

_df = _df.dropna(subset=[_metric_col])
_result = _df.groupby(_dim_col).agg(
    total=pd.NamedAgg(column=_metric_col, aggfunc='sum'),
    average=pd.NamedAgg(column=_metric_col, aggfunc='mean'),
    count=pd.NamedAgg(column=_metric_col, aggfunc='count'),
).reset_index()
_result = _result.sort_values(by='total', ascending=False)
result = __result__ = _result
""",
    "distribution": """
import pandas as pd
import numpy as np

_df = df.copy()
_metric_col = '{metric_col}'

_numeric_cols = _df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64']).columns.tolist()
if _metric_col not in _numeric_cols:
    _metric_col = _numeric_cols[0] if _numeric_cols else _df.columns[0]

_data = _df[_metric_col].dropna()
_stats = {{
    'count': int(len(_data)),
    'mean': float(_data.mean()),
    'median': float(_data.median()),
    'std': float(_data.std()),
    'min': float(_data.min()),
    'max': float(_data.max()),
    'q25': float(_data.quantile(0.25)),
    'q75': float(_data.quantile(0.75)),
}}
result = __result__ = _stats
""",
    "anomaly": """
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

_df = df.copy()

_numeric_cols = _df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64']).columns.tolist()
if not _numeric_cols:
    result = {{'error': 'No numeric columns for anomaly detection', 'anomalies': []}}
    __result__ = result
else:
    _X = _df[_numeric_cols].copy()
    for _c in _X.columns:
        _X[_c] = _X[_c].fillna(_X[_c].median())
    _model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
    _preds = _model.fit_predict(_X)
    _df['_anomaly_score'] = _model.decision_function(_X)
    _df['_is_anomaly'] = _preds == -1
    _anomalies = _df[_df['_is_anomaly']].drop(columns=['_anomaly_score', '_is_anomaly'])
    result = {{
        'total_rows': len(_df),
        'anomaly_count': int(_anomalies.shape[0]),
        'anomaly_pct': round(float(_anomalies.shape[0] / max(len(_df), 1) * 100), 2),
        'anomalies': _anomalies.head(50).to_dict(orient='records'),
    }}
    __result__ = result
""",
    "profitability": """
import pandas as pd
import numpy as np

_df = df.copy()
_revenue_cols = []
_cost_cols = []
for _c in _df.columns:
    _cl = str(_c).lower()
    if any(_kw in _cl for _kw in ['revenue', 'sales', 'income', 'doanh', 'bán', 'thu']):
        _revenue_cols.append(_c)
    if any(_kw in _cl for _kw in ['cost', 'expense', 'chi phí', 'phí', 'giá vốn', 'cogs', 'mua']):
        _cost_cols.append(_c)

_numeric_cols = _df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64']).columns.tolist()
if not _revenue_cols and _numeric_cols:
    _revenue_cols = [_numeric_cols[0]]
if not _cost_cols and len(_numeric_cols) >= 2:
    _cost_cols = [_numeric_cols[-1]]

_dim_col = '{dimension_col}'
if not _dim_col or _dim_col not in _df.columns:
    _text_cols = _df.select_dtypes(include=['object']).columns.tolist()
    _dim_col = _text_cols[0] if _text_cols else None

_rev_col = _revenue_cols[0] if _revenue_cols else (_numeric_cols[0] if _numeric_cols else _df.columns[0])
_cost_col = _cost_cols[0] if _cost_cols else (_numeric_cols[-1] if len(_numeric_cols) >= 2 else _rev_col)

_df = _df.dropna(subset=[_rev_col])
if _dim_col:
    _result = _df.groupby(_dim_col).agg(
        total_revenue=pd.NamedAgg(column=_rev_col, aggfunc='sum'),
        total_cost=pd.NamedAgg(column=_cost_col, aggfunc='sum'),
    ).reset_index()
    _result['profit'] = _result['total_revenue'] - _result['total_cost']
    _result['margin_pct'] = (_result['profit'] / _result['total_revenue'].replace(0, np.nan) * 100).round(2)
    _result = _result.sort_values(by='profit', ascending=False)
else:
    _total_rev = float(_df[_rev_col].sum())
    _total_cost = float(_df[_cost_col].sum())
    _profit = _total_rev - _total_cost
    _margin = (_profit / _total_rev * 100) if _total_rev != 0 else 0
    _result = pd.DataFrame([{{
        'total_revenue': _total_rev,
        'total_cost': _total_cost,
        'profit': _profit,
        'margin_pct': round(_margin, 2),
    }}])
result = __result__ = _result
""",
    "segmentation": """
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

_df = df.copy()
_numeric_cols = _df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64']).columns.tolist()
if len(_numeric_cols) < 2:
    result = {{'error': 'Need at least 2 numeric columns for segmentation', 'segments': []}}
    __result__ = result
else:
    _X = _df[_numeric_cols].copy()
    for _c in _X.columns:
        _X[_c] = _X[_c].fillna(_X[_c].median())
    _scaler = StandardScaler()
    _X_scaled = _scaler.fit_transform(_X)
    _k = min({n_clusters}, len(_df) - 1)
    _k = max(_k, 2)
    _model = KMeans(n_clusters=_k, random_state=42, n_init=10)
    _df['_cluster'] = _model.fit_predict(_X_scaled)
    _summary = _df.groupby('_cluster')[_numeric_cols].mean()
    _sizes = _df['_cluster'].value_counts().sort_index()
    _segments = []
    for _c in range(_k):
        _segments.append({{
            'cluster_id': int(_c),
            'size': int(_sizes.get(_c, 0)),
            'pct': round(float(_sizes.get(_c, 0) / len(_df) * 100), 2),
            'centroid': {{_nc: round(float(_summary.loc[_c, _nc]), 2) for _nc in _numeric_cols if _nc in _summary.columns}},
        }})
    result = {{
        'k': int(_k),
        'total_rows': int(len(_df)),
        'segments': _segments,
    }}
    __result__ = result
""",
    "forecast": """
import pandas as pd
import numpy as np

_df = df.copy()
_metric_col = '{metric_col}'
_date_col = '{time_column}'

if _date_col is None or _date_col == '' or _date_col not in _df.columns:
    for _col in _df.columns:
        _cl = str(_col).lower()
        if 'date' in _cl or 'time' in _cl or 'ngày' in _cl or 'tháng' in _cl:
            _date_col = _col
            break
    if _date_col is None or _date_col not in _df.columns:
        _date_col = _df.columns[0]

_numeric_cols = _df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64']).columns.tolist()
if _metric_col not in _numeric_cols:
    _metric_col = _numeric_cols[0] if _numeric_cols else _df.columns[0]

_df[_date_col] = pd.to_datetime(_df[_date_col], errors='coerce')
_df = _df.dropna(subset=[_date_col, _metric_col])
_agg = _df.groupby(_df[_date_col].dt.to_period('M').dt.to_timestamp()).agg(
    total=pd.NamedAgg(column=_metric_col, aggfunc='sum'),
    avg=pd.NamedAgg(column=_metric_col, aggfunc='mean'),
).reset_index()
_agg.columns = ['date', 'total', 'avg']

try:
    from prophet import Prophet
    _prophet_df = _agg[['date', 'total']].rename(columns={{'date': 'ds', 'total': 'y'}})
    _prophet_df = _prophet_df.dropna()
    if len(_prophet_df) >= 5:
        _model = Prophet(weekly_seasonality=True, yearly_seasonality=True, daily_seasonality=False)
        _model.fit(_prophet_df)
        _future = _model.make_future_dataframe(periods={forecast_periods}, freq='D')
        _forecast = _model.predict(_future)
        _forecast_result = _forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail({forecast_periods})
        result = {{
            'model': 'prophet',
            'historical': _agg.to_dict(orient='records'),
            'forecast': _forecast_result.rename(columns={{'ds': 'date', 'yhat': 'predicted', 'yhat_lower': 'lower', 'yhat_upper': 'upper'}}).to_dict(orient='records'),
        }}
    else:
        result = {{'model': 'simple_moving_average', 'error': 'Not enough data for Prophet, using SMA'}}
except Exception as _e:
    _sma = _agg['total'].rolling(window=3, min_periods=1).mean().iloc[-1]
    result = {{
        'model': 'simple_moving_average',
        'last_value': float(_agg['total'].iloc[-1]),
        'sma_3': float(_sma),
        'error': str(_e),
    }}
__result__ = result
""",
    "summary": """
import pandas as pd
import numpy as np

_df = df.copy()
_total_rows = len(_df)
_numeric_cols = _df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64']).columns.tolist()
_text_cols = _df.select_dtypes(include=['object']).columns.tolist()
_date_cols = _df.select_dtypes(include=['datetime64']).columns.tolist()

_stats = {{}}
for _c in _numeric_cols:
    _s = _df[_c].dropna()
    if len(_s) > 0:
        _stats[_c] = {{
            'min': float(_s.min()),
            'max': float(_s.max()),
            'mean': float(_s.mean()),
            'median': float(_s.median()),
            'sum': float(_s.sum()),
            'missing': int(_df[_c].isnull().sum()),
        }}

_uniques = {{}}
for _c in _text_cols:
    _uniques[_c] = int(_df[_c].nunique())

_date_range = None
if _date_cols:
    _dmin = _df[_date_cols[0]].min()
    _dmax = _df[_date_cols[0]].max()
    _date_range = {{'min': str(_dmin), 'max': str(_dmax), 'span_days': (_dmax - _dmin).days}}

result = {{
    'total_rows': _total_rows,
    'total_columns': len(_df.columns),
    'numeric_columns': _numeric_cols,
    'text_columns': _text_cols,
    'date_columns': _date_cols,
    'numeric_stats': _stats,
    'unique_counts': _uniques,
    'date_range': _date_range,
}}
__result__ = result
""",
}


class CodeGenerator:
    def __init__(self):
        self._template_cache: dict[str, str] = {}

    def generate(self, intent: dict, error_context: str | None = None) -> str:
        analysis_type = intent.get("analysis_type", "summary")
        template = ANALYSIS_TEMPLATES.get(analysis_type)
        if template is None:
            template = ANALYSIS_TEMPLATES["summary"]

        metric_col = self._resolve_metric_column(intent)
        time_col = intent.get("time_column", "")
        dim_col = intent.get("dimension_column", "")
        top_n = intent.get("top_n", 10)
        sort_order = intent.get("sort_order", "desc")
        n_clusters = intent.get("n_clusters", 3)
        forecast_periods = intent.get("forecast_periods", 90)

        code = template.format(
            metric_col=metric_col,
            time_column=time_col,
            dimension_col=dim_col,
            top_n=top_n,
            sort_order=sort_order,
            n_clusters=n_clusters,
            forecast_periods=forecast_periods,
        )

        if error_context:
            code = (
                "# Previous attempt error: " + error_context.replace("\n", " ") + "\n"
                "# Retrying with adjusted logic...\n" + code
            )

        return code

    def _resolve_metric_column(self, intent: dict) -> str:
        mc = intent.get("metric_column")
        if mc and mc.strip():
            return mc.strip()

        schema = intent.get("schema_context", {})
        suggested = schema.get("suggested_roles", {})
        for col, role in suggested.items():
            if role.startswith("metric"):
                return col
        cols = schema.get("columns", [])
        types = schema.get("column_types", {})
        for col in cols:
            if types.get(col) in ("numeric", "currency", "percentage"):
                return col
        return "revenue"


def generate_code_for_schema(
    intent: dict,
    schema: dict,
    error_context: str | None = None,
) -> str:
    generator = CodeGenerator()
    intent_with_schema = {**intent, "schema_context": schema}
    return generator.generate(intent_with_schema, error_context)
