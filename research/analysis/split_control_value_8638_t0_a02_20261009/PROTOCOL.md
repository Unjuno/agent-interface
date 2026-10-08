# Issue #8638 T0 A02 protocol

Allocation: `8638-T0-A02-20261009` (`SCV-8638-v2`). This is a fresh successor to A01. A01's in-memory result and artifact-custody STOP remain unchanged; its 48 raw rows were not persisted, and neither A01 program is rerun here.

## H / T / D / C / U

**H.** Across the three preregistered A/B pairs, VOI-C and the acquisition-only information-minus-cost proxy rank the high-accuracy/low-uptake cue A above B, while exact expected net value under the separate downstream policy ranks A below B. Positive acquisition value can coexist with a negative realized value when the signal is not used. Stale and unsupported cues remain unknown and cannot alter mandatory gates.

**T.** Exhaustively enumerate the finite binary state, latent signal, delivery and uptake space for 12 supported cases (16 rows each), plus one unsupported case that must remain unscored. Use integer probability masses with denominator `1000^4`; retain every row including zero-mass combinations. Candidate and raw-only auditor are separate programs. The candidate has no model, GUI, external service, or runtime dependency. Candidate writes the complete raw JSON itself using exclusive temporary creation, fsync and atomic rename. The auditor independently reconstructs the row frame and all expected losses from `inputs.json` and candidate raw.

**D.** `PASS_METHOD_SCOPED` requires all 192 supported rows and all 13 cases to reconcile; the three A/B rank reversals must match their preregistered direction; positive-but-unconsumed, irrelevant, rare/high-consequence, misleading, stale and unsupported controls must satisfy their named checks; all corruption controls must be rejected; and authority remains `NONE` with mandatory gates unchanged. Any dropped row, forged use, altered loss/rank, or stale/unsupported score is `FAIL_AUDIT`. This does not estimate real planner uptake or deployed observation value.

**C.** A fixed reliable downstream policy can make VOI-C sufficient. The authored uptake and response rules may manufacture rank reversals; fixing presentation or downstream use may be preferable to a new ledger.

**U.** Inputs are synthetic and chosen for falsifiability, not calibrated. There is no model, user, GUI, latency, application effect, safety, deployment, or product claim. The finite result addresses only accounting under this declared simulator.

## Frozen inputs and commands

- Cases and all probabilities/losses: `inputs.json`.
- Candidate: `candidate.py`.
- Independent raw-only auditor: `auditor.py`.
- Process network-deny profile: `network_deny.sb`.
- Formal candidate: `sandbox-exec -f network_deny.sb python3 -B candidate.py inputs.json raw/candidate_raw.json`.
- Formal auditor: `sandbox-exec -f network_deny.sb python3 -B auditor.py inputs.json raw/candidate_raw.json raw/audit.json`.
- The candidate and auditor each run once. If the candidate does not exit 0 and produce a complete hash-verified raw file, the formal auditor does not run. No retry, overwrite, or replacement is allowed.

The no-acquisition comparison is an explicit zero net-value baseline. VOI-C assumes the cue is valid and fully used by the optimal single controller. The acquisition-only proxy is mutual information in bits minus acquisition cost; it ignores delivery and downstream uptake. Split-control value uses only a delivered, valid, consumed signal under the frozen separate response. A stale cue is not shown to the downstream policy; its baseline outcome and acquisition cost remain visible, but its signal-specific VOI and information proxy are unknown. Out-of-model support has no score or fabricated outcome. The optional ledger never grants authority, and raw validity, freshness, authority, release and independent-effect gates stay outside the utility calculation.
