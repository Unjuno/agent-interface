# Cancellation receipts across release and verification failures

**H — Hypothesis.** Any exception during cancellation release must publish an explicitly unverified owner receipt promptly and wake the lease watcher. Intervals are valid only if shared XSync completed. A later cleanup retry may establish a separate verified release.

**T — Test.** The frozen fake-Xlib experiment admits `W` and `A`, requests cancellation, and runs two fault phases: the `A` release changes fake physical state then raises before XSync; the second phase completes XSync and makes the keymap verification raise. An owner-state read queues behind cancellation processing, records are inspected before close, and the experiment then closes to observe recovery. Both receipts pass through the V13 release-event adapter.

**D — Result.** The baseline failed: the cancellation path emitted no `owner_release` record and no interruption before close. After repair, both fault phases emit `verified=false` receipts listing both held keys, and V13 maps each to `input_release_unverified` with no authority grant. The pre-XSync failure has no intervals; the post-XSync keymap failure retains both request bounds. A separate close cleanup then records a verified release. The ordered adjacent suite passes all 20 tests.

**C — Competing interpretation.** The fake backend accepts the second request before raising, but real client/server error timing may differ. The implementation therefore treats every still-owned key as unverified and does not infer release from the exception or fake keymap. A post-sync query error preserves timing bounds but cannot establish physical release.

**U — Limits.** This is deterministic fake-Xlib evidence only. It does not establish real X11 request delivery, physical key-up timing, GUI/game response, or full-session recovery. The #59 live lane remains unassigned.

The RED/GREEN outputs, exit codes, exact source snapshots, and consistency audit are retained in this directory. Two harness stops are also retained: the first fake display lacked pointer coordinates, and the first ordered-suite invocation used a nonexistent module path. An initial baseline-override invocation loaded the candidate because the helper import changed `sys.path` precedence; that run was discarded, the loader order was corrected, and the RED traceback identifies the exact baseline file. The #59 live lane remains unassigned, so this does not verify real X11, application effect, or session recovery.
