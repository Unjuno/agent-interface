# Issue #1968 successor audit — serialized package bytes

## H/T/D/C/U

- **H:** A typed multi-resolution package can reduce actual serialized representation while preserving exact authoritative recovery, including positional disambiguation of visually identical labels.
- **T:** Freeze a deterministic 64x40 fixture with two identical visual labels at distinct positions, serialize FULL and three reduced arms with one canonical JSON encoder, compare exact reconstruction and serialized byte lengths.
- **D:** `experiment.py`, 24 rows, per-arm byte lengths and SHA-256 values, this report, and the source branch commit.
- **C:** PASS only if FULL is exact, reduced exactness is explicit, a reduced arm is smaller than FULL on a nontrivial case, and both duplicate-label controls pass.
- **U:** model usability, automatic attention proposal, token/latency benefit, GUI correctness, and transfer remain unknown.
- **STOP:** No container-backed formal run was possible: Docker CLI was unavailable in the execution environment. The local run below is a non-formal sanity check only.

## Local sanity result

Command: `python experiment.py`

- 24 rows total.
- FULL: 6/6 exact.
- LOW_ONLY: 4/6 exact.
- CANDIDATE: 5/6 exact.
- CRITICAL: 6/6 exact.
- Serialized bytes are measured after canonical JSON encoding, not by summing pixel buffers.
- Duplicate visual labels are tested separately as `save_left`, `save_right`, and both together; each positional case reconstructs exactly under CRITICAL.
- The largest reduced exact package is 1,985 bytes versus 8,724 bytes for FULL in the same dialog case.

## Decision

**HOLD_NO_FORMAL_CONTAINER — scoped successor audit.**

The local result supports the intended serialization and ambiguity controls, but the requested container-backed formal evidence is absent. This does not relabel PR #1951 and makes no model, GUI, latency, token, or transfer claim.

