# #5156 T3: independently auditable XQueryKeymap witnesses

## Status

Host-only construction is verified; formal X11/Docker execution is **NOT RUN**. This directory is an additive successor and does not alter A06 or any previous raw result/STOP. It is not yet a formal #5156 result and does not claim physical key occupancy, application consumption, or MAP01 effects.

Repository freeze: main `7c44e41934a62b6f90227b0dc74231cf897ab898`, observed 2026-09-30 UTC. The proposed identity is `MAP01-OWNER-KEYMAP-WITNESS-5156-T3-20261001-01`; it is a unique label only, **not a reservation or permission to run**. Vendored dependencies are copied byte-for-byte from A06's tracked frozen bundle in the history at that main commit; see `SOURCE_MANIFEST.json` for every repository path and SHA-256. In particular, bundled `input_owner_v11.py` is A06's owner-thread implementation and is not the current top-level telemetry wrapper of the same filename. Recheck main and all manifest hashes before formal use. There is deliberately no launch/slot dispatcher here: a fresh exclusive allocation, queue reconciliation, image/platform inspection, and a new one-shot launch contract must be established first. Never reuse an earlier allocation or another lane's slot.

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
`run_cli_construction_experiment.py` invokes `emit_synthetic_candidate.py` once, then invokes `audit_formal_x11.py` once in a distinct process only after candidate exit 0, with an explicit `synthetic-cli` audit mode. Synthetic mode requires exactly one fixture carrying `evidence_mode: synthetic-cli` and `synthetic_only: true`. Formal mode rejects synthetic markers and also requires an out-of-band host launch receipt plus a separately provisioned trusted host key; fields in the candidate's raw stream alone are never sufficient to assert X11 provenance. The receipt must be captured outside the container by the one-shot launch supervisor after candidate completion and Docker inspection, then retained separately. It binds the exact raw and expected hashes, frozen allocation, `run_formal_x11.py` hash, container/image/platform, argv, and candidate/container exit codes. The auditor verifies HMAC-SHA256 over canonical JSON with the `hmac_sha256` field omitted, using the trusted key file, and records the exact receipt file's SHA-256 in the audit. The key must be provisioned outside this package, not mounted into the container, and not exposed to the candidate. This authenticates the host signer, not the engine independently; preserve the trusted host capture/custody chain. The current package has no formal host launcher or receipt, so formal mode is intentionally unavailable until that independently acquired artifact exists. The synthetic driver records PIDs, exit codes, stdout/stderr, raw/expected hashes, and hashes for the candidate, auditor, candidate fixture source, and experiment driver. This is a host-only file/process-boundary construction experiment; it does not exercise the X11 runner.

`results/construction-cli-01/` is immutable historical evidence for the first attempt. Its candidate/raw were synthetic, but the original auditor JSON mislabeled scope as X11. `CORRECTION.json` records the issue and hashes without modifying the original bytes. `construction-cli-02` is the corrected successor run. Independent review found that removing the synthetic marker could still default to the formal scope; `construction-cli-03` records explicit mode and expanded source-hash provenance. The stronger `evidence_mode` allowlist and both mode mismatch controls are validated by the current suite; `construction-cli-04` is the successor run using that contract and includes the same expanded hashes. After latest-main refresh, `construction-cli-05` preserves the same host-only scope on a new freeze. A second independent review showed that raw fields could be relabeled; `construction-cli-06` retains a synthetic-only PASS while tests now require an out-of-band host launch receipt. Review then found that receipt custody itself was unverified; formal mode now requires a separately provisioned HMAC key and records receipt hash. The refrozen `construction-cli-07` is the successor on main `7c44e41`; `construction-cli-08` uses the same source freeze with the HMAC receipt contract. A further review found that malformed receipt schemas could misleadingly set the authenticated boolean; the validator now returns signature authentication explicitly, tested by a malformed-schema CLI regression, and `construction-cli-09` preserves this successor run. All older run records remain unchanged.

## Reproduction

From this directory run:

```sh
python3 -B -m unittest -v test_keymap_witness test_audit_formal_x11 test_serialize_release test_cli_boundary
python3 -B -m py_compile audit_formal_x11.py run_formal_x11.py
python3 -B run_cli_construction_experiment.py --results results/construction-cli-NN
```

When a separately authorized formal X11 run exists, first retain its independent host launch receipt, then invoke the auditor with the explicit formal mode:

```sh
python3 -B audit_formal_x11.py /path/to/formal/raw.jsonl EXPECTED.json /path/to/formal/audit.json formal-x11 /path/to/formal/host-launch-receipt.json /path/to/trusted/host-receipt.key
```

Latest host-only result on frozen main `7c44e41934a62b6f90227b0dc74231cf897ab898`: 32/32 tests passed; `py_compile`, JSON parsing, vendored-source byte comparison, all result SHA256SUMS, and `git diff --check` passed. `construction-cli-09` emitted `PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY`; candidate/auditor PIDs 21304/21306, raw SHA-256 `b18cdae371f1601bff2ff97eaa9170c6ae34986d7e5e4cbbc9d341996ccc9160`. The synthetic audit records no formal receipt/key, and synthetic CLI evidence does not imply Docker/X11 execution. Use a fresh results directory for every experiment and preserve exact stdout and file hashes.
