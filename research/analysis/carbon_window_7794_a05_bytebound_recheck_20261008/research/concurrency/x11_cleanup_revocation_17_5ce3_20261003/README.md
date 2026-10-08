# Cleanup is not revocation — Issue #7010

Bounded successor to #6999/PR7006 under #17/#57. Frozen source main
8d89dcff4508fac19945731ddf46ffb4d5092d8c. All code/data is additive in this
package; no public runtime or predecessor source/raw/decision is changed.

H: independently releasing the current F8 hold during PNG persistence may leave
the same already-admitted program able to emit its queued F9 afterwards. A
minimal cancelled check before positive key_state is a causal reference, not a
new production runtime or exported cancel API.

T: PLAN fixes12fresh privateXvfb cells,3repeats × cleanup_only/reference-gate ×
healthy/blocked-and-revoked. Same six-op public X11RuntimeSession program:
focus,F8down,observe/PNG,F9down,40mswait,release_all. Fresh independent logical
server-state queries and owned-window key events. In fault arms only, declare a
probe Event revocation and call same-owner serialized cleanup at actual PNG
write entry. Check+150ms; resume+400ms. Both policies use the same cleanup/input
mutex; the reference alone checks the Event immediately before positive native
key_state. No second conflicting input owner. Healthy arms do not cancel or add
out-of-band cleanup, and must produce identical F8/F9 press/releases.

D:12valid exposures/exact source/PNG/program/input-call/capture/release/physical
joins/neutral terminals. All3cleanup_only fault cells must release F8 before the
checkpoint but later emit/independently observe F9 after revocation+resume;
this is FAIL_CLEANUP_ONLY_COMPOSITION_LATE_INPUT_SCOPED, not a failure of the
documented release_all contract. All3reference faults must reject F9 at op3,
retain completed[0,1,2] and verified cleanup, no F9 event/logical state. Healthy6
complete all ops with exact four app events. Other coherent contrasts are HOLD;
incomplete/unexpected native exposure is STOP, never a successful-subset rerun.
The saved auditor rejects protocol/trace contradictions. ScientificFAIL is a
valid collected counterexample, so candidate/auditor process exit0 is expected.

C/U: public session offers admission/recovery, not cancellation; the reference
Event/wrapper is research instrumentation. No production cancellation/broker,
other input methods, check-to-injection cancellation race, harddeadline,
hardware state, native compositor/server stall, natural disk/fsync, game/model,
semantic task feedback/quality, token/speed benefit or full roadmap completion.
QueryKeymap is logical X-server state, not hardware sensing. GetImage/encoding
finish before the Event-wait pause. The 2s lease avoids expiry confounding and
is only admission authority. The40ms F9 hold is fixed for exposure/readback.

Roadmap: prospective Issue7010 → saved-oracle RED/GREEN → source/image/input/
decision freeze → one candidate12cells → one saved-only auditor → localCI and
copied-record corruption controls → batch push, independentreview and eligible
PR/main evidence handoff. Resource: only owned VM research-59-hud-ocr-5ce3-20261003
and its private Docker; no default/shared engine/otherguest/GPU/host display.
Immutable cached arm64 image,networknone,readonlyroot/source,dropallcaps,
no-new-privileges,1CPU,512MiB/noSwap,128PIDs,64MiBtmpfs. Actual inspection and
cgroups retained; normal-mode VM shares host hardware/filesystem integration.

Use `python3 run_stage.py candidate`, then `python3 run_stage.py auditor` only
after candidate exit0. The exclusive stage folders and frozen hash checks refuse
repeat collection. All original receipts/raw/PNGs/logs remain retained regardless
of scientificFAIL/HOLD/STOP. Do not retry a consumed stage. Before freeze,
construction checks may import/validate records without Xvfb/native input; none
of those tests is the scientific allocation. A later supplemental verifier may
read saved evidence, never rewrite it or upgrade broader claims.
