from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aquant.data.repository import DataRepository
from aquant.data.sample import make_sample_daily_bars, make_sample_index_members


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic sample A-share data.")
    parser.add_argument("--output", default="data/sample", help="Output Parquet directory")
    parser.add_argument("--start", default="2023-01-02")
    parser.add_argument("--periods", type=int, default=260)
    parser.add_argument("--stock-count", type=int, default=10)
    args = parser.parse_args()

    bars = make_sample_daily_bars(
        start=args.start,
        periods=args.periods,
        stock_count=args.stock_count,
    )
    members = make_sample_index_members(bars)
    repo = DataRepository(bars, members, Path(args.output))
    repo.write_parquet()
    print(f"Wrote sample data to {args.output}")
    print(f"daily_bars={len(bars)} index_members={len(members)}")


if __name__ == "__main__":
    main()
