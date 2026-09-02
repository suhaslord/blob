#!/usr/bin/env python3
"""Leakage-safe threshold calibration for anomaly scores.

Designed as a small follow-up experiment around TranAD+/DSN:
- Tune a threshold on calibration data only.
- Never tune on the held-out evaluation/test labels.
- If calibration labels are available, optimize F1 over candidate thresholds.
- If labels are unavailable, use a configurable high quantile.

Inputs are 1-D NumPy .npy arrays.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np


def _as_1d(path: str) -> np.ndarray:
    arr = np.asarray(np.load(path), dtype=float).reshape(-1)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{path} contains NaN or infinite values")
    return arr


def metrics(scores: np.ndarray, labels: np.ndarray, threshold: float) -> dict[str, float]:
    pred = scores >= threshold
    truth = labels.astype(bool)
    tp = int(np.sum(pred & truth))
    fp = int(np.sum(pred & ~truth))
    fn = int(np.sum(~pred & truth))
    tn = int(np.sum(~pred & ~truth))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "threshold": float(threshold),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


def calibrate_supervised(scores: np.ndarray, labels: np.ndarray, candidates: int = 400) -> tuple[float, dict]:
    if len(scores) != len(labels):
        raise ValueError("calibration scores and labels must have equal length")
    labels = labels.astype(int)
    if not set(np.unique(labels)).issubset({0, 1}):
        raise ValueError("labels must contain only 0/1")
    qs = np.linspace(0.50, 0.9995, candidates)
    thresholds = np.unique(np.quantile(scores, qs))
    best = None
    for t in thresholds:
        result = metrics(scores, labels, float(t))
        # Deterministic tie-break: higher F1, then higher recall, then lower threshold.
        key = (result["f1"], result["recall"], -result["threshold"])
        if best is None or key > best[0]:
            best = (key, result)
    assert best is not None
    return float(best[1]["threshold"]), best[1]


def calibrate_unsupervised(scores: np.ndarray, quantile: float = 0.995) -> tuple[float, dict]:
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must be in (0, 1)")
    threshold = float(np.quantile(scores, quantile))
    return threshold, {
        "threshold": threshold,
        "method": "unsupervised_quantile",
        "quantile": quantile,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cal-scores", required=True, help="Calibration anomaly scores (.npy)")
    p.add_argument("--cal-labels", help="Optional calibration 0/1 labels (.npy)")
    p.add_argument("--eval-scores", help="Optional held-out evaluation scores (.npy)")
    p.add_argument("--eval-labels", help="Optional held-out evaluation labels (.npy)")
    p.add_argument("--quantile", type=float, default=0.995)
    p.add_argument("--out", default="threshold_calibration.json")
    args = p.parse_args()

    cal_scores = _as_1d(args.cal_scores)
    if args.cal_labels:
        cal_labels = _as_1d(args.cal_labels).astype(int)
        threshold, calibration = calibrate_supervised(cal_scores, cal_labels)
        method = "supervised_calibration_f1"
    else:
        threshold, calibration = calibrate_unsupervised(cal_scores, args.quantile)
        method = "unsupervised_quantile"

    report = {
        "method": method,
        "threshold": threshold,
        "calibration": calibration,
        "leakage_guard": "threshold selected using calibration split only",
    }

    if bool(args.eval_scores) != bool(args.eval_labels):
        raise ValueError("--eval-scores and --eval-labels must be supplied together")

    if args.eval_scores:
        eval_scores = _as_1d(args.eval_scores)
        eval_labels = _as_1d(args.eval_labels).astype(int)
        if len(eval_scores) != len(eval_labels):
            raise ValueError("evaluation scores and labels must have equal length")
        report["held_out_evaluation"] = metrics(eval_scores, eval_labels, threshold)

    Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
