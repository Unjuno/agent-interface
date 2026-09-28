# Successor #4304: global target uniqueness beyond an unchanged inline-cache patch

Status: pre-formal freeze candidate only. No formal case has run for allocation 02.

## Lineage and ownership

This is allocation `inline-cache-uniqueness-4304-20260928-02`, a fresh successor to the immutable STOP `inline-cache-uniqueness-4304-20260924-01` in Issue #4304. It does not edit or pool the closed #4260 result, allocation-01 freeze/partial rows, or any shared runtime. Allocation 01 stopped at `formal-0-06` before warm input when Python-Xlib `String8` supplied `str` for an all-black ROI; its first six rows remain descriptive only. The only hypothesized repair is lossless UTF-8 normalization at the capture adapter. `src/normalize.py` is byte-identical to the current-main X11 String8 study helper; no production runtime path was changed. The live and byte-representation construction tests below exercise this boundary.

Own branch: `research/inline-cache-global-uniqueness-4304-v2-20260928`.
Owned repository path: `research/integration/inline_cache_global_uniqueness_4304_v2/**`.
Frozen base: `main` at `d8ca8bfed9cd8d84201c91645e4ed25364181d3f`.
Local execution: Arch Linux WSL2 on this PC; private Xvfb only. No Docker invocation, GPU/CUDA, model/provider, host desktop, user data, or network experiment. GitHub MCP is used only for coordination/publication.

The branch is additive. Do not include `scratch/`, predecessor restore material outside `lineage/`, or any file outside the owned path in a commit. Preserve every STOP and partial output losslessly.

## H — hypothesis

For an intent requiring exactly one matching target in the current declared window domain, an unchanged cached local patch is insufficient evidence of global uniqueness: a distant indistinguishable target can appear while the cached bytes and window-incarnation binding remain unchanged. A `LOCAL_PATCH` warm guard may therefore cause an ambiguity-violating effect. A `GLOBAL_UNIQUENESS` guard that reacquires the complete current domain should refuse duplicate, absent, or unavailable evidence while retaining effects for stable, unrelated-change, and uniquely relocated cases.

This tests the composition of XGetImage, policy proposal, XTEST delivery, and independently app-observed event/effect. It is not an inference that current production code has a defect.

## T — treatment and apparatus

### Host and input boundary

Use only the frozen local Arch Linux WSL2 environment described in `ENVIRONMENT.json`; verify every listed package/version, kernel, Python, and relevant Xlib source digest immediately before formal launch. The experiment uses a fresh private Xvfb per session and one separate cooperative Xlib fixture application. A mount namespace overlays WSLg's read-only `/tmp/.X11-unix` socket mount with a disposable private tmpfs, then drops to uid/gid 1000. Never alter the WSLg X0 socket or the native Windows desktop. No package update, install, network access, GPU, CUDA, model load, Docker daemon, or container is part of the formal run.

Each 320x120x24 mapped, unobscured window contains 16x16 exact green target rectangles over black, with an optional 12x12 blue nuisance. A cold complete-frame observation verifies one target and caches its rectangle, exact patch digest, and binding. Binding generation represents the X window incarnation; it deliberately remains unchanged within each session. The fixture actor receives scenario commands, but the policy child receives only the frozen byte/image/binding/cache contract. The independent scorer-only witness is not supplied to policy.

### Policies

- `LOCAL_PATCH`: compare the fresh 16x16 ROI bytes with the cached exact patch. On a match, propose the cached center. On mismatch, deopt to a complete current-frame unique-target search; if complete evidence is unavailable, yield.
- `GLOBAL_UNIQUENESS`: always require a complete current declared-domain frame and exactly one target; otherwise yield.

Both only emit a point proposal. The fixed driver turns a proposal into ordinary XTEST motion/press/release. The application itself journals delivered events and increments its effect journal only for a matching press/release pair. The policy receives no task input authority.

### Fixed design

Six scenarios × two policies × two fresh repetitions = 24 sessions and 24 warm decisions. Batch 0 uses scenario order `STABLE, UNRELATED, DUPLICATE, MOVED, ABSENT, DUPLICATE_FULL_UNAVAILABLE`, then arms `LOCAL_PATCH, GLOBAL_UNIQUENESS`; batch 1 reverses both orders. Exact runner hashes and schedule are in `FREEZE.json`.

1. `STABLE`: original target remains.
2. `UNRELATED`: blue nuisance appears outside the cached patch.
3. `DUPLICATE`: a distant identical target appears; the original ROI and binding remain unchanged.
4. `MOVED`: only one target remains at the distant location.
5. `ABSENT`: no matching target remains.
6. `DUPLICATE_FULL_UNAVAILABLE`: a duplicate exists and local ROI is available, but complete current-frame evidence is unavailable to either policy; the independent scorer still retains its own witness.

The fixture mutation and XSync finish before observation. The actor is quiescent through proposal and effect, so this is not a check/use race or an XGrabServer experiment. Preserve complete raw image bytes, capture roles/receipts, exact policy wire, actor command/ack/event/effect journals, input edges, process commands/exits/stderr, neutral-state checks, display/auth cleanup, source hashes, and all STOP/partial evidence.

### Construction gates already observed

