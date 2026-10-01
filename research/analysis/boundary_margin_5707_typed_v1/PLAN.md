# Issue #5707 typed boundary-margin T0

Allocation: `MAP01-R133-TYPED-MARGIN-5707-T0-20261001-01`

This is a new synthetic measurement-contract test. It does not reuse or pool
#5709/#5715 raw rows. It tests whether unlike boundary margins remain typed,
whether an interval is classified against its own threshold, and whether
abstention/no-actuation and blocked-proposal margins retain their distinct
meaning. The experiment has no action authority and no live system input.

## H / T / D / C / U

**H.** A typed ledger keyed by boundary purpose, kind, unit, contract ID/version,
and threshold can retain every fixed opportunity without producing a cross-kind
pooled scalar; it will keep a safe stop as `NO_ACTUATION_MARGIN`, a blocked
negative proposal separate from actuation, an unavailable timestamp as
`UNKNOWN`, and exact zero as not crossed while detecting a fully negative
interval as crossed.

**T.** One finite standard-library fixture with eight immutable opportunity IDs:
lease-expiry in milliseconds, hazard-clearance in pixels, blocked negative
proposal-admission in milliseconds, safe stop, missing-timestamp UNKNOWN, a
second lease contract version, an exact-zero lease margin, and a negative
lease-boundary crossing. Every opportunity is present in the raw denominator.
The candidate writes one row per opportunity plus per-type summaries. A
separate read-only auditor reconstructs the ledger from `plan.json` and raw
JSONL, then applies ten fixed in-memory mutations. No model, GUI, provider,
network inside the containers, GPU, user data, or live safety exposure.

**D.** `PASS_TYPED_MARGIN_CONTRACT_SCOPED` only if all eight opportunity IDs
appear exactly once; measured intervals and threshold states reconstruct;
comparisons stay within exact purpose/kind/unit/contract/version/threshold
groups; actuation is `NO_ACTUATION_MARGIN` for safe-stop and blocked proposal;
the proposal's negative admission margin remains distinct; missing time stays
UNKNOWN; exact zero is not crossing; the negative interval is detected as
crossed; forbidden external effects remain zero; all ten mutations reject; and
the independent audit has no errors. A complete contrary output is a scoped
FAIL; incomplete provenance or execution is HOLD/STOP.

**C.** The cases and margins are authored deterministic fixtures with explicit
units. A bounded interval straddling zero would be uncertain, not a positive
margin. The fixture does not calibrate uncertainty or define a universal
cross-boundary risk scale.

**U.** No claim about real hazard probability, live MAP01 safety, runtime
promotion, policy efficacy, survival, task success, or predictive value of
near-miss margins. A T0 PASS validates only these ledger semantics.

## Frozen execution boundary

- Base main: `24f6b7d5f9395105807f981d48db212e6692a6f4`.
- Planned candidate and auditor: one invocation each in isolated containers;
  no retry, replacement, or tuning.
- Planned image: `python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8f910824d4e93bdce61e212c7e87168123ea3073b41a1a`,
  `linux/amd64`. This identity will be checked before formal execution.
- Container profile: network none, read-only root, all capabilities dropped,
  no-new-privileges, bounded memory/CPU/PIDs, and a dedicated writable output
  mount. Raw first outcomes are never overwritten or retried.

## Execution addendum (append-only)

The frozen planned image could not be pulled or run: Docker Hub returned `not found`
for digest `1aaa65a...`; OrbStack's local image listing contained the same
hexadecimal value only as an untagged image ID, with no resolvable repository
reference, and the frozen expected image ID/platform did not match an
inspectable image. The planned formal gate was therefore stopped before
invocation.

For method diagnostics only, the candidate and independent auditor were each
invoked once in separate OrbStack containers using the already-present
`python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
image (`linux/arm64`, actual image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`).
Both used `--network none --read-only --cap-drop=ALL --security-opt no-new-privileges`,
256 MiB, 1 CPU, 32 PIDs, and a read-only study mount with separate output.
The diagnostic raw bytes are byte-identical to the one host construction
output (SHA-256 `3455ef59650bb7841c22b2941c572655a83f220c07aa84c2d8d9dc9c631d89f4`).
The raw-only audit reconstructed 8/8 opportunities, 4 typed groups, 1 UNKNOWN,
2 `NO_ACTUATION_MARGIN`, zero forbidden effects, and rejected 10/10 mutations.
It reports `PASS_TYPED_MARGIN_CONTRACT_SCOPED` for the method fixture, but the
frozen image-verification gate rejected its execution receipt with exactly
`EXECUTION_IMAGE_REF_MISMATCH`, `EXECUTION_IMAGE_ID_MISMATCH`, and
`EXECUTION_PLATFORM_MISMATCH`. This is a **non-formal alternate-image
construction result**, not the preregistered formal allocation result. The
formal allocation disposition is `STOP_IMAGE_IDENTITY_UNAVAILABLE`; the
hypothesis remains unevaluated under its frozen gate. No container was
retried or rerun after the independent audit.

Host construction checks: Python 3.14.5 on Darwin arm64; `unittest` 6/6,
JSON parse, Ruby YAML parse, `git diff --check`, and `SHA256SUMS` all passed.
These checks do not substitute for the unavailable fixed-image run. No real
runtime, model, GUI, physical input, user data, network access in containers,
or safety effect was exercised. The candidate/auditor source remains unchanged
after its runs; the report/manifest record both the non-formal diagnostic and
formal STOP separately.
