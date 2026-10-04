# A06: field pixel-change semantic counterexample

This bounded test-double experiment checks whether the A04 compiled form adapter can distinguish exact task-token presence from an unrelated field pixel change. It freezes the caller-v3, compiled-core, and adapter source hashes in `run.py`, executes no GUI/model/provider/input/network operation, and does not modify the retained A04 result.

The test double reports `field_pixels_changed=true` while the field content remains empty. The adapter admits `activate_submit`; with the submit target present and downstream test doubles returning success, the compiled path reports `TASK_SUCCEEDED`. This is a counterexample to the adapter contract's field-progress predicate, not evidence that a live application submitted an incorrect value.

Disposition: `FAIL_FIELD_SEMANTIC_PREDICATE`. The candidate must not be promoted to a live success path until a fresh versioned contract binds continuation to exact task-specific field content (or an independently sufficient semantic predicate), with a negative test proving pixel change alone cannot admit Submit. No consumed GUI allocation was repeated.

Reproduce with `python run.py /tmp/a06-raw.json`, then `python audit.py /tmp/a06-raw.json /tmp/a06-audit.json`. Raw output records action sequence, field content state, source hashes, and outcome. The independent auditor enforces the counterexample and source freeze.
