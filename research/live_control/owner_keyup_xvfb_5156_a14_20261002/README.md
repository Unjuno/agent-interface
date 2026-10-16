# Issue #5156 allocation-14: explicit-up bracket and cancellation owner record

Status: **STOP — candidate failed; auditor not run; no retry.** A13 remains immutable in its own branch/PR and neither allocation is retried.

## H / T / D / C / U

**H.** Candidate-local timestamps around existing v10 KeyRelease/XSync operations can join explicit key-up calls by occurrence, owner, intent, and key. Autonomous cancellation cleanup is observable as an owner-only record and must be joined to the cancelled admission without reading a Lease-local asynchronous sink.

**T.** On one disposable private Xvfb server: (1) single W down/up; (2) W+A down, reject stale different-intent W-up without releasing W, then explicitly release W and A; (3) admit W, request cancellation, reject A admission, and observe autonomous W cleanup. Between the first two lease scenarios, use existing owner release and require verified neutral receipt plus neutral keymap.

**D.** Three explicit-up joins meet caller_start <= owner_release_start <= owner_sync_return <= caller_return, matching each admission identity and down/up keymaps. Stale-up is rejected and leaves W held. Cancellation yields one owner cleanup row matched by occurrence, intent, owner, keycode and reason=cancelled, ordered owner timestamps, W down-before/up-after, verified neutral owner record, and rejected A admission. Teardown receipts for first two cases are verified neutral. Authority flags false; owner and Xvfb stop cleanly. Independent raw auditor accepts synthetic positive control and rejects identity, timestamp, keymap, stale, cancellation, and teardown corruption.

**C.** Candidate-only instrumentation; no request reorder, added X11 query, or admission/release predicate change. Cached pinned linux/amd64 image under OrbStack ARM64 emulation, private Xvfb, no network, no image pull/build. Construction fixtures are not formal experiment outcomes.

**U.** XSync brackets server processing, not hardware key-up or application delivery/usefulness. No physical desktop, game/MAP01, model/provider, GPU, task-effect, safety/effectiveness, latency, human-tempo, or transfer claim.

## A13 learning / A14 correction

A13 failed only after three explicit-up observations, stale-up rejection, and two neutral case teardowns. Its runner attempted to retrieve asynchronous cancellation cleanup from the cancelled Lease-local instrumentation list; raw owner records show owner cleanup was logged, but A13 lacks a joined cancellation row. Candidate exit was nonzero, so its independent auditor correctly was not run and the allocation is consumed. Exact A13 raw and STOP remain in the A13 branch/PR.

A14 intended to send each candidate-only observation to the owner record stream and match cancellation by identity. Its extraction self-test passed against a normal list, and the independent auditor's 14 corruption controls passed. In the actual integration, however, transition-owner v3 exposes records through a property that returns a copy; appending to self.records mutated only a temporary list. The actual worker list is self._inner.records. Consequently, cancellation again lacked a joined measurement row even though cleanup remains separately represented in the wrapper's generic records. The integration seam was not exercised by construction tests.

## Freeze and execution

FREEZE.json will identify exact main base, vendored Git blob/LF SHA-256 values, runner/auditor hashes, image ID, allocation, and invocation limits. The four runtime modules come byte-identically from that base. serialize_release.py is the disclosed local join helper copied from unmerged A11 commit 860c42dab79f723226ad06085133879b7426a91d; it is not represented as main source.

The pinned, network-none construction runner self-test passed; independent auditor synthetic positive passed and 14/14 corruption controls were rejected. The one formal candidate then exited 1 at cancellation-row extraction. The auditor was NOT RUN as required after nonzero candidate status; retries=0. The allocation is consumed. Raw, stdout, stderr, and explicit STOP are preserved. Do not repair or rerun A14.

No container build or pull; use exact cached image map01-attack-start-gate-4223-t8:20261001 (sha256:d8c51b45569cc4fdf0f5d82ae285c3fbb20fae8525d6fab0cebadca171b3bebe). Leave the existing shared unjuno-native-ci-6092 container untouched.

## Formal outcome

- Candidate: **FAIL**, one execution, exit 1; auditor: **NOT RUN**; retries: **0**.
- Exact failure: RuntimeError: cancel cleanup did not produce exactly one release receipt.
- Evidence: raw.json SHA-256 fd895700a3f0d7416926d1583a88e482fd9ab32775517eb10c2e9b0021a8380c; stdout SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855; stderr SHA-256 0e5c7b329c898444e795c5d2fe3969085755517b47e66c4fe2a44484ed6382de.
- The raw preserves all three explicit-up brackets, stale-up rejection, both verified-neutral case teardowns, cancellation rejection, and the terminal exception. owner_cleanup is reported clean; owner_thread_stopped and processes_clean are not asserted because candidate did not reach those gates.
- STOP cause: candidate instrumentation appended through transition wrapper records property, which returns a copy; actual worker storage is _inner.records. This observation from the failed integration is not a hypothesis pass or failure of the user-visible cleanup behavior.
- Any revalidation needs a separately preregistered successor and an integration construction test that proves a record appended through the actual wrapper persists in the underlying worker list before formal allocation.
