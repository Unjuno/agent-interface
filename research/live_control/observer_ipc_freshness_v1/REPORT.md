# Issue 3944 — retained pre-formal publication STOP

Parent: #2117. Intake main: b2457b746a6df06f6536585dfe2ab937aff639f4.
Branch: research/issue-2117-observer-ipc-freshness-20260922.
Additive scope: research/live_control/observer_ipc_freshness_v1/.

## Disposition

STOP_PREFORMAL_PUBLICATION_BLOCKED. Scientific outcome: NONE.
Formal invocation count: 0. Short-pulse experimental cases: 0.
No model/provider calls, input injection, host desktop interaction, or predecessor reruns occurred.

An attempt to publish the exact source freeze as a comment on Issue #3944
was blocked by the connected tool's safety check before a comment receipt
was returned. The response stated that the request's safety could not be
verified. No comment publication is claimed. The blocked comment operation
was not retried or routed through a substitute endpoint. Because the Issue
required that publication before formal execution, the formal command was
not invoked. This is a publication-infrastructure STOP, not a scientific
failure of process-isolated observation. Source preparation and construction
checks must not be relabeled as the planned 40-case experiment.

## Executed construction

Construction output: construction-01/construction.json.
Status: PASS_STATIC_CONSTRUCTION.
Exact static target-pixel counts: 0, 511, 512, 1024, all correct.
Native/Python monotonic clock enclosure: PASS.
Separate-process static-zero JSONL observation path: PASS.
Consumer-interpreter CPU-load thread readiness and positive CPU exposure: PASS.
Private Xvfb pinned CPU2: terminated cleanly, exit 0, socket absent.
Independent auditor synthetic checks: positive PASS and delayed-delivery HOLD
classified correctly; all 11 corruption controls rejected. These are synthetic
construction controls, not live short-pulse observations or scientific evidence.

## Frozen local source

- native.c: 2289 bytes; SHA256 5297e1252113ab4d91c58bd5e7b9462af155979cc44259d42eb98c0d9ce35975
- native.so: 16024 bytes; SHA256 e4b6d268a670005c6f5646db9c73786e6092688e25b3ea56c2f1fcf951df67cd
- study.py: 15958 bytes; SHA256 5aeb0b3d7663606bbd06d1caa20586272ac3ee1ad196610855f3cfc66e29e34e
- audit.py: 16105 bytes; SHA256 0bd2cbf81736c32de80e33bdf85c349596dcccba002968340ee72826448d67a6
- FREEZE.json: 4653 bytes; SHA256 0e03ab655969afed3670907bf398d8580b3d8d6f9ad71dcd2512b93aade3541c

native.c is an exact copy of predecessor Git blob
92b2ca11117f6bcb80f45dbac62e16d62bb4f6fd, not a rerun of #361.
Build completed: cc -O2 -Wall -Wextra -Werror -shared -fPIC native.c -lX11 -o native.so.

## H/T/D/C/U retained

H: separate-process acquisition may preserve short target captures despite a
CPU-bound thread in the consumer, but JSONL/pipe/consumer delay may erase recent
delivery. Capture and receive age are different quantities.
T: the planned single 40-case block (INLINE/PROCESS x IDLE/THREAD, ten blocks)
was NOT executed. Only static construction and synthetic audit checks ran.
D: no scientific PASS/HOLD/FAIL is assigned; the pre-formal publication gate
stopped the allocation. Historical #455/#479 and #462/#493 remain unchanged.
C: OS scheduling, CPU placement, interpreter sharing, and IPC can explain any
future measured difference; construction does not distinguish those effects.
U: scientific timing, short-pulse capture, age-qualified receipt, real model
consumption, useful task effects, tokens, and integrated benefit remain unknown.

## Integration and handoff boundary

This STOP record does not replace the blocked pre-formal comment, authorize the
formal run, complete #2117, or qualify any runtime change. No shared source,
workflow, goal, or historical result changed. Preserve the prepared runner,
auditor, freeze and construction evidence for review. Any future allocation
must first resolve its publication gate and recheck source/environment and
parallel ownership; never infer that this allocation executed from its freeze.

The full prepared source and construction bundle is retained as a conversation
artifact; this report alone is not a claim that remote raw-byte publication
is complete. Repository-wide ROADMAP remains open.
