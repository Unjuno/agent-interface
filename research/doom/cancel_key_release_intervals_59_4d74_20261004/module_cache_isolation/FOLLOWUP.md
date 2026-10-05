# Test module-cache isolation follow-up

An independent review of PR #7529 found that the new fake-Xlib owner test removed cached `input_owner_v12`/transition modules without restoring earlier entries. The regression below sets a preloaded sentinel module, runs the fake owner test, and requires the sentinel to remain installed afterward.

The same save-and-restore discipline is applied to the adjacent explicit-key-up cancellation test. The test-order runner executes the cancellation interval test before and after the transition-receipt, cancellation-cause, release-batch, and V13 executor suites in one interpreter process.

H: fake-Xlib tests restore any pre-existing Xlib and owner/transition module cache entries after completion.

T: observe the pre-fix sentinel test fail, apply the minimal test-fixture restoration, then run the ordered single-process suite.

D: pre-fix must fail because `input_owner_v12` becomes absent; post-fix must pass all 18 test executions in the prescribed order.

C/U: This tests Python test-process isolation only. It does not add X server, OS input, gameplay, model, or task-effect evidence.
