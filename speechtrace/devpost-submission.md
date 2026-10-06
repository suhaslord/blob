## Inspiration
Speech feedback is often hard to act on. “Work on pacing” leaves the speaker guessing which passage needs attention. SpeechTrace makes that feedback more specific: compare a recording to a reference, find a measurable difference, and listen to the exact moment before deciding what to change.

## What it does
SpeechTrace is a new Track C prototype built on October 6, 2026. It accepts reference audio, participant audio, and their shared transcript. The dashboard shows aligned energy curves, estimated word timestamps, detected regions with mathematical explanations, and a transparent reference-similarity rubric. Region and word buttons seek both recordings to matched positions. The complete analysis can be downloaded as JSON.

Fourteen paired examples cover two public-domain excerpts from John F. Kennedy’s 1961 inaugural address. Each has an unchanged control, an overall-volume control, a near-perfect local change, moderate and severe local volume changes, an inserted pause, and a pitch-preserving 1.8× tempo version. They use the same words. The mirrors are deliberately edited audio, not claims that JFK gave those altered performances.

Bundled results say **Precomputed example**. **Reanalyze recordings** runs the real backend. Custom uploads run through the same engine. Changing input hides stale results and cancels pending analysis.

## How it was built
The frontend is HTML, CSS and JavaScript. Vercel hosts it alongside a Python analysis function. NumPy extracts windowed FFT power, mel cepstra, RMS energy and relative pitch. A monotone dynamic-time-warping path aligns the acoustics. Pretrained Vosk/Kaldi constrained decoding provides word boundaries; ordered transcript matching avoids errors around repeated words.

Energy and pitch are normalized within each recording. The scoring rule is explicit: 40% energy, 40% pacing and 20% contour, with duration penalties for merged flagged intervals. Explanations include the observed delta, units, interval and overlapping words. This measures similarity to a reference, not a person’s inherent speaking ability or the quality of their argument.

The GitHub folder contains the complete code, all paired WAV files, transcripts, exact injected interval labels, estimated word alignments, audio hashes and computed results. The six-page technical report explains the architecture, dataset, rubric, evaluation and limitations. Source-download and transformation scripts make the dataset reproducible.

## Challenges and fixes
Repeated words initially produced a false pause in the held-out excerpt. Ordered sequence matching fixed that error. Invalid WAV data now produces a useful validation response. Rapidly uploading both recordings exposed another bug: one file’s preparation could cancel the other. Each upload now has independent preparation state, while analysis results are still guarded against stale responses.

## Results and verification
The small stress test contains 14 pairs, two excerpts and one speaker. The Power excerpt calibrated thresholds; Revolutionary Beliefs is a held-out excerpt from the same speaker. Four unchanged/global-gain controls produced no flags. Mean detected-interval IoU was 0.975 for moderate/severe volume edits and 0.815 for inserted pauses. Both rushed cases produced pacing flags. The near-perfect 5 dB edits stayed below threshold; that sensitivity limit is disclosed.

Five engine tests passed. Thirty-one browser checks passed locally, including real fresh analysis, overlapping uploads, stereo/44.1 kHz conversion, invalid files, stale responses, audio seeking, JSON export, clearing data, and four responsive widths. Thirty-two production browser checks also passed, including a clear fallback for non-JSON service errors. Four HTTP regression tests passed for chunked bodies, header casing, size limits and invalid uploads. Cold and warm Vercel API requests returned the same score and time interval; invalid WAV input returned HTTP 400.

## What the prototype still needs
More speakers, manually checked word boundaries and independent human evaluation would be needed before making broader accuracy or fairness claims. One historical speaker cannot validate cross-speaker generalization. Differences can be intentional. Pause boundaries may include adjacent natural silence, and noisy or mismatched transcripts can make alignment uncertain. Coverage warnings are shown rather than hidden. Cold model starts can take longer.

## Privacy and AI disclosure
Audio is converted in the browser, then sent with the transcript to the analysis function for that request. The app does not persist recordings or transcripts and does not log their contents. Ordinary hosting request metadata still exists. There is no database or account requirement.

Codex assisted with scoping, implementation, debugging, dataset transformations, tests, documentation and submission preparation. Vosk/Kaldi is pretrained; this project did not train a new acoustic model. Project code is MIT licensed. Public-domain audio source, attribution, hashes and modifications are recorded in the README and manifest.

## Deliverables
- Dashboard: https://speechtrace-lab.vercel.app
- Code, dataset and README: https://github.com/suhaslord/blob/tree/main/speechtrace
- Six-page technical report: https://speechtrace-lab.vercel.app/SpeechTrace-technical.pdf
- Dataset, rubric and evaluation: https://speechtrace-lab.vercel.app/docs.html
- Demo: the attached YouTube video shows source provenance, dataset construction, controls, stress tests, specific detected moments, and actual uploads and backend analysis.
