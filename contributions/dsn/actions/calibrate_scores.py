#!/usr/bin/env python3
"""Leakage-resistant threshold calibration for streamed DSN_1k scores.

Threshold selection uses calibration-track labels only. Final F1 is reported on
separate held-out tracks. Both raw pointwise and TranAD+/OmniAnomaly-style
point-adjusted metrics are reported.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def counts_metrics(pred: np.ndarray, labels: np.ndarray) -> dict:
    pred = np.asarray(pred, dtype=bool)
    truth = np.asarray(labels, dtype=bool)
    tp = int(np.sum(pred & truth))
    tn = int(np.sum(~pred & ~truth))
    fp = int(np.sum(pred & ~truth))
    fn = int(np.sum(~pred & truth))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "f1": float(f1),
        "precision": float(precision),
        "recall": float(recall),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def anomaly_runs(labels: np.ndarray) -> list[tuple[int, int]]:
    x = np.asarray(labels, dtype=np.uint8)
    if x.size == 0:
        return []
    padded = np.concatenate(([0], x, [0]))
    d = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1) - 1
    return list(zip(starts.tolist(), ends.tolist()))


def adjusted_predictions(scores: np.ndarray, labels: np.ndarray, threshold: float) -> np.ndarray:
    # Match TranAD+/OmniAnomaly: score > threshold, then if any point in a
    # labeled anomaly region fires, mark the entire region detected.
    pred = np.asarray(scores) > threshold
    pred = pred.copy()
    for start, end in anomaly_runs(labels):
        if np.any(pred[start : end + 1]):
            pred[start : end + 1] = True
    return pred


def threshold_metrics(scores: np.ndarray, labels: np.ndarray, threshold: float) -> dict:
    point_pred = np.asarray(scores) > threshold
    adjusted_pred = adjusted_predictions(scores, labels, threshold)
    return {
        "threshold": float(threshold),
        "pointwise": counts_metrics(point_pred, labels),
        "point_adjusted": counts_metrics(adjusted_pred, labels),
    }


def calibrate(scores: np.ndarray, labels: np.ndarray, candidates: int = 500) -> tuple[float, dict]:
    if scores.size != labels.size:
        raise ValueError("calibration scores/labels length mismatch")
    if scores.size == 0:
        raise ValueError("empty calibration split")
    if not np.any(labels):
        raise ValueError("calibration split has no positive labels")

    qs = np.linspace(0.50, 0.9995, candidates)
    thresholds = np.unique(np.quantile(scores, qs))
    best_key = None
    best = None
    for threshold in thresholds:
        result = threshold_metrics(scores, labels, float(threshold))
        adjusted = result["point_adjusted"]
        key = (adjusted["f1"], adjusted["recall"], -float(threshold))
        if best_key is None or key > best_key:
            best_key = key
            best = result
    assert best is not None
    return float(best["threshold"]), best


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with np.load(args.scores, allow_pickle=False) as data:
        train_scores = np.asarray(data["train_scores_global"], dtype=np.float64)
        cal_scores = np.asarray(data["calibration_scores_global"], dtype=np.float64)
        cal_labels = np.asarray(data["calibration_labels_global"], dtype=np.uint8)
        eval_scores = np.asarray(data["held_out_scores_global"], dtype=np.float64)
        eval_labels = np.asarray(data["held_out_labels_global"], dtype=np.uint8)
        alpha = float(data["alpha"])
        beta = float(data["beta"])
        identifier = str(data["identifier"])

    threshold, calibration = calibrate(cal_scores, cal_labels)
    held_out = threshold_metrics(eval_scores, eval_labels, threshold)

    # Existing public POT artifact for this exact checkpoint.
    published_threshold = 0.0029835498576782607
    published = {
        "f1": 0.9247305754501705,
        "precision": 0.8653049287536468,
        "recall": 0.9929203325139087,
        "tp": 245577,
        "tn": 679068,
        "fp": 38227,
        "fn": 1751,
        "roc_auc": 0.9698135285416489,
        "threshold": published_threshold,
        "alpha": 1.0,
        "beta": 0.0,
    }

    full_scores = np.concatenate((cal_scores, eval_scores))
    full_labels = np.concatenate((cal_labels, eval_labels))
    published_threshold_reproduction = threshold_metrics(full_scores, full_labels, published_threshold)
    published_threshold_held_out = threshold_metrics(eval_scores, eval_labels, published_threshold)

    # Label-free reference using only training-score distribution.
    unsupervised_threshold = float(np.quantile(train_scores, 0.995))
    unsupervised_held_out = threshold_metrics(eval_scores, eval_labels, unsupervised_threshold)

    report = {
        "experiment": "DSN_1k track-level held-out threshold calibration",
        "identifier": identifier,
        "alpha": alpha,
        "beta": beta,
        "split_policy": "sorted test tracks alternated: even tracks calibration, odd tracks held out",
        "selection_guard": "threshold selected from calibration-track scores/labels only",
        "sizes": {
            "train_samples": int(train_scores.size),
            "calibration_samples": int(cal_scores.size),
            "held_out_samples": int(eval_scores.size),
            "calibration_positive_samples": int(cal_labels.sum()),
            "held_out_positive_samples": int(eval_labels.sum()),
        },
        "calibrated_threshold": float(threshold),
        "calibration_metrics": calibration,
        "held_out_metrics": held_out,
        "published_artifact": published,
        "published_threshold_recomputed_on_full_streamed_test": published_threshold_reproduction,
        "published_threshold_on_same_held_out_tracks": published_threshold_held_out,
        "unsupervised_train_q995_threshold": unsupervised_threshold,
        "unsupervised_train_q995_held_out": unsupervised_held_out,
        "held_out_adjusted_f1_delta_vs_published_threshold_same_tracks": float(
            held_out["point_adjusted"]["f1"] - published_threshold_held_out["point_adjusted"]["f1"]
        ),
        "note": "Only the held-out-track result is a leakage-resistant final comparison. Full-test published-threshold reproduction is a sanity check, not threshold selection.",
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