- Local WSL CPU-only suite: 11/11 tests passed (7 policy-contract and 4 `String8` normalization tests). The normalization fixtures cover all-zero black bytes represented as `str`, valid multibyte UTF-8 `str`, invalid/binary bytes, and other bytes-like input.
- Excluded live construction allocation `construction-02`: four cases (STABLE/LOCAL_PATCH; MOVED/LOCAL_PATCH; DUPLICATE/GLOBAL_UNIQUENESS; ABSENT/GLOBAL_UNIQUENESS), all complete. The black moved ROI returned `bytes` under Python-Xlib 0.33 in this apparatus. It is not formal evidence.
- Independent construction-only raw audit: PASS, 340 checks, 0 errors.
- Construction copied-evidence controls: PASS, 15/15 changed corruptions rejected, including unexpected Xvfb stderr.
- `construction-01` Xvfb-ready timeout and `construction-03` unsupported `-kb` option are retained as STOPs, not erased or reclassified. `construction-03` stopped before observation/input. The Xvfb's fixed XKB warning is recognized by exact SHA-256 in the independent auditor; actor and policy stderr must remain empty.

The construction records and stdout/stderr are immutable. Any further apparatus change requires a new excluded construction output and an amended pre-formal freeze before any formal row.

### Formal invocation boundary

Before formal: read back this exact branch's commit/tree and every frozen blob from GitHub; verify the GitHub `main` ref still equals the frozen base; verify all source/environment hashes, output path absent, no active process/output collision, Xvfb/namespace readiness without task cases, and all construction gates above. Formal output root is `research/integration/inline_cache_global_uniqueness_4304_v2/results/formal-02/` and must be absent before first invocation. The invocation creates the root and batch directory exclusively.

Run exactly one invocation for batch 0, under a 120-second WSL `timeout` outer bound. Batch 1 is permitted exactly once only if batch 0's retained `BATCH.json` is `COMPLETE`, all twelve `RAW.json` files exist, and the no-overlap/current-main/source checks still hold. Each output directory is created exclusively by the runner. A first STOP, timeout, exception, missing output, source drift, or changed main ends this allocation; do not retry, replace, exclude, pool, tune, or substitute. Do not invoke any old seed, formal result, or adapter state.

After a complete pair, run the separate CPU raw-only auditor (which imports no candidate runner/policy/actor) exactly against the frozen output; then run the copied-evidence corruption harness. Preserve their outputs, command receipts and hashes. Any audit rejection, ineffective control, missing evidence, or incomplete denominator is HOLD/STOP, not a scientific PASS/FAIL. Publish exact result/failure, source/environment/output hashes, commands, audit and controls to Issue #4304 and a reviewable additive PR. No promotion by comment alone.

## D — decision rule

`PASS_INLINE_CACHE_GLOBAL_UNIQUENESS_BOUNDARY_SCOPED` only if all 24 first outcomes reconcile and all of these hold:

- cold unique-target acquisition succeeds 24/24 and emits no input;
- both policies produce exactly one correct application-observed effect in STABLE, UNRELATED, and MOVED (12 effects), with MOVED at the new center;
- `LOCAL_PATCH` emits ambiguity-violating effects in all four DUPLICATE and DUPLICATE_FULL_UNAVAILABLE rows while its original patch and binding are unchanged;
- `GLOBAL_UNIQUENESS` emits zero warm input/effect in the six DUPLICATE, ABSENT, and DUPLICATE_FULL_UNAVAILABLE rows;
- `LOCAL_PATCH` refuses both ABSENT rows;
- candidate ambiguous/absent/unavailable admissions = 0 and authority grants = 0;
- every click has exactly one app-observed press/release; final key/button state is neutral; every owned process exits 0; displays, locks, and auth files are cleaned up;
- independent raw-only audit returns `errors=[]`; all 15 prospectively frozen copied-evidence controls are effective and reject without crash/no-op.

Any candidate unsafe input/effect is a scientific failure. Missing provenance, bytes, process evidence, denominator, incomplete rows, or ineffective controls is HOLD/STOP. A safely refused ambiguous operation is safe incompletion, not task success. Report acquired/scanned pixels and bytes per policy; no speed-benefit threshold. The weaker local policy remains unacceptable under the preregistered unique-target intent even if the boundary hypothesis is confirmed.

## C — controls and identification limits

The authored intent and declared search domain define uniqueness. Exact colored rectangles are not semantic detectors. Full-window pixels establish only fixture-visible uniqueness and do not reveal off-window, occluded, hidden-app, or undocumented semantic dependencies. The guard-scope factor changes available evidence, not an equal-information algorithm speed comparison. Cooperative actor quiescence is assumed; this does not provide an atomic currentness guarantee. This is a single WSL2 host and synthetic fixture, not evidence about physical HID or arbitrary applications.

The CPU-only independent auditor reconstructs target components with a 4-connected flood-fill distinct from the candidate row-run algorithm, verifies raw image bytes/digests/provenance, actor and policy wire, event/effect lineage, process exits, cleanup and neutral state, and recomputes the full schedule/decision. Corruption controls operate on deep-copied evidence; frozen raw records are never changed.

## U — scope and integration

This is scoped evidence relevant to the observation/guarded-action boundary in ROADMAP O3 and #2789. It makes no automatic guard synthesis, model/token/latency, natural duplicate-frequency, live product, authorization, cross-platform, or broad capability claim. It does not close #3311 or any global roadmap item. Integrate only as additive research evidence by PR; retain all prior results and STOPs unchanged.
