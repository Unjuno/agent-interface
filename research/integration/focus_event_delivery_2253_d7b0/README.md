# Live focus-event delivery boundary (#2253)

## Chronology and scope

Retrospective publication of the already completed local allocation `live-focus-delivery-2253-d7b0-20260922-01`. The local freeze preceded formal case 0 but was **not** published to GitHub before measurement. Preserve closed #658, #2253's earlier PR #2257 construction STOP, and all historical outcomes unchanged.

Scientific disposition: **PASS_LIVE_FOCUS_BUFFER_BOUNDARY_SCOPED**.
Parent #2253 remains **HOLD_MODEL_TASK_UNTESTED** because no real model, ACK/expiry/resolution policy, task recovery, token accounting, or independently scored application effect was exercised.

Publication branch: `research/focus-event-delivery-2253-d7b0`.
Additive namespace only: `research/integration/focus_event_delivery_2253_d7b0/`.

## H / T / D / C / U

**H.** Current state replacement must not erase native-derived focus history. A bounded event list may discard payloads only if loss is explicit and fail-closed.

**T.** Six schedules x three repetitions = 18 fresh authenticated private-Xvfb lifetimes. Separate actor, watcher and consumer processes. The watcher uses actual core-X11 FocusChangeMask events and XGetImage state captures. Three policies consume identical records: LATEST_ONLY, SPLIT_UNBOUNDED, SPLIT_CAP4.

**D.** Scoped PASS requires all 18 identities, pixels, event order, consumer wires, source hashes and process exits to reconcile; unbounded split retains every authored native-derived event; bounded split retains at most four payloads per stream and exactly identifies all omitted critical events through RESYNC_REQUIRED; no unaccounted loss, cross-stream migration, model/input authority, rerun or replacement.

**C.** Criticality is authored, mutations are serialized, and this is not a saturated-kernel/backpressure or real-unavailable-model experiment. A current-state-only API is not inherently incorrect; it fails only the stronger history-preservation contract tested here.

**U.** Model decision quality, delivery deadline, ACK/expiry/resolution, resync implementation, task recovery, natural event rates, tokens, latency benefit, native-desktop transfer and production adoption remain unknown.

## Result

| Policy | Focus events observed | Payloads retained | Explicit omitted count | Unaccounted silent loss |
|---|---:|---:|---:|---:|
| LATEST_ONLY | 60 | 0 | 0 | 60 |
| SPLIT_UNBOUNDED | 60 | 60 | 0 | 0 |
| SPLIT_CAP4 | 60 | 48 | 12 | 0 |

SPLIT_CAP4 intentionally loses 12 payloads. In each of six overflow cases it retains the first four event payloads and reports the remaining two with `RESYNC_REQUIRED`, `coverage_complete=false`, the first unretained sequence/kind, and exact unretained count.

The consumer received 618 STATE records plus 60 focus-event records = 678 records. All 618 watcher image captures matched independent witness images. All 60 focus transitions were independently observed through a separate X connection. All 72 actor/watcher/consumer/Xvfb exits and all 18 external case-process exits were zero.

No keyboard/mouse input, model/provider call, user desktop, game, package install, or experiment-network operation occurred.

## Integrity

Local freeze SHA-256: `f332cc7a81b36d3ba472002e0dac1d5a4506115643be0bc532d55fe38499b09b`.
Raw-only audit SHA-256: `7ba2cef15e711fa9475e7aceb04e1a6d981cb0906cc174174a8a41e8c0e1c1c4`.
Full evidence archive: 146,704 bytes, SHA-256 `057ee2e5c75755ad854082cdea5fff2046551942ae67873d295397f3c3b9aed5`; expands to 288 files / 20,421,623 bytes.
24 unit-test methods passed; 16 copied-evidence mutations rejected; formal reruns = 0.

The complete raw archive remains a conversation-hosted attachment and is **not claimed fully GitHub-hosted by this PR**. This GitHub subtree publishes the exact freeze/source hashes, decision summary, candidate policy/watcher code and availability boundary. Original bytes remain immutable.

## Integration meaning

Carry latest state, retained historical events, and history-completeness/overflow as distinct fields. Returning focus does not prove that no focus-loss event occurred. After overflow, a latest frame cannot certify complete history and does not authorize automatic resync, replay, or input.

This does not close #2253 or the repository ROADMAP. The next substantive #2253 step requires a source-backed model/task-consumption path with expiry/ACK/overflow decisions and independent task effects.