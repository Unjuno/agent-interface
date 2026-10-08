# Allocation 18 preregistration — WSLc explicit key-up bracket

Parent: Issue #5156 (successor to #443), direct prerequisite for #1907 / #59.
Preserve A13–A17 and all prior STOP/HOLD records unchanged. A17 remains unrun and frozen for its OrbStack route. This A18 is a fresh, owner-directed WSLc runtime allocation; it does not consume, supersede, or alter A17.

Allocation: `MAP01-OWNER-KEYUP-BRACKET-5156-WSLC-20261002-18`
Base main: `3f78141830f22462cbefd5a2fac906668339d9a4`
Branch/path: `research/5156-keyup-bracket-wslc-a18-20261002` / `research/live_control/owner_keyup_xvfb_5156_a18_20261002/`

## H — hypothesis

On a private Xvfb server inside Microsoft WSLc, candidate-local monotonic timestamps around the existing InputOwner v10 XTest `KeyRelease` request and its `XSync` return can be joined to the unchanged transition-v3 caller bracket by occurrence, owner, intent and key, while preserving explicit key ownership, cancellation, verified neutral cleanup, and zero input-authority expansion.

## T — one-shot bounded experiment

Use the exact source files from base main: InputOwner v10 (blob `341b3c01649943ddaad5f28431a792c4889cc36e`), transition owner v3 (blob `0ea631abcf6272f0538a9ef9198ad8069b47b464`), and executor v3 (blob `2b072454fd81c41bf9e025217afc78020c7059de`). Make only additive candidate-local telemetry changes; do not change admission, lease, cancellation, release order, or wrapper behavior.

A private disposable Xvfb display runs three cases:

1. Admit W and explicitly release W.
2. Admit W+A under one intent; reject a stale different-intent W-up without a receipt and while W remains down; explicitly release W then A.
3. Admit W, request cancellation, reject A under the cancelled intent, observe the asynchronous owner cleanup receipt and verified neutral keymap.

A separate raw-only auditor checks full candidate evidence, identity joins, boundary order, pre/post keymaps, stale-up rejection, cancellation reason, neutral teardown, process exit, and false authority flags. Candidate cap=1; auditor cap=1 only if candidate exits 0; retries/substitutes=0. Any failed start gate is retained as STOP without a candidate retry.

## D — decision gates

`PASS_OWNER_THREAD_KEYUP_BRACKET_WSLc_SCOPED` requires exactly three explicit-up occurrences, each matched to one owner-thread row and satisfying `caller_start_ns <= owner_release_start_ns <= owner_sync_return_ns <= caller_return_ns`; each key must be down before and up after its release. The stale foreign-intent release must be rejected, produce no owner release row, and leave W down until the owning intent releases it. Cancellation must reject A and yield exactly one W owner-cleanup row with ordered key-release/sync timestamps, matching owner/intent/key/reason, verified neutral keymap, and no caller-nested claim. Both inter-case teardowns must verify neutral; all owner/Xvfb processes must exit; every raw artifact/hash must verify; independent audit must report zero errors and reject all frozen mutations.

A setup/source/image/output mismatch is STOP. Any unsafe admission, foreign release, missing release, non-neutral terminal state, authority increase, or auditor disagreement is FAIL/STOP as frozen; no retry.

## C — conditions and risks

CPU-only, one private Xvfb server, one Linux/amd64 WSLc container, network disabled during construction smoke/candidate/audit after image creation; one CPU and 512 MiB requested. WSLc may not enforce swap/cgroup limits, so no resource-enforcement claim will be made. Image build uses the already cached digest-pinned Python 3.12.14 base and records installed package versions and the resulting image ID. No host desktop, physical keyboard, GPU, model/provider, game/MAP01, or task input is touched.

## U — limits

XSync brackets X-server processing; it is not an exact hardware key-up time or proof of application delivery/usefulness. One Xvfb fixture cannot establish live MAP01 occupancy, task effect, safety rate, recovery quality, latency benefit, human tempo, or cross-domain transfer. This does not close #5156, #1907, or #59.

## Owner authorization and resource check

The repository owner instructed this task in chat to run container work in WSL and complete the current experiment. WSLc was available; the read-only `wslc ps` inventory showed no running containers immediately before this allocation. This is the single bounded CPU-only WSLc lane for this allocation. It is not inferred from GPU idleness and does not authorize work on any other allocation.
