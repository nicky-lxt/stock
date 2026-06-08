from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd


def make_sample_daily_bars(
    start: str | date = "2024-01-01",
    periods: int = 90,
    stock_count: int = 8,
    seed: int = 7,
) -> pd.DataFrame:
    """Create deterministic A-share-like daily bars for local smoke tests."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start=start, periods=periods)
    codes = [f"000{i:03d}.SZ" for i in range(1, stock_count + 1)]
    rows: list[dict[str, object]] = []

    for code_idx, code in enumerate(codes):
        base_price = 10 + code_idx * 3
        drift = 0.0008 + code_idx * 0.00008
        noise = rng.normal(drift, 0.018, size=len(dates))
        closes = base_price * np.cumprod(1 + noise)
        opens = closes * (1 + rng.normal(0, 0.004, size=len(dates)))
        highs = np.maximum(opens, closes) * (1 + rng.uniform(0.002, 0.02, size=len(dates)))
        lows = np.minimum(opens, closes) * (1 - rng.uniform(0.002, 0.02, size=len(dates)))
        amounts = rng.uniform(250_000_000, 1_200_000_000, size=len(dates))
        volumes = amounts / closes * 100

        for i, trade_date in enumerate(dates):
            pre_close = closes[i - 1] if i > 0 else closes[i] / (1 + noise[i])
            pct_chg = closes[i] / pre_close - 1
            rows.append(
                {
                    "trade_date": trade_date.date(),
                    "ts_code": code,
                    "open": round(float(opens[i]), 4),
                    "high": round(float(highs[i]), 4),
                    "low": round(float(lows[i]), 4),
                    "close": round(float(closes[i]), 4),
                    "pre_close": round(float(pre_close), 4),
                    "volume": round(float(volumes[i]), 2),
                    "amount": round(float(amounts[i]), 2),
                    "adj_factor": 1.0,
                    "is_suspended": False,
                    "is_limit_up": pct_chg >= 0.095,
                    "is_limit_down": pct_chg <= -0.095,
                    "is_st": False,
                    "list_date": pd.Timestamp("2020-01-01").date(),
                    "industry": f"industry_{code_idx % 3}",
                    "market_cap": float(10_000_000_000 + code_idx * 800_000_000),
                }
            )

    return pd.DataFrame(rows)


def make_sample_index_members(bars: pd.DataFrame) -> pd.DataFrame:
    codes = sorted(bars["ts_code"].unique())
    split = max(1, len(codes) // 2)
    rows = []
    for index_code, index_codes in {
        "000300.SH": codes[:split],
        "000905.SH": codes[split:],
    }.items():
        for code in index_codes:
            rows.append(
                {
                    "index_code": index_code,
                    "ts_code": code,
                    "in_date": bars["trade_date"].min(),
                    "out_date": None,
                    "weight": 1.0 / len(index_codes),
                }
            )
    return pd.DataFrame(rows)
