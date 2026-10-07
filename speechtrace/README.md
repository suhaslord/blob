# SpeechTrace

A new Multimodal AI Hackathon 2026 Track C project by Suhas Beemineni, built October 6, 2026. SpeechTrace compares a speech against a reference, highlights time-grounded acoustic deviations, and gives a reproducible reference-similarity rubric. It does not rate a person's inherent speaking ability or claim a fair replacement for human judges.

Live dashboard: https://speechtrace-lab.vercel.app

This directory contains the full submission, including the contrastive audio dataset. Other content in the repository is outside this project.

## Run and reproduce

Use Python 3.12: `pip install -r requirements.txt`, then `python dev-server.py`. Open http://localhost:4181. Run `python -m unittest qa/test_engine.py -v` and `python tools/evaluate.py`. The first alignment request downloads the official small English Vosk model to a temporary cache. Its SHA-256 is verified before extraction. A network connection is needed for that first download; there are no API keys.

Rebuild the contrastive dataset with `python tools/download_source.py` followed by `python tools/build_dataset.py`. To supply a previously downloaded full speech instead, run `python tools/build_dataset.py /path/to/speech.mp3`. FFmpeg is required for clipping and tempo changes. Source and model SHA-256 hashes are pinned in the scripts; the checked-in audio examples make the dashboard usable without rebuilding.

## Actual workflow

Choose one of 14 labeled comparisons or upload reference audio, participant audio and their shared transcript. The browser decodes and resamples audio to mono 16 kHz PCM WAV. The Python API validates clips, extracts features, performs acoustic time alignment and constrained word alignment, and returns scores, timeline data, estimated word boundaries and causal explanations. Click a region or word to seek both recordings to matched positions. Export the full result as JSON.

Example results are explicitly marked **Precomputed example**. Press **Reanalyze recordings** to run the current recordings through the actual backend. Custom uploads always use the backend. Changing input invalidates the result and aborts a pending request so late results cannot overwrite a new comparison.

## Dataset and rights

`public/data/dataset.json` is the manifest. It records source offsets, transcripts, audio hashes, transformation labels, exact injected flaw intervals, estimated baseline word alignment, and computed results. All paired WAV recordings are in `public/data/`.

The good reference is John F. Kennedy's January 20, 1961 inaugural address, credited to the John F. Kennedy Presidential Library & Museum. Two excerpts begin at 57.0 s and 70.2 s in the downloaded source. They are a historical reference, not a universal ideal performance.

Public-domain rights evidence:

- https://commons.wikimedia.org/wiki/File:JFK_inaugural_address.ogg
- https://archive.org/details/JohnF.KennedyInauguralAddress

Exact source: https://archive.org/download/JFK_Inaugural_Address_19610120/JFK_Inaugural_Address_19610120.mp3

SHA-256: `7a931ad726a9b732d8db01af6eaff55b9a34d42ee78f7ea73eba8533c3aa0e4d`

Each excerpt has an unchanged mirror, a whole-recording -10 dB gain control, a near-perfect -5 dB local edit, a moderate -14 dB edit, a severe -24 dB edit, an inserted 2-second pause, and a 1.8× pitch-preserving tempo mirror. These are digital modifications of the same transcript, not new human recordings or claims that JFK made those altered performances.

## Architecture, alignment and features

The static dashboard runs on Vercel with a Python `/api/analyze` function. NumPy implements the analysis; Vosk/Kaldi supplies a pretrained acoustic model. There is no database or persistent user profile.

Features use 25 ms frames and 20 ms hops: windowed FFT power, a 26-band mel filterbank, 12 DCT cepstral coefficients, RMS energy, and autocorrelation-based pitch. Cepstra are normalized per recording. Energy is relative to the recording's active-frame median; pitch is in semitones relative to that recording's median voiced pitch. This removes overall gain and pitch offsets but is not proof of cross-speaker generalization.

A monotone dynamic-time-warping path at 100 ms resolution aligns acoustic features. Vosk constrained sentence grammar decodes the supplied transcript and returns acoustic word boundaries. An ordered longest-common-subsequence match avoids confusing repeated words with spurious recognized tokens. Coverage and uncertainty are reported. Baseline word timestamps are machine estimates, not manually verified ground truth.

## Rubric and explainability

Energy deviations above 7 dB must persist for at least 400 ms. Contour deviations above 5 relative semitones require 700 ms of voiced frames. Acoustic progression and matched speech spans expose pacing shifts. Word gaps can flag extra pauses when all adjacent boundary confidences exceed 0.8; low-energy intervals provide independent pause evidence. Explanations show the underlying delta, unit and interval.

For each component, overlapping flagged intervals are merged. Component score = `max(0, 100 - 400 × flagged_duration / participant_duration)`. Total reference-similarity score = `0.4 × energy + 0.4 × pacing + 0.2 × contour`. A pause can affect both energy and pacing under this stated rubric. Differences can be artistically intentional; listen before changing delivery.

## Evaluation and testing

`public/data/evaluation.json` contains the exact per-case results. The Power excerpt calibrates the thresholds; Revolutionary Beliefs is a held-out excerpt from the same speaker. This is a small demonstration, not a general population benchmark.

- 14 paired cases, 2 excerpts, 1 speaker.
- 0 false-positive cases among 4 unchanged/global-gain controls.
- Mean interval IoU for moderate/severe volume edits: 0.975.
- Mean pause interval IoU: 0.815; one detection includes adjacent natural silence.
- Both 1.8× tempo mirrors have pacing flags.
- Both near-perfect 5 dB edits remain below threshold; this sensitivity limitation is deliberate and disclosed.

Tests check controls, severity ordering, injected interval overlap, pause and pacing detection, repeat-analysis consistency, and rejection of invalid/silent/wrong-rate WAV input. Four HTTP regression tests additionally check chunked uploads, header casing, request-size limits, and invalid JSON/base64. Browser and production checks are recorded in the submission audit.

## Privacy and operational limits

Uploaded audio is converted locally, then sent with the transcript to the analysis function for the current request. The application does not persist audio or transcript data and does not log request contents. Hosting infrastructure processes normal request metadata. Avoid confidential recordings.

Clips must be 1–32 seconds, PCM mono 16 kHz after browser conversion, with up to 120 English transcript words. Cold starts can take longer while the model downloads. Alignment can be uncertain with clipping, accents, different text, noise or severe delivery edits. One historical speaker is insufficient to validate cross-speaker fairness, biological normalization or competitive scoring. Content, argument quality and interpretation are not scored. No independent judge agreement or user adoption is claimed.

## AI and third-party disclosure

Codex assisted with scoping, implementation, debugging, data transformations, tests, documentation and submission preparation. The Vosk/Kaldi model is pretrained and was not trained by this team. Analytical thresholds were calibrated using the Power excerpt. Vosk API/model and NumPy retain their upstream licenses. Source code written for this project is MIT licensed. Public-domain audio attribution and modifications are disclosed above and in the dataset manifest.

## EurekaDev entry

Coding / Computer Science + AI. Judge walkthrough: https://speechtrace-lab.vercel.app/eureka.html. Originally built October 6 for Multimodal AI Track C and already submitted there. The October 7 release adds a tailored evaluation guide, with a proposed independent validation study clearly distinguished from completed work.
