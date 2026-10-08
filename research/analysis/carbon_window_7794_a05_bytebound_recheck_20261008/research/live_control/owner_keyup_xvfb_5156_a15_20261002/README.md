# Issue #5156 allocation-15: Xvfb explicit-up and cancellation record join

Status: **STOP — candidate failed; auditor not run; no retry.** Preserve A13 and A14 STOP evidence unchanged; never retry any consumed allocation.

## H / T / D / C / U

**H.** Candidate-local timestamps around existing v10 KeyRelease/XSync operations join explicit key-up calls by occurrence, owner, intent, and key. Cancellation cleanup can be captured by writing to the actual worker-owned list (wrapper._inner.records), then selected by exact admission identity and cancelled reason.

**T.** In one private Xvfb: single W down/up; W+A down, reject stale different-intent W-up without releasing W, then owning W/A ups; finally admit W, cancel, reject A admission, and observe autonomous neutral cleanup. Require verified-neutral owner release plus neutral keymap between first two leases.

**D.** Three explicit-up rows have nested caller/owner timestamps and down/up keymaps with identity joins; stale W-up is rejected and leaves W down; cancellation has exactly one row joined by occurrence, intent, owner, keycode and cancelled reason, ordered owner timestamps, W down-before/up-after and a verified neutral owner record. Both teardowns are neutral, authority remains false, and processes stop cleanly. Independent raw auditor accepts positive control and rejects identity, timestamp, keymap, stale, cancel, and teardown corruptions.

**C.** Cached image map01-attack-start-gate-4223-t8:20261001, pinned ID sha256:d8c51b45569cc4fdf0f5d82ae285c3fbb20fae8525d6fab0cebadca171b3bebe, linux/amd64 on OrbStack ARM64 emulation. Network none, no pull/build, private Xvfb, no request reorder or extra X11 query. Construction-only wrapper persistence test must use the same mutable worker-list selector as runtime instrumentation and prove its read-only snapshot property observes the appended sentinel.

**U.** XSync does not prove physical hardware key-up or application delivery/usefulness. No physical desktop, game/MAP01, provider/model, GPU, task-effect, safety/effectiveness, latency, human-tempo or transfer claim.

## Predecessor results and A15 correction

A13 candidate failed retrieving cancellation evidence from a Lease-local sink; candidate exit 1, auditor not run. A14 then appended through transition-owner v3's records property, which returns a copy; its generic owner records confirmed cleanup, but no joined measurement row. Candidate exit 1, auditor not run. Both exact raw outputs and STOPs remain in their own branches/PRs; neither is changed or rerun.

A15 selected mutable worker storage through wrapper._inner.records. Its construction test exercised this selector against the transition wrapper object but did not exercise the selector from within the wrapped worker method. In actual execution the injected code runs in the inner worker itself; its self is already the worker and has no _inner. Thus the first explicit-up candidate call failed before any release observation, and cleanup returned a failed record. The method-body integration seam was not represented by the construction test.

## Source and execution controls

The four runtime modules must match the exact base Git blobs. serialize_release.py is a local join helper copied from unmerged A11 commit 860c42dab79f723226ad06085133879b7426a91d, not claimed as main. FREEZE.json pins main SHA, exact dependency byte hashes, scripts, image and one-shot limits.

Construction runner self-test and independent auditor positive/14 corruption controls passed. One formal candidate exited 1 on the first explicit-up because worker-local self._inner was absent. Auditor NOT RUN; retries 0. Raw/logs/status and STOP are preserved. Do not repair or rerun A15. Do not use or modify the shared unjuno-native-ci-6092 container.

## Formal outcome

- Candidate: **FAIL**, one execution, exit 1; independent auditor: **NOT RUN**; retries: **0**.
- Exact error: RuntimeError: input owner does not expose mutable worker records.
- Evidence: raw.json SHA-256 d28687d7f3e608dcb82adfcf48e2fa8955910b95c4a3ddb57537df953c1c5874; stdout SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855; stderr SHA-256 a9b188d18d3b79a2b7233a9cc5f1ce42faa32d242dd5f8d96e5844fd98e0e352.
- One W admission is observed down. No explicit-up measurement was recorded. owner_cleanup is failed; owner_thread_stopped and processes_clean are not asserted.
- A successor must call the record helper using the worker method's self.records directly, while wrapper-side collection may read the wrapper records snapshot. Add a construction smoke that executes the injected release call on the actual instrumented worker/wrapper path before formal allocation.
