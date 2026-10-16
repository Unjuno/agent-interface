# Issue #5156 allocation-16: explicit-up and cancel record owner/wrapper integration

Status: **STOP — candidate failed; auditor not run; no retry.** A13/A14/A15 remain immutable STOP allocations; none will be rerun.

## H / T / D / C / U

**H.** Candidate-only observation around existing v10 KeyRelease/XSync calls can join explicit-up intervals. Since instrumentation executes inside the worker method, it appends directly to that worker's self.records. The transition wrapper exposes a read-only snapshot owner.records; cancellation extraction reads that snapshot after the call.

**T.** Private Xvfb full candidate: single W down/up; W+A with stale different-intent W-up rejected and then owning W/A releases; W cancellation with queued A admission rejected and autonomous W cleanup. Verified-neutral owner release plus neutral keymap between first two leases.

**D.** Three explicit-up joins with nested caller/owner timestamps, matching admissions and down/up keymaps; stale W-up rejected while W remains down; one cancel cleanup row matched by occurrence, intent, owner, keycode, reason, ordered timestamps and W keymap down-to-up; verified neutral owner cancellation record; neutral between-case teardowns; authority false and all processes stopped. Independent raw auditor accepts positive control and rejects frozen identity/time/keymap/stale/cancel/teardown mutations.

**C.** Cached map01-attack-start-gate-4223-t8:20261001, pinned sha256:d8c51b45569cc4fdf0f5d82ae285c3fbb20fae8525d6fab0cebadca171b3bebe, linux/amd64 on OrbStack ARM64 emulation; network none, no pull/build, private Xvfb. No release request reordering or extra X11 query. Construction-only smoke uses the exact instrumented owner source and vendored transition wrapper: one explicit W up and one cancellation W cleanup; both measurement rows must be readable from the wrapper snapshot, keymap neutral, generic owner cleanup verified, and owner thread stopped.

**U.** XSync does not demonstrate hardware release or application delivery/usefulness. No physical desktop/game/MAP01/model/provider/GPU/task-effect/safety/effectiveness/latency/transfer claim.

## Predecessor evidence and A16 boundary

A13 failed while reading asynchronous cancellation evidence from a lease-local sink. A14 appends through a copy-returning wrapper property and lacks the measurement row. A15 called wrapper._inner from inside the inner worker method, causing failure on its first explicit-up. Each has exit 1, auditor not run, zero retries, and a separate preserved raw/STOP/PR. None is treated as a scientific result.

A16 corrects the execution context: injected worker code appends to self.records; outer runner reads the wrapper's owner.records snapshot. Before formal execution, run both candidate pure construction controls and a separate real Xvfb integration smoke through the exact patched worker plus transition wrapper. If the actual explicit-up/cancel rows do not persist through that wrapper, or cleanup/process gates fail, no formal candidate is allocated.

Construction results: runner self-test PASS; actual worker/wrapper Xvfb smoke PASS with one explicit-up row and one cancellation row visible via wrapper snapshot, verified neutral cleanup and stopped owner thread; independent auditor synthetic positive PASS and 14/14 corruption controls rejected. The first smoke attempt failed before formal allocation because its diagnostic omitted component observations and incorrectly required Xvfb exit -15; the check was expanded and accepts normal exit 0 as well. The corrected smoke passed. The one formal candidate later failed at cancellation record selection despite three explicit-up rows, stale rejection, and two neutral teardowns.

## Source, freeze, and run limits

FREEZE.json pins exact main base, source Git blobs, dependency byte hashes, candidate/auditor hashes, image and one-shot limits. serialize_release.py is disclosed as a local helper copied from unmerged A11 commit 860c42dab79f723226ad06085133879b7426a91d, not current-main source.

Candidate maximum 1; independent raw auditor maximum 1 only after candidate exit 0; retries 0. Any formal nonzero exits STOP, preserve raw/logs/status, do not audit or retry. Leave shared unjuno-native-ci-6092 untouched.

## Formal outcome

- Candidate: **FAIL**, one execution, exit 1; auditor: **NOT RUN**; retries: **0**.
- Failure: RuntimeError: cancel cleanup did not produce exactly one release receipt. The wrapper snapshot filter returned no matching row in the formal candidate; raw does not include the complete owner-record snapshot, so the specific mismatched identity field cannot be reconstructed. Do not speculate beyond this evidence.
- Raw SHA-256: 1d03cadf2eac3821fa05fde3051e53a034047558ba687f1532dc21ceb8644dfa. stdout SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. stderr SHA-256: 76f5d3c783cd090ec5a88ece48c887331b4afa3e40bb86e543a1f807b3e5527f.
- owner_cleanup clean. owner_thread_stopped and processes_clean are not asserted because candidate failed before those gates.
- Construction smoke previously found one matching cancellation row through the same wrapper path, so this formal mismatch is currently unexplained. A successor should persist the complete wrapper record snapshot before selection and emit per-field diagnostics before any candidate gate can throw.
