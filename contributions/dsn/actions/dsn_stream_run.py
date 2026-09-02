#!/usr/bin/env python3
"""Memory-bounded DSN_1k TranAD+ checkpoint inference.

This reproduces the TranAD+ global anomaly-score definition while reducing each
batch from per-parameter MSE to a 1-D mean score immediately. That avoids
retaining multi-gigabyte prediction/loss tensors for the full DSN_1k dataset.

The public dff16/window-10 result used alpha=1.0, beta=0.0. Test tracks are
split at the track level (alternating sorted tracks) into calibration and final
held-out groups so threshold selection never sees held-out labels.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader


def _paths(directory: Path) -> list[str]:
    return [str(p) for p in sorted(directory.iterdir()) if p.is_file()]


def _stream_scores(model, dataloader, *, alpha: float, beta: float, device: str, include_labels: bool):
    score_chunks: list[np.ndarray] = []
    label_chunks: list[np.ndarray] = []
    model.eval()
    started = time.time()

    with torch.no_grad():
        for batch_idx, (windows, anoms_tmp) in enumerate(dataloader, start=1):
            # Match helpers.gen_TranAD_predictions exactly:
            # (batch, window, features) -> (window, batch, features)
            anoms_np = anoms_tmp.numpy()
            windows = windows.to(device).permute(1, 0, 2)
            elem = windows[-1, :, :].unsqueeze(0)
            x1, x2 = model(windows, elem)
            z = alpha * x1 + beta * x2

            # MSELoss(reduction='none')[0], then mean across parameters.
            loss_per_parameter = (z - elem).pow(2)[0]
            global_score = torch.mean(loss_per_parameter, dim=1)
            score_chunks.append(global_score.detach().cpu().numpy().astype(np.float32, copy=False))

            if include_labels:
                if dataloader.dataset.padding:
                    latest = anoms_np[:, -1, :]
                else:
                    latest = anoms_np[:, 0, :]
                label_chunks.append((np.sum(latest, axis=1) >= 1).astype(np.uint8))

            if batch_idx == 1 or batch_idx % 25 == 0:
                n = sum(len(x) for x in score_chunks)
                print(f"batch={batch_idx} samples={n} elapsed_s={time.time() - started:.1f}", flush=True)

            del windows, elem, x1, x2, z, loss_per_parameter, global_score

    scores = np.concatenate(score_chunks) if score_chunks else np.empty(0, dtype=np.float32)
    labels = (
        np.concatenate(label_chunks).astype(np.uint8, copy=False)
        if include_labels
        else np.empty(0, dtype=np.uint8)
    )
    return scores, labels


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--identifier", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--batch-size", type=int, default=2048)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    sys.path.insert(0, str(repo_root.parent))

    from TranADPlus.src import helpers, models  # noqa: E402
    from TranADPlus.src.datasets import TSDataset_tracks  # noqa: E402

    torch.manual_seed(1)
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    device = "cpu"

    checkpoint_path = repo_root / "Checkpoints" / f"{args.identifier}.ckpt"
    checkpoint = torch.load(checkpoint_path, map_location=device)
    hp = checkpoint["hp_dict"]

    if hp["dataset_str"] != "DSN_1k" or hp["model_str"] != "TranAD":
        raise RuntimeError(f"Unexpected checkpoint metadata: {hp}")
    if int(hp["features"]) != 129 or int(hp["window_sz"]) != 10:
        raise RuntimeError(f"Unexpected DSN checkpoint shape: {hp}")

    parsed_dff = helpers.parse_dim_feedforward(hp["features"], hp["dim_feedforward"])
    model = models.TranAD(
        n_feats=hp["features"],
        dim_feedforward=parsed_dff,
        batch_sz=hp["batch_sz"],
        window_sz=hp["window_sz"],
        num_encoder_layers=hp["num_layers"],
        num_decoder_layers=hp["num_layers"],
    ).to(device).to(torch.float32)
    model.load_state_dict(checkpoint["model_states"])
    model.eval()
    del checkpoint
    gc.collect()

    base = repo_root / "Datasets" / "Preprocessed" / "DSN_1k"
    train_tracks = _paths(base / "Train" / "Tracks")
    train_labels = _paths(base / "Train" / "Labels")
    test_tracks = _paths(base / "Test" / "Tracks")
    test_labels = _paths(base / "Test" / "Labels")

    if len(train_tracks) != len(train_labels):
        raise RuntimeError(f"Train track/label count mismatch: {len(train_tracks)} vs {len(train_labels)}")
    if len(test_tracks) != len(test_labels):
        raise RuntimeError(f"Test track/label count mismatch: {len(test_tracks)} vs {len(test_labels)}")
    if len(test_tracks) < 2:
        raise RuntimeError("Need at least two test tracks for track-level calibration/evaluation split")

    # Deterministic track-level split. Sorting + alternating prevents samples from
    # the same track from appearing in both threshold calibration and evaluation.
    paired_test = list(zip(test_tracks, test_labels))
    cal_pairs = paired_test[::2]
    eval_pairs = paired_test[1::2]

    runtime_batch = min(int(args.batch_size), int(hp["batch_sz"]))
    print(json.dumps({
        "hp_dict": {k: (v.item() if hasattr(v, "item") else v) for k, v in hp.items()},
        "runtime_batch_size": runtime_batch,
        "train_tracks": len(train_tracks),
        "calibration_tracks": len(cal_pairs),
        "held_out_tracks": len(eval_pairs),
        "alpha": 1.0,
        "beta": 0.0,
    }, indent=2), flush=True)

    # Train first to fit exactly one scaler. Then release the large train dataset
    # before materializing calibration or held-out test data.
    train_dataset = TSDataset_tracks(
        track_paths=train_tracks,
        anom_paths=train_labels,
        window_size=hp["window_sz"],
        padding=hp["padding"],
        scaling=True,
        downsample=hp["downsample"],
    )
    scaler = train_dataset.scaler
    train_loader = DataLoader(train_dataset, batch_size=runtime_batch, shuffle=False, num_workers=0)
    print(f"train_samples={len(train_dataset)}", flush=True)
    train_scores, _ = _stream_scores(model, train_loader, alpha=1.0, beta=0.0, device=device, include_labels=False)
    del train_loader, train_dataset
    gc.collect()

    cal_dataset = TSDataset_tracks(
        track_paths=[p[0] for p in cal_pairs],
        anom_paths=[p[1] for p in cal_pairs],
        window_size=hp["window_sz"],
        padding=hp["padding"],
        scaling=True,
        scaler=scaler,
        downsample=hp["downsample"],
    )
    cal_loader = DataLoader(cal_dataset, batch_size=runtime_batch, shuffle=False, num_workers=0)
    print(f"calibration_samples={len(cal_dataset)}", flush=True)
    cal_scores, cal_labels = _stream_scores(model, cal_loader, alpha=1.0, beta=0.0, device=device, include_labels=True)
    del cal_loader, cal_dataset
    gc.collect()

    eval_dataset = TSDataset_tracks(
        track_paths=[p[0] for p in eval_pairs],
        anom_paths=[p[1] for p in eval_pairs],
        window_size=hp["window_sz"],
        padding=hp["padding"],
        scaling=True,
        scaler=scaler,
        downsample=hp["downsample"],
    )
    eval_loader = DataLoader(eval_dataset, batch_size=runtime_batch, shuffle=False, num_workers=0)
    print(f"held_out_samples={len(eval_dataset)}", flush=True)
    eval_scores, eval_labels = _stream_scores(model, eval_loader, alpha=1.0, beta=0.0, device=device, include_labels=True)
    del eval_loader, eval_dataset
    gc.collect()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_path,
        train_scores_global=train_scores,
        calibration_scores_global=cal_scores,
        calibration_labels_global=cal_labels,
        held_out_scores_global=eval_scores,
        held_out_labels_global=eval_labels,
        alpha=np.float64(1.0),
        beta=np.float64(0.0),
        pot_q=np.float64(hp["pot_q"]),
        identifier=np.asarray(args.identifier),
        calibration_track_paths=np.asarray([Path(p[0]).name for p in cal_pairs]),
        held_out_track_paths=np.asarray([Path(p[0]).name for p in eval_pairs]),
    )

    manifest = {
        "identifier": args.identifier,
        "alpha": 1.0,
        "beta": 0.0,
        "runtime_batch_size": runtime_batch,
        "train_samples": int(train_scores.size),
        "calibration_samples": int(cal_scores.size),
        "held_out_samples": int(eval_scores.size),
        "calibration_anomalous_samples": int(cal_labels.sum()),
        "held_out_anomalous_samples": int(eval_labels.sum()),
        "calibration_tracks": [Path(p[0]).name for p in cal_pairs],
        "held_out_tracks": [Path(p[0]).name for p in eval_pairs],
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
