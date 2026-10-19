from __future__ import annotations

import math

import pandas as pd


class Metrics:
    def generate(self, history: list[dict[str, object]]) -> dict[str, object]:
        curve = pd.DataFrame(history)
        if curve.empty:
            return {"equity_curve": curve, "summary": {}}

        curve = curve.sort_values("trade_date").reset_index(drop=True)
        curve["return"] = curve["total_asset"].pct_change().fillna(0.0)
        curve["cummax"] = curve["total_asset"].cummax()
        curve["drawdown"] = curve["total_asset"] / curve["cummax"] - 1

        total_return = curve["total_asset"].iloc[-1] / curve["total_asset"].iloc[0] - 1
        annual_return = (1 + total_return) ** (252 / max(len(curve), 1)) - 1
        volatility = curve["return"].std() * math.sqrt(252)
        sharpe = annual_return / volatility if volatility > 0 else 0.0

        summary = {
            "start_asset": float(curve["total_asset"].iloc[0]),
            "end_asset": float(curve["total_asset"].iloc[-1]),
            "total_return": float(total_return),
            "annual_return": float(annual_return),
            "max_drawdown": float(curve["drawdown"].min()),
            "sharpe": float(sharpe),
            "trading_days": int(len(curve)),
        }
        return {"equity_curve": curve, "summary": summary}
