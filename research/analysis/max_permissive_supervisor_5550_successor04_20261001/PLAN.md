# Issue #5550 T0 OrbStack successor 04

**State: self-assigned bounded CPU-only OrbStack window; source/image freeze
pending the exact start gate.** The 2026-09-30 18:30–18:45 and 19:45–20:00 UTC
proposals expired without assignment and were not run. This successor preserves
the expired T0 allocation and all raw/audit files unchanged.

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

- Allocation: `MAXPERM-SUPERVISOR-5550-T0-ORBSTACK-SUCCESSOR-20261001-04B`.
- Named owner: Unjuno. Self-assignment comment: #5085 comment
  `5922184340`; preregistration recorded on Issue #5550 comment `5922258479`.
  Direct user instruction to continue experiments is in this task.
- Window: 2026-10-01 00:50:00–01:05:00 UTC (half-open). This starts five
  minutes after the #5156 sentinel's recorded 00:30–00:45 window. At start,
  refresh the coordination issue and STOP if any conflicting allocation or
  unreleased active owner remains.
- Latest main observed during preparation: `a43d274803c1689c3f948641aef5a57102a04f34`.
  This is planning context only; refreeze at the start boundary.
- Candidate/auditor/tests currently match the predecessor hashes recorded in
  its `FREEZE.json`; they must be re-hashed against a fresh main at assignment.
- Proposed cached image only: `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
  `linux/arm64`. No image has been inspected or approved for this allocation.
- Cached image remains a proposal until the exact start gate verifies local
  image digest/platform; no pull/build is allowed.

## Launch gates

1. Reconcile #5085 and the most recent competing requests at the start; require
   the exact self-assigned allocation above to remain non-overlapping.
2. Commit a new freeze receipt with assignment comment, owner, window, current
   main, source hashes, image digest/platform and commands.
3. At the start boundary, read back current main, verify the cached image and
   platform, confirm no active containers, and invoke the merged prelaunch
   guard using the actual system UTC clock.
4. Run at most one candidate and one conditional independent audit. Preserve
   exit statuses and hashes; release the lane immediately afterward.
