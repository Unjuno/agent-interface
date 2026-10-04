# #5260 A03 — single readiness epoch, no-input WSLc construction

Outcome: `PASS_CONSTRUCTION_CUSTODY_NO_INPUT_ONLY`. Four legacy apps
scheduled/focused/finalized twice; four corrected apps did each once.
This is a disposable Tk component result, **not** a first-character,
public-client, visual/OCR, performance, OOM or integrated product PASS.

The parent A02 result remains `STOP_READINESS_CUSTODY_AFTER_PASS_AUDIT`
in [PR #7065](https://github.com/Unjuno/agent-interface/pull/7065), merged
as `cf2a0d59b5a147fb1918eb34f5bc03242336df05`. Nothing in that consumed
allocation was repaired, normalized or replayed.

## What can be integrated

`readiness_once.py` is a single-thread callback barrier: claim PREPARING
before reentrant GUI work, schedule once, claim FINALIZING before the
final callback, and fail closed after exceptions. It has no GUI, input,
file, network or process side effects. An application supplies its own
readiness predicate, retry scheduling, finalizer scheduling and finalizer.
See `probe_app.py` for the derived Tk construction. The helper is not a
cross-thread lock, crash-durable singleton or complete window-state guard.

Do not deploy a default wait or claim first-character recovery from this
packet. A future input experiment must have its own source/fixture/receipt
freeze and fresh allocation, with first/final ready identity gates before
qualification. No input allocation is authorized by the CI commands below.

## Retained validation

From the repository root:

```powershell
python -B -m unittest discover -s research/integration/tk_firstchar_5260_a03_wslc_20261003 -p 'test_*.py' -v
python -B research/integration/tk_firstchar_5260_a03_wslc_20261003/verify_packet.py
```

These commands are read-only apart from temporary synthetic test files;
they never launch WSLc, Xvfb, Tk apps or input. Twenty tests cover the
callback barrier, synthetic epoch/receipt adversaries, four separate raw
file bindings, and complete exact-byte manifest custody. The independent
auditor was written after the construction outcome; it is not claimed to
be a prospectively frozen formal auditor. Its first captured source/output
and host receipt are retained and independently reconstructed.

`FREEZE_CONSTRUCTION.json` records the historical source/image/argv and
host paths; it is a provenance record, not a portable launch recipe.
Do not run that occupied allocation again. The image is a locally cached
WSLc image ID, not a published pullable repository tag. Parent A02 retains
the image build, base manifest and runtime-version evidence. Rebuilding
from rolling apt repositories is not guaranteed to recreate those bytes.

See [REPORT.md](REPORT.md), [PLAN.md](PLAN.md), [LEDGER.md](LEDGER.md),
[RUN.json](RUN.json), and `SHA256SUMS`. All first streams and warnings are
retained under `results/`; no warning is evidence of enforced memory caps.
