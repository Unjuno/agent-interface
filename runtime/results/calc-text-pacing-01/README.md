# Explicit text pacing in Calc

The existing public text operation accepts `gap_ms`; no new runtime behavior or default is introduced here. A primary-agent compact trial had typed `477` but displayed `47`. These follow-ups test whether explicit pacing is a useful mitigation through the current implementation.

Source: c5b97fc5660f84f870f0d10abe20b1bcd4da69cc. Ubuntu 24.04.4, LibreOffice 24.2.7.2, Xvfb 21.1.12, python-xlib 0.33, Openbox; private application profile with SAL_USE_VCLPLUGIN=gen. No helper model. Each completed trial used a fresh X server/application, eight shared strings per interval in seeded shuffled order, and a fixed 100ms delay after each Return. Expected values were frozen before execution; saved XLSX values were read only after all inputs and saving.

| Route | gap ms | exact / 8 | median backend execution ms |
| --- | ---: | ---: | ---: |
| Backend execute, seed 991313 | 0 | 4 | 2.978 |
| Backend execute | 1 | 8 | 7.450 |
| Backend execute | 2 | 8 | 11.378 |
| Backend execute | 10 | 8 | 39.476 |
| Public API dispatch, held-out strings, seed 991314 | 0 | 4 | 1.319 |
| Public API dispatch | 1 | 8 | 7.472 |
| Public API dispatch | 2 | 8 | 14.927 |
| Public API dispatch | 10 | 8 | 38.886 |

All eight zero-gap mismatches involved adjacent repeated digits, including 477 -> 47 and held-out 688 -> 68. Every public dispatch returned completed, including the four incorrect saved values. Input emission completion is not text correctness. This reproduces the symptom without compact response presentation, but does not prove the mechanism of loss in the earlier primary trial.

Use an explicit interval when deliberately selecting pacing for this environment, e.g. `{"op":"text","text":"688","gap_ms":1}`, then inspect the result before relying on it. One millisecond succeeded in these small samples; it is not a universal minimum or guarantee. The existing compiler inserts only between-character waits; it does not wait for field selection, redraw, Return processing or save completion. Keep source/binding/lease checks and the expanded 128-operation bound.

Timings include backend focus, text, Return and release. They exclude row settling, saving, observation and model judgment. Public API wall timings are retained separately in rows.json. The API uses caller-owned source/lease assertions and opens a session per call; this is not a persistent MCP/model benchmark. Eight strings per arm, one session per route, sequential rows, fixed row settling and one application/backend limit generalization. No human-tempo, token, cost or useful-feedback-latency claim follows. No automatic retry or global pacing default is added.

The first setup attempt failed waiting for a filesystem X socket under WSLg. Its source/plan/failure remain in raw.tar.gz; the next attempt used the existing PrivateSession handshake and abstract socket support. The abandoned Xvfb process was terminated; completed trial fixture cleanup reports all processes stopped.

Run `python runtime/results/calc-text-pacing-01/verify.py` with openpyxl. It checks hashes, plans, saved cell values, recomputed aggregates, public completed receipts and release verification. It does not rerun GUI actions or independently establish visual/model performance. Original self-use evidence is in ../compact-mixed-app-01.
