# Issue #59 candidate-stack check on current main

This is an integration check, not a live allocation or a new scientific result. It verifies that the existing #8272/#8269 measurement-custody changes compose with current `main` after the main branch advanced to `75bfe2badd49376ac33cd8a87030e7a6a3396ecf`.

The exact checked source tree before adding this evidence package was `0c062cc8e15f1c003daac0108d452f07051ad21a`. It was formed by merging PR #8272 head `c9f054be4333de65cca57eac3e696dc3b9633b41` and then PR #8269 head `9f7a4a96847ee29787a87f6fb238e71da112712c` into current main. Both merges were conflict-free. PR #8272 contains the current #8266 candidate branch (`e7be07d196eebe00d9f306087edf5890cc0ecc98`); PR #8261's separately posted head is `4190104d0c72a025093c8569fdbd216b5929de0b`.

The focused candidate-stack checks are V13 terminal custody and V15/V12 batch key-measurement composition. The container uses the locally retained Linux/arm64 image `sha256:b82a3260f3e5839b9dce6d745233f09c9189d5f2154cf7a6d18e24d190c10907`, no network, read-only source, 1 CPU, 1 GiB memory/swap, 64 pids, dropped capabilities, and no-new-privileges. `run_candidate_stack_tests.py` contains the test import setup (including the unused `vizdoom` import stub).

Reproduce from a checkout of the recorded source tree by mounting the checkout read-only at `/workspace` and a fresh output directory at `/out`, then running:

```sh
python /workspace/research/doom/issue_59_candidate_stack_current_main_20261007/run_candidate_stack_tests.py
```

The retained first run is in `results/a01/`. `audit_candidate_stack.py` independently verifies the exact source hashes, test counts/status, and raw-log hashes; its verdict is scoped to this synthetic integration check.

This does not establish real X11 behavior, application consumption, physical key state, live threat response, useful feedback, recovery, or gameplay outcome. It does not replace nonauthor review or authorize merge.
