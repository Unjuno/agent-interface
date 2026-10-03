# #7041: empty-backend cleanup receipt is not dead-owner release evidence

Successor to #7024 STOP archive (PR #7038). Same scientific endpoint, new18cell
allocation, source main a06d7f77, byte-identical public runtime7files. No product
or predecessor edits. All18 candidate cells and one saved-only formal auditor
completed exit0, not OOM, terminal. No scientific retries or replacement cells.

## Observed contrast

| Condition | Observed result |
|---|---|
| Empty-scope crash6 | scopedverified=true, helperemissions0, originalF8stilldown at kill+150ms checkpoint |
| Prearmed-scope crash6 | exactlyone helperF8up, independentF8neutral before checkpoint |
| Healthy6 | liveowner/F8held/helperpending at entry+200ms; public program completes later, no helperinput |
| Bystander6 (subset of crash12) | separately-owned F9 retained through checkpoint; helper never touches it |
| Final18 | whole32-byte keymap/buttons neutral, final emergency emissions0 |

Formal outcome FAIL_EMPTY_SCOPE_AS_OWNER_RELEASE_EVIDENCE; reference
SUPPORTED_PREARMED_OWNER_SCOPE_TRANSFER_SCOPED. 1748 independent query samples,
48 app events, 36 source actor streams joined/hashes; raw SHA256
aafcc9a0b9db97619008dbb446304bf8d6ac703616e4a79329111fc674957643.
Reference kill-request→publicrelease-return ms:3.889,0.806,3.471,0.911,3.522,3.703.
These are observed software intervals under shared hardware, not hard deadlines,
hardware sensing, app receiver latency or general reliability bounds.

## Death gate and preserved failures

The previous #7024 owner explicitly closed its writer before exiting; its guard
failed before any crash cell. Its frozen firstSTOP remains unchanged. This
successor leaves writer closure to actual process teardown, then polls original
PID/starttick identity for at most250ms/2ms. EOF alone never grants cleanup.
Death states/ticks/query start/end samples are retained, Z/missing accepted only
under declared identity. Actual no-input image probes demonstrated EOF while
original process still R for both normal exit and SIGKILL, then confirmed Z.
Pure deathgate RED5 failures→GREEN; death-observation joins RED2→GREEN;25total
pre-freeze hand checks. Original copied18 source-oracle tests had prior RED/GREEN
in #7024, not newly recreated/claimed as fresh RED here.

A premature preparation freeze raced the still-live host preflight session.
Driver refused SOURCE_DRIFT on setup/preflight.json BEFORE creating a scientific
container/runs directory. First FREEZE.json and construction/premature_freeze_stop
are preserved. The premature GitHub PASS assertion was explicitly retracted.
Terminal preparation exit0/image25/process3 was read before FREEZE_FINAL.json;
driver changed only its final-freeze selection before any scientific input.
Source/method/PLAN/image/terminalsetup frozen thereafter. Scientific candidate1,
auditor1; no consumed scientific allocation rerun or post-run code tuning.

## Checks and interpretation

Local host27 package (20hand oracle+5death transition+2saved), workspace21,
scorer2; same immutable image package27. Savedcopied-row16 invalid projections
reject schema/owner/death/scope/timing/wait/terminal corruptions without editing
originalraw. Function-level controls do not cover every CLI actor-stream mutation
or coherent scientific alternative. Pure/savedCI is not formal science PASS.
Own privateenginezero running, exactownedVM stopped; exitedcontainers/image kept.

The public API legitimately cleans its own tracking. A fresh empty backend's
verified scoped receipt cannot be promoted to proof of the dead owner's input
obligation. Reference prearmedcatalog injection is research instrumentation,
not an authenticated/public recovery API or production adoption. A persistent
broker retaining owned obligations may be a simpler integration choice.

Excluded: same-key ownership transfer, keymap/display replacement, uncertain
partial press, multiplekeys/buttons, descendants/securityboundary, hardware,
unresponsive X/kernel/host, model/game/useful-task/token benefit. Source lease
is admission-only; crash does not produce a completed publicreceipt. Normal-mode
OrbStack shares hardware/host mounts. Broad #17/#2437/#57 and fullroadmap remain
open. #7034 requested processfencing experiment belongs to another owner.
