# Issue #5550 T0 OrbStack successor 04

**State: queue request only; no lease, source freeze, image inspection, or
container invocation.** The 2026-09-30 18:30–18:45 UTC proposal expired without
assignment and was withdrawn. This successor will preserve the expired T0
allocation and all raw/audit files unchanged.

## H / T / D / C / U

- **H:** A correctly serialized, network-disabled OrbStack replay of the
  existing finite, fully observed DFA reproduces its frozen output and
  independent exhaustive audit; this establishes only reproducibility of that
  synthetic model under an in-window container run.
- **T:** At a newly assigned exact non-overlapping interval, freeze the then-
  current main and the existing T0 source SHA-256 values. Run the existing
  `model.py` once in one isolated candidate container; only on exit 0, run the
  existing independent literal-table `audit.py` once in a separate container
  against the retained raw JSON. Store both outputs only in this new path.
- **D:** `PASS_T0_SYNTHETIC_SCOPE_REPRODUCED` only if the explicit assignment,
  current-main/source, image/platform, empty-lane, and half-open UTC guard all
  pass; the candidate exits 0 and emits 108 rows; the raw hash equals the
  predecessor's `f17273be18b33083353a883c47c2834a3c33457cb4daada2227aeaf00bd6eb8b`;
  and the separate audit exits 0 with no errors and the frozen expected
  counters. Any gate or invocation failure is retained as STOP; no retry.
- **C:** This is a replay for valid execution provenance, not a new plant or
  increase in scientific generality. Fully observed hand-authored transitions
  may account for the permissiveness result.
- **U:** Synthetic finite DFA only. No GUI, event classification, real
  observation freshness, timing, task success, utility, latency, runtime
  safety, or cross-domain transfer.

## Queue state (not a source freeze)

- Allocation proposal: `MAXPERM-SUPERVISOR-5550-T0-ORBSTACK-SUCCESSOR-20261001-04`.
- Latest main observed after prelaunch-guard PR #5622: `ac61a92b51139476fad181e0c14dfbdd5af5b026`.
- Candidate/auditor/tests currently match the predecessor hashes recorded in
  its `FREEZE.json`; they must be re-hashed against a fresh main at assignment.
- Proposed cached image only: `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
  `linux/arm64`. No image has been inspected or approved for this allocation.
- The 19:45–20:00 UTC interval is a request only. No container/image calls are
  allowed unless the coordinator records an exact owner, window, main SHA,
  image digest/platform, and exclusive lane assignment.

## Launch gates

1. Reconcile #5085, #5156, #5360, #5413, #5081, #5513, PRs, branches, and
   current main; require an explicit non-overlapping allocation.
2. At assignment, commit a new freeze receipt with exact coordinator comment
   ID, owner, window, source hashes, image digest/platform and commands.
3. At the start boundary, read back current main, verify the cached image and
   platform, confirm no active containers, and invoke the merged prelaunch
   guard using the actual system UTC clock.
4. Run at most one candidate and one conditional independent audit. Preserve
   exit statuses and hashes; release the lane immediately afterward.
