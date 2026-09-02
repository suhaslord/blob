# Open-source contribution handoff — September 2026

This branch is a public, permanent handoff for contribution artifacts whose upstream repositories are readable but not writable through the connected GitHub integration.

## MMGIS #963

Target: `NASA-AMMOS/MMGIS` development branch.

- `mmgis/mmgis_issue_963_current.patch` — documentation + OpenAPI mutual-requirement fix for `/api/configure/upsert`.
- `mmgis/VALIDATION.txt` — validation evidence and exact base SHA.

The patch was regenerated against MMGIS development `793dc05b55f7654e3a345eaff42120aa3bae3e25` and passed `git apply --check` against the current snippets. It preserves `mission` as required and adds an OpenAPI `anyOf` requiring either `config` or `version`.

## AlpaSim speed-limit metric

Target: `NVlabs/alpasim` main branch.

- `alpasim/alpasim_speed_limit_metric_current.patch` — opt-in configured speed-limit scorer, schema/registration/config wiring, and repo-style tests.
- `alpasim/VALIDATION.txt` — validation evidence and exact base SHA.

The implementation deliberately does not infer a posted limit from `trajdata.RoadLane`, because the current lane schema has no posted-speed field. The scorer is disabled by default and accepts an explicit `speed_limit_mps` until AlpaSim defines a canonical automatic source.

## TranAD+ / DSN thresholding

- `dsn/tranadplus_score_export.patch` — adds an opt-in raw score/label export after the selected POT alpha is frozen.
- `dsn/tranad_dsn_threshold_calibration.py` — leakage-safe held-out threshold calibration utility.

The public DSN_1k checkpoint is available. The public OSF project has three files: `drs.pkl`, `README.Rmd`, and a 3.70 GB `mons.pkl`; the upstream DSN loader imports that large pickle in its entirety, so a full inference run requires an environment with enough memory for the deserialized pandas objects.

These files are review/handoff artifacts, not claims that upstream PRs exist where the upstream repositories remain read-only to this GitHub integration.
