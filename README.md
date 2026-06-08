# AQuant

AQuant is a local scaffold for an A-share AI factor quant trading system.

The initial implementation focuses on the strategy discussed in the design:

- Universe: CSI 300 (`000300.SH`) + CSI 500 (`000905.SH`)
- Signal: LightGBM factor score pipeline, with a deterministic heuristic fallback before training
- Rebalance: weekly
- Portfolio: Top 5, equal weight by default
- Risk: ST/suspension/limit-up/full-lot/single-position/kill-switch checks
- Execution: local backtest and paper gateway first; QMT gateway is intentionally a placeholder

## Quick start

Install dependencies:

```bash
python -m pip install -e ".[dev]"
```

Generate deterministic sample data:

```bash
python scripts/sync_sample_data.py --output data/sample --periods 260 --stock-count 10
```

Generate weekly Top 5 targets:

```bash
python scripts/predict_weekly.py --data data/sample --date 2023-12-29
```

Train a local LightGBM model:

```bash
python scripts/train_model.py \
  --data data/sample \
  --train-start 2023-01-02 \
  --train-end 2023-08-31 \
  --valid-start 2023-09-01 \
  --valid-end 2023-11-30 \
  --model-version sample-lgbm
```

Generate targets using the trained model:

```bash
python scripts/predict_weekly.py \
  --data data/sample \
  --date 2023-12-29 \
  --model data/models/sample-lgbm.joblib
```

Run a sample backtest:

```bash
python scripts/run_backtest.py --data data/sample --start 2023-07-03 --end 2023-12-29
```

Run a sample backtest using the trained model:

```bash
python scripts/run_backtest.py \
  --data data/sample \
  --start 2023-07-03 \
  --end 2023-12-29 \
  --model data/models/sample-lgbm.joblib
```

Run tests:

```bash
python -m pytest
```

## Project layout

```text
configs/                 Strategy and system configuration
scripts/                 CLI utilities for sample data, prediction, backtest
src/aquant/core/         Domain types and config loader
src/aquant/data/         Local repository and sample data generator
src/aquant/factors/      Factor definitions and preprocessing
src/aquant/ml/           Dataset builder, LightGBM trainer, and prediction helpers
src/aquant/strategy/     Universe and portfolio construction
src/aquant/risk/         Risk checks and kill-switch logic
src/aquant/backtest/     Simple weekly rebalance backtester
src/aquant/trading/      Paper/QMT gateway abstractions
tests/                   Smoke tests for the MVP pipeline
```

## Notes

This repository is a first local implementation scaffold, not a production trading system yet.
Before using real capital, replace sample data with audited A-share data, implement the QMT gateway
inside the broker runtime, run extended backtests, and keep manual confirmation enabled.