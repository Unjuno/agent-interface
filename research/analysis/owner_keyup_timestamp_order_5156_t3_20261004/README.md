# Owner key-up timestamp-order construction T3 — Issue #5156

## H / T / D / C / U

- **H:** The current direct retained-input analyzer marks a measurement ready only when its four caller-side monotonic timestamps satisfy `admitted_ns <= input_ack_ns <= release_call_started_ns <= release_call_returned_ns`. Two adjacent-order violations not present in the previously reported direct-analyzer control—ACK preceding admission, and release return preceding release start—should fail closed.
- **T:** Freeze the current-main analyzer and evaluate two positive controls (ordinary order and all-equal boundary) plus exactly those two new malformed-order cases. Candidate imports the frozen analyzer and records its unmodified outputs once. A separate raw-only auditor checks the temporal oracle, arithmetic, source identity and four corruption controls. The auditor reports evidence integrity separately from hypothesis mismatch so a valid negative finding is not mislabeled as an audit failure. No runtime, GUI, X11, game, model, provider, GPU, or network is used.
- **D:** `PASS_ORDER_GATE_SCOPED` requires both positives ready, both malformed cases not ready, the retained bounds exactly reconciled, and all four audit mutations rejected. If either malformed case is ready, record `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED`; this is a construction finding, not a live measurement result.
- **C:** Host Python 3.14.5, standard library only. OrbStack's daemon responds, but Docker image/container inventory fails while opening a containerd content blob (`operation not supported`). No image pull, container launch, or retry is attempted. This narrow pure-Python check does not need X11 or the shared formal lane.
- **U:** Whether the current analyzer enforces the remaining adjacent monotonic-order relations in this finite synthetic input contract. This does not establish owner-thread timing, physical key state, live MAP01 telemetry, or task effect.

## Frozen provenance and execution

Allocation: `OWNER-KEYUP-TIMESTAMP-ORDER-5156-T3-20261004-01`.

Frozen main: `2f72c6474167f93a2e1a6e2b8a497a1a8a6d266a`. T1 and T2 are preserved in their own paths with first STOP outcomes; this is a new allocation and path. The byte-identical analyzer source is retained in [`source/`](source/). Freeze and source hashes are in [`FREEZE.json`](FREEZE.json); the input cases and executable test/auditor hashes are in the same manifest.

Run exactly once after prospective registration on Issue #5156:

```sh
python3 candidate.py cases.json source/analyze_map01_direct_retained_input_v1.py output/raw.json
python3 audit.py cases.json output/raw.json output/audit.json
```


The candidate invocation does not interact with an application or input device. No formal X11 allocation is consumed. The prior analyzer finding and its two exact temporal inversions are not repeated here; the two negative rows in `cases.json` test distinct adjacent-order relations.

Before formal freeze, `preflight/test_auditor_classification.py` checks that the auditor reports malformed-order observations as scientific findings while retaining a clean integrity status, and that raw/identity/arithmetic corruptions remain integrity errors. This isolated auditor-unit preflight is not a candidate or formal-auditor invocation and is excluded from those counts.
