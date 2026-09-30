# #5156 T3: independently auditable XQueryKeymap witnesses

## Status

Host-only construction is verified; formal X11/Docker execution is **NOT RUN**. This directory is an additive successor and does not alter A06 or any previous raw result/STOP. It is not yet a formal #5156 result and does not claim physical key occupancy, application consumption, or MAP01 effects.

Repository freeze: main `728d30cb2bf4e3b0a183a929258064d3ba823404`, observed 2026-09-30 UTC. The proposed identity is `MAP01-OWNER-KEYMAP-WITNESS-5156-T3-20261001-01`; it is a unique label only, **not a reservation or permission to run**. Vendored dependencies are copied byte-for-byte from A06's tracked frozen bundle in the history at that main commit; see `SOURCE_MANIFEST.json` for every repository path and SHA-256. In particular, bundled `input_owner_v11.py` is A06's owner-thread implementation and is not the current top-level telemetry wrapper of the same filename. Recheck main and all manifest hashes before formal use. There is deliberately no launch/slot dispatcher here: a fresh exclusive allocation, queue reconciliation, image/platform inspection, and a new one-shot launch contract must be established first. Never reuse an earlier allocation or another lane's slot.

## H / T / D

**H:** Persisting each 32-byte XQueryKeymap bitmap, monotonic observation timestamp, case/stage, and admitted keycode map lets a raw-only auditor independently verify server key-state transitions instead of trusting runner booleans.

**T:** In a future disposable Xvfb fixture, capture pre-down, post-down, and post-terminal snapshots for a single-key explicit release, ordered two-key explicit release, and partial-cancel cleanup. Do not query between the two release requests. Run the candidate once and, only after zero exit, run the raw-only auditor once.

**D:** Host tests require exactly nine unique case/stage witnesses; decode exactly 32 bytes; match keycode maps to the complete expected admission inventory; verify the entire bitmap equals the expected pressed-key state with no unaccounted pressed keys; and verify monotonic timestamps. Held-state samples must precede release requests and terminal-state samples follow the corresponding XSync completion. Two-key snapshots occur only before the first and after the second release. Missing, duplicate, malformed, contradictory, identity-mismatched, or mistimed witnesses fail closed. Fixture allocation/frozen-main identity must match `EXPECTED.json`. The audit result remains server processing/state evidence only.

## C / U

**C:** XQueryKeymap is a server-state snapshot, not a continuous physical-occupancy measure or proof that an application consumed an event. A single X server/fixture does not characterize scheduling variability.

**U:** No live MAP01 occupancy, efficacy, safety rate, recovery quality, human tempo, latency, or cross-domain transfer is established. No MAP01/control interaction is part of this construction.

## Synthetic raw-only CLI boundary experiment

**H:** A synthetic JSONL fixture can cross the actual on-disk boundary from one candidate process to a separate auditor process, preserving all nine keymap snapshots and producing a correctly scoped synthetic result.

**T/D:**
`run_cli_construction_experiment.py` invokes `emit_synthetic_candidate.py` once, then invokes `audit_formal_x11.py` once in a distinct process only after candidate exit 0, with an explicit `synthetic-cli` audit mode. Formal callers must explicitly choose `formal-x11`. Synthetic mode requires exactly one fixture carrying `evidence_mode: synthetic-cli` and `synthetic_only: true`; formal mode requires `evidence_mode: formal-x11` and rejects synthetic markers. Missing or contradictory provenance fails closed and cannot promote unmarked bytes to formal X11 scope. The driver records PIDs, exit codes, stdout/stderr, raw/expected hashes, and hashes for the candidate, auditor, candidate fixture source, and experiment driver. This is a host-only file/process-boundary construction experiment; it does not exercise the X11 runner.

`results/construction-cli-01/` is immutable historical evidence for the first attempt. Its candidate/raw were synthetic, but the original auditor JSON mislabeled scope as X11. `CORRECTION.json` records the issue and hashes without modifying the original bytes. `construction-cli-02` is the corrected successor run. Independent review found that removing the synthetic marker could still default to the formal scope; `construction-cli-03` records explicit mode and expanded source-hash provenance. The stronger `evidence_mode` allowlist and both mode mismatch controls are validated by the current suite; `construction-cli-04` is the successor run using that contract and includes the same expanded hashes. All older run records remain unchanged.

## Reproduction

From this directory run:

```sh
python3 -B -m unittest -v test_keymap_witness test_audit_formal_x11 test_serialize_release
python3 -B -m py_compile audit_formal_x11.py run_formal_x11.py
python3 -B -m unittest -v test_cli_boundary
python3 -B run_cli_construction_experiment.py --results results/construction-cli-NN
```

Latest host-only result: 29/29 tests passed; `py_compile`, JSON parsing, vendored-source byte comparison, all result SHA256SUMS, and `git diff --check` passed. `construction-cli-04` emitted `PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY`; candidate/auditor PIDs 4336/4337, raw SHA-256 `779a5c527ab1d423ec2e9452abf51fa6c25d401a8345b0c7aaf2b3539d238274`. Synthetic CLI evidence does not imply Docker/X11 execution. Use a fresh results directory for every experiment and preserve exact stdout and file hashes.
