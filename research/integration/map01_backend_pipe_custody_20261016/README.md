# Selected MAP01 backend / owner custody over child pipes

Base `a081dc8780c609fb4beb3f954dc5f48a00ec95ac`; tested code
`e5654a341a28fba58b3ff8b87a0d68d2d6944a03`. New ordinary test:
`research/doom/test_map01_backend_pipe_custody.py`. No production behavior change.

## Actual path and retained effects

Owned child processes instantiate actual process-identity backend, owner-thread
release-batch backend, InputOwner V4/V12, and Executor v13 through the existing
backend_fixture. X display/input/query and ImageGrab are patched fixtures only;
no native connection is opened. Parent test protocol sends submit/cancel,
generation change, inspect and explicit fixture resume/close over real pipes.
This parent is not the full V39/controller/session main.

Four selected modules pass **17 unique methods**, zero failures/errors/skips,
normal and actual optimized. Three new backend pipe cells per mode cover:

| Cell | Actual selected code / Fake X result |
|---|---|
| cancel | One a-key press/release on one owner thread; cancelled terminal, verified fake empty bitmap |
| generation change | No cancel command; owner autonomously releases and returns needs_decision / target_generation_invalidated |
| blocked release | Terminal is unverified while fake key38 remains down; closed Executor replacement refused. Resume makes key up and stops retired owner, but exact backend custody obligation remains and replacement still refuses |

Every cell sends only one program and retains exactly KeyPress38/KeyRelease38,
with identical owner thread ID. The late fake bitmap becoming empty cannot
clear the earlier uncertain release obligation. A fresh post-late-return capture
also does not erase that obligation. Original/late custody is compared exactly.
Captured source binds sequence/surface41 to generation a*64; generation-change
cell replaces the fixture digest with b*64 after press. Decoded32x32 RGB PNG
bytes are independently joined to typed/full source hashes. White images and
fixed HUD readers are synthetic, not semantic perception or task effects.

Raw child wire/commands, real backend events, per-key release attempts and timing,
custody snapshots, exact PNG bytes/base64/hashes, child flags and launcher/parent
identities are preserved. 66 unique executed repository source joins cover
parent/child loaded selection, not every dependency or platform route. Existing
eight pipe cells also run per mode (22 final owned children total). No final
cell forced cleanup; readers and processes joined. A subsequent named44
launcher/interpreter PID snapshot found all absent, not a global/future guarantee.

The independent saved reader imports no candidate. It checks raw command/edge
counts, identity/timing joins, generation-without-cancel, unknown/late custody,
replacement refusal, single-owner thread and actual decoded PNG hash. Six copied
contradictions reject per mode: lost custody, late authority, stale typed identity,
two writers, bad PNG bytes and repeated submit.

## Preserved collection/readback corrections

The exploratory three-method check passed; only full stdout/stderr retained.
The first complete normal suite passed17 methods and saved raw, then the copied
collector expected a nonexistent parent cancel-thread field and raised KeyError.
That driver has only a stdout reader. Initial raw/streams and exact collector
source remain; final collection handles the new driver and prior pipe cells.
The original copied CONDITIONS scope string says synthetic backend; SCOPE_NOTE
separates actual production backend code from fake platform/query/capture.

The first independent-reader mutation check accepted a stale typed-observation
identity because it checked only full-observation identity. Its exact source is
preserved; explicit typed/full identity and sequence joins now reject it. This
is a reader repair with unchanged raw, not a rerun or repaired experiment.
These initial tracebacks were seen in tool output, not independently saved as
stderr; SCOPE_NOTE records the limitation. Final collection/readback stderr is
retained. No failure is reclassified as live success.

## Remaining computer-control gates

This advances the previous fully synthetic backend pipe construction to the
actual selected ownership/query/release/capture code on Fake X. It does not
run the real session_map01_v12/v15 main, game, native X transport, full V39/model,
public MCP, actual pixels, physical release bounds or independently useful task
effects. It is a separate selected-backend composition, not proof that all
prior helper/semantic/transport properties hold together in one live run.
No GUI/native input/model/provider/WSL/container/allocation or old producer ran.
#59/#57/#17 remain open. Actual session/native failure, independent task effects,
finite live recovery and matched efficiency/transfer still require qualification.
