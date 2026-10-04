# Cancellation batch per-key release interval composition

This construction check closes a source/telemetry gap found during the current-main #59 integration audit. The selected release owner now records one conservative interval for each key it releases while cleaning up a cancelled lease, and the V13 no-authority `input_released` event retains the exact owner record.

**H — Hypothesis.** For each held key released by cancellation cleanup, `owner_release.key_release_intervals_ns` contains exactly one row with the matching keycode and integer bounds from that key’s XTest release request start through the completion of the shared XSync. The bound ends no later than owner key-state verification. `ExecutorV13` publishes the same owner record inside `input_released`, with no input authority grant.

**T — Test.** A fake-Xlib owner-thread test admitted two keys, set cancellation, and checked both request intervals, key identities, order, verified-empty state, and propagation into `input_released`. The exact pre-repair source was first tested after staging the missing `lease.py` dependency.

**D — Result.** The pre-repair baseline failed because `key_release_intervals_ns` was absent. The repaired candidate passed the new owner/publication regression and 15 adjacent explicit-up, transition-receipt, V13 watcher, and release-batch tests (16 total). `py_compile` and `git diff --check` also passed. The initial incomplete baseline staging attempt is retained separately as STOP; it lacked `lease.py` and made no claim about the source defect.

**C — Competing interpretation.** A single XSync completion timestamp conservatively bounds each request; it does not identify the physical key-up instant or when an application consumed it. Independent key-state verification remains a distinct assertion.

**U — Uncertainty and limits.** This is fake-Xlib/source-composition evidence only. It does not test a real X server, OS input, physical key transition, GUI/game effect, model, useful feedback, full session, or bounded recovery. The candidate suite ran on the macOS host because the configured OrbStack Docker daemon returned an unsupported content-store operation during image listing. No game/GPU allocation was used. The private #59 game lane remains unassigned.

The exact freeze, commands, source hashes, raw output, and an audit script are in this directory. Historical STOP and FAIL outputs are preserved and not relabeled as candidate results.

## Partial cancellation release failure follow-up

A second fake-Xlib experiment injected an accepted-then-raised per-key release request before XSync. On the prior source, this produced no cancellation receipt or lease interruption until later cleanup; the raw failing assertion is retained. The repair now emits an explicitly unverified `owner_release` record with no release intervals, conservatively retains the held keycodes, and wakes the lease watcher. The V13 adapter maps that record to `input_release_unverified`; it grants no authority. A subsequent close attempt independently verifies that both keys are up. The ordered adjacent suite still passes all 18 tests. See `partial_release_failure/REPORT.md` and its frozen consistency audit. This remains fake-Xlib evidence, not real X11 or task-effect validation.


## Test-isolation follow-up

An independent review found that the fake-Xlib tests evicted cached owner/transition modules without restoring earlier entries. A sentinel regression failed against the original test, then both owner fixtures were updated to restore saved module entries. The ordered 18-test single-process follow-up passes with the new interval test before and after the adjacent transition, cancellation, batch, and V13 suites. Raw outcomes and hashes are retained under `module_cache_isolation/`. This repairs test isolation only and does not change the production behavior or construction-only scope.


## Synthetic keymap-change follow-up

A separate fake-Xlib probe tests whether a synthetic symbol-to-keycode map change breaks the admission-to-release identity join. With the resolved keycode retained at admission, remapping W after both keys were admitted preserved `[87, 65]` in both admissions and cancellation intervals; remapping W/A before the second admission produced `[87, 77]` on both sides. Both cancellation cleanups verified empty state. This supports the narrow claim that an already-held physical keycode remains stable for release across later map changes. A keymap epoch is still needed to interpret what symbol an admitted keycode represented.

The probe loads pinned source at `1721f7cb2a47f53641bc7c93effe2a2b817013cd` and applies an in-memory-only receipt mutation. It is synthetic evidence: no real X server mapping delivery, keyboard layout, physical key, game effect, model, or recovery was tested. The source, result, and inner audit are under `keymap_epoch_stability/`; the parent audit verifies the frozen probe and inner audit result.

## Explicit key-up after a map change

A separate fake-Xlib regression exposed a normal-release defect. The pinned source admitted W as keycode 87, then re-resolved W after the synthetic map changed it to 77. The explicit key-up therefore left physical code 87 down. The candidate now retains the resolved keycode per active lease and logical key, includes it in the admission receipt, and uses that same code for explicit key-up. The regression confirms the physical state empties and admission/key-up receipts both identify 87; the explicit-up request-start and XSync-return timestamps are ordered. The ordered owner/release/V13 suite passes 20 tests. See `explicit_keyup_remap/` for the pinned baseline failure, candidate result, STOP from an incorrect script invocation, and independent audit.

This corrects key identity for paired key-down/key-up across a later mapping change. It does not prove real X11 mapping-change delivery, the semantic meaning of the remapped key, physical transition timing, application/game effect, model behavior, bounded recovery, or live threat response.
## Additive unmatched-keyup alias follow-up

At the explicit-keyup candidate from PR #7529, a new fake-Xlib case admitted
`W` at code 87, remapped unadmitted `A` to code 87, and requested `up(A)`. The
candidate released W despite there being no admission for A. The follow-up
changes explicit key-up to use only the `(lease, logical key)` admission map;
unmatched key-up is a no-op. The exact prior source fails the retained test and
the candidate passes it. A 22-test ordered adjacent suite also passes with the
new regression at both ends. See
`unmatched_keyup_alias/README.md` and `unmatched_keyup_alias/RESULT.json`.

The original explicit-remap evidence remains unchanged. Its archived source
re-audit is `explicit_keyup_remap/AUDIT_v2.json`; it checks the retained result
against the pinned pre-follow-up candidate instead of requiring that old source
to remain the current runtime file.

This closes one logical ownership edge in fake-Xlib construction only. It does
not establish real X11 behavior, per-key physical transition times, useful
feedback, game effect, bounded recovery, or live threat response. The matched
Issue #59 live allocation gate remains open.

## Additive keymap-eviction follow-up

Review of the pushed alias fix found that explicit key-up still resolved the
current keysym before reading its stored admission. A frozen regression admits
W as code 87, changes the current mapping to unavailable, then requests
`up(W)`. The exact pushed source fails with `ValueError` and leaves code 87
down; the candidate reads the admitted code directly, releases it, and emits a
matching receipt. The ordered adjacent owner/release/V13 suite passes 24 tests.
Evidence and independent audit are under `keymap_eviction/`.

The two key-up repairs establish a narrower fake-Xlib invariant: explicit up
uses only a same-lease, same-logical-key admission record and does not depend on
the current symbol map. They do not establish real X11 remap delivery,
per-key physical transition time, useful task effect, recovery, or live threat
control. Issue #59's matched live allocation remains unassigned.
