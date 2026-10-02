# Issue #5442 T7 — WSLc container replay of the four-case semantic receipt boundary

Allocation: `SEMANTIC-RECEIPT-5442-T7-WSLC-20261002-01`
Frozen main observed: `900c48368909a247ffd2b1b4dddd944cd6008d90` (2026-10-02 04:32:19 UTC)
Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64, already cached)

## H / T / D / C / U

**H.** An independently written deterministic layered simulator will reproduce the four previously specified Issue #5442 cases in an offline WSLc container, and a separate raw-only auditor will accept the exact expected outcomes while rejecting four frozen corruptions. This addresses the open containerized-simulator reproducibility gate; it is not a new claim that toy simulation proves GUI correctness.

**T.** Run `candidate.py` exactly once in a network-disabled, one-CPU WSLc container with the frozen `scenarios.json` and source mounted read-only. Candidate emits one JSON raw document to stdout. Only on exit 0 and a single complete JSON document, run `audit.py` exactly once in a separate network-disabled WSLc container; mount the same frozen source and candidate raw read-only. No retries, replacements, package installs, pulls, GPU, or external calls. Candidate and auditor are distinct processes and containers.

**D.** Candidate disposition table must be: `valid_effect` → intermediate `SUCCESS`, endpoint `SEMANTICALLY_CONFIRMED`; `wrong_target`, `stale_pre_state`, and `noop` → intermediate `SUCCESS`, endpoint `UNKNOWN`. The auditor independently reconstructs all four rows from the frozen scenario source, checks exact schema/order/source SHA-256, and rejects four separate raw mutations (wrong endpoint status, changed intended target, missing row, duplicate row). `PASS_CONTAINER_REPLAY_SCOPED` requires the expected raw table and four-of-four corruption rejection with zero auditor errors. Any schema/source/count/exit mismatch is STOP/HARNESS_FAIL; retain first outputs.

**C.** This is a stipulated deterministic simulator with stipulated authoritative endpoint state. One Python 3.12 image and WSLc 3.0.1.0; no physical GUI, application observer, model, user data, task effect, or real fault process.

**U.** The result can establish portable execution of this finite contract and independence of the raw audit only. It does not validate endpoint authority/fidelity, observer freshness in real applications, latency, safety rates, or runtime integration. The earlier host T0 and T4 remain unchanged; this is a distinct T7 container-reproducibility rung.

## Frozen one-shot accounting

Candidate=1 maximum; auditor=1 maximum and only after candidate exit 0; retries=0. Construction tests do not consume either invocation. Output path was absent before this freeze. All source inputs are network-disabled and read-only in formal containers. Requested memory settings are not treated as enforced unless runtime evidence confirms them; no memory claim is part of D.
