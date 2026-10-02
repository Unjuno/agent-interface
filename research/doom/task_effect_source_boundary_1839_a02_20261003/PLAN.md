# Issue #1839 successor A02 — auditor mutation-contract qualification

## Lineage

A01 (merged PR #6761) is preserved as `HOLD_AUDITOR_NOT_COMPLETED`: its candidate ran once, but its auditor stopped before an audit result on `ghost_actuation`. A02 does not rerun A01 or alter its bytes. It tests the distinct missing execution property: whether a fresh raw-only auditor can reconstruct the A01 source summary and reject six corruptions of a candidate summary. Input source remains the same immutable #4193 retained corpus; the target is auditor completeness, not new task-effect evidence.

## H / T / D / C / U

**H.** A fresh candidate/auditor pair on the hash-pinned retained source will agree on six sessions, 194 scorer samples, three attack receipt joins, no positive endpoints, and no authority grants; the raw-only auditor will reject six independent candidate-summary corruptions.

**T.** Freeze current main, package, source hash, OrbStack image digest, and output paths. Run candidate once in a network-disabled container with read-only package/raw and separate output mount. Run an independent auditor once in a second network-disabled container, with raw/candidate read-only and separate audit output. The auditor re-parses the raw independently (no candidate imports), reconstructs the expected summary, compares the exact accepted fields, and applies six in-memory output corruptions. No live runtime/game/GUI/model/GPU/input, no A01 rerun, and no touching the shared CI container.

**D.** `PASS_AUDIT_MUTATION_CONTRACT_SCOPED` iff raw bytes/hash and six-session inventory match; independent candidate/auditor rows agree exactly; attack DOWN/UP joins=3/3; samples=194 with exact bool/int types and within-session increasing timestamps; attack/no-input positive endpoint sessions=0/3 and 0/3; authority=0; and all six mutations are rejected. Nonzero process, mismatch, or an accepted corruption => preserve STOP/FAIL and never rerun this allocation.

**C.** This is a read-only audit-implementation qualification on a corpus with no positive endpoints. It cannot establish positive-effect sensitivity, task causality, scorer truth, multi-actuation generality, or live behavior. A01's failure remains separate and immutable.

**U / stop.** No live MAP01, causal/effect efficacy, recovery, completion, latency, safety, human-tempo or product claim. Stop after the one candidate/auditor pair; any next step needs a different hypothesis and allocation.

## Frozen input

- Intake main: `b7300488efd4d27b874785bd024929c886484048`.
- Source: #4193 `RAW_USED.json.xz`, 7,392 bytes, SHA-256 `0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740`.
- OrbStack Engine 29.4.0 linux/arm64; image `python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`; network none; requested 1 CPU, 512 MiB and 64 PIDs; read-only source/root.
