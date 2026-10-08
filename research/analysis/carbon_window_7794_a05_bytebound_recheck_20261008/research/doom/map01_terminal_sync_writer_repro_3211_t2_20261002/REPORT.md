# MAP01 terminal-sync trace-writer reproduction — T2

Disposition: **CONFIRMED_JSONL_TRACE_FORMAT_DEFECT** at the synthetic `JsonSession` writer boundary. This is not a MAP01 recovery result.

## H / T / D / C / U

- **H:** The exact pinned current-main `JsonSession` writer fails to emit ordinary JSONL because it appends a literal `\\n` string after each serialized event.
- **T:** Imported only the pinned `JsonSession` class after verifying Git blob `f5caf71a743a563b7de046b82d44db7ebe49e829`. One synthetic Python child emitted a `probe` row containing an embedded newline and a `terminal` row; one independent raw-only auditor checked memory order, process exit, sidecar hash, structural reconstruction and normal JSONL parsing.
- **D:** Candidate child exit 0; in-memory event count 2; retained sidecar 110 bytes with SHA-256 `db04370fa45f76c84e9cc9c3ff562bc81bfae99af60fe39149572d0c5d4eae9d`. The auditor reconstructed both exact events from the escaped-separator stream. Physical line count was 1, so ordinary JSONL parsing did not yield two records. The predicted serialization defect is reproduced.
- **C:** The synthetic child validates the exact reader-side writer boundary, not the full MAP01 runner/session lifecycle. It does not show whether the missing recovery terminal was emitted, dropped, delayed, or omitted by artifact packaging.
- **U:** The original fallback-terminal timeout remains unexplained. No controller efficacy, MAP01 task outcome, formal allocation, or input behavior is inferred.

## Run record

- Frozen main at preparation: `df883cbe0eb60d06f304fee321edcb572fb01e08`.
- Runtime: Python 3.12.10 on the local Windows host.
- Construction suite: `python -m unittest -v test_construction.py` — **3/3 passed**.
- Compilation: `python -m py_compile candidate.py audit.py test_construction.py` — **passed**.
- Candidate: `python candidate.py --out results/t2-01` — **one invocation**, exit 0.
- Independent auditor: `python audit.py --repo-root ..\\..\\..` — **one invocation**, exit 0.
- Retry: 0. Game/model/GUI/input/Actions dispatch: 0. Container: 0.
- `git diff --check`: exit 0; only the existing unrelated LF-to-CRLF warning for `research/analysis/README.md`.
- No source, allocation, workflow, threshold, or prior result was edited.

## Retained evidence

- Raw synthetic sidecar: `results/t2-01/session-events.jsonl`.
- Candidate receipt: `results/t2-01/candidate.json`.
- Independent audit summary: `AUDIT.json`.
- Source, construction tests, receipts and report hashes: `SHA256SUMS`.

Docker was not started: this host's Docker service is Stopped/Manual, the CLI is unresponsive, the container inventory is unknown, and no owner-bound lease was transferred. This scoped CPU test can inform a future diagnostic implementation, but it does not replace the issue's pending container-level session reproduction.
