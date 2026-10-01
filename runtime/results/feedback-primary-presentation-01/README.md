# Primary feedback and exact duplicate observation references

Production integration: `inputWithFeedback(alias, offset, interaction, tail,
policy)` snapshots explicit cue choices before dispatch. Existing four-argument
`input` remains unchanged. Requested cues missing/mismatching expected title,
rejected titles, stable title or no-authority fields latch caller STOP while
preserving the original response. No automatic action, model, sensor or retry.

The opt-in `guarded-feedback-observation-refs-v1` projection replaces exactly
`feedback.observation` with a reference to complete `source` and
`observation_report.observation` with a reference to `source.native`. Fixed-path
expansion is exact; unknown literals remain literal. It leaves input receipts,
cue samples/verdict, complete source and original PNG intact. Pending/rejected,
unstable cues, failed release/recovery and near duplicates stay full. Brief guard
presentation remains full for this extension; this new layer is lossless.

Frozen source d294e34164092afc05b81eb0cd652c27cea7b615; archive SHA-256
4c3125a49497f8be3fbbb4706df2d70c60ec89162000379e1f98712c4368cc50.
Archive and Node host bundle share one source revision. Two new primary-operated
cases, seed 1001069, each one allocation/no replay. Actual path: frozen primary
caller → instrumented Node host → frozen Python relay → frozen MCP server →
native X11 bridge. Four original PNGs reviewed and grounded by the primary.
Original relay JSON/image bytes, runtime reports, app events, host reviews,
cleanup and build manifests are retained. All owners/children exited before
independent app score inspection. Each case has one input, three emissions,
six native captures and two primary images. Matched performs one additional
read-only full retrieval, explicitly counted, with no new native capture/input.

| Case | Public requests | Cue | Original JSON bytes when expanded | Returned JSON bytes | Input call ms |
|---|---:|---|---:|---:|---:|
| matched | 5 | SAVED | 9496 | 7738 | 698.357 |
| pending | 4 | PENDING / STOP | 10617 | 10617 | 1102.698 |

Matched saves once and has an independent Saved ack; pending saves once and
has no completed task at cleanup. Matched JSON is 1758 bytes (18.5%) smaller
for this exact metadata; reference overhead is included. This is wire JSON,
not overall model token or cost reduction. Host text sinks are inert in this
scaffold: the primary received status/identity summaries plus original PNGs.
The retained matched full-retrieval acknowledgment is attribution from those
summary fields, not proof that every full JSON field was inspected. Primary
semantic awareness and per-reply tokens/billing remain unknown. Local times
include authored 600 ms/5000 ms delays, with a 1000 ms polling budget; no
comparable route, generic app or human tempo conclusion follows.

Actual combined live-window model counters: six unique responses, input 982377,
cached input 974464, uncached input 7913, output 3283 (reasoning 487 is included),
total 985660. Covers first allocation through second close, including startup,
controls, original images, commentary and cleanup; excludes earlier code/tests/
build and later audit/accounting/publication. These are whole growing-context
counters, not cold-session/per-reply values or billing. The requested context
records gpt-6.1-sol/medium, not provider revision attestation. Original source
replay verifies 18 source lines and all counters; `usage-whole.json` and
`verify_usage.py` retain boundaries/digests. HOLD_EFFICIENCY remains.

Local native checks: protocol 374 tests, harness 176; host suite 126 tests;
scoped Python suite 41 normal and -O. New reference tests cover exact roundtrip,
critical preservation, redirects/chains and near duplicates. Audit independently
reconstructs fixed paths, compares every original runtime field and native
input/cue receipt, validates PNG/host review association and checks one Save.
Eight mutation categories are rejected normally and under -O. These are finite
checks, not formal proof. Red tests and the first stricter-caller synthetic
fixture failure are retained; no live case was repeated to obtain better output.

Run `python3 audit.py` and `python3 test_audit.py` here. REPORT.json records scope,
counts, actual counters and limits. Historical experiments are unchanged.
