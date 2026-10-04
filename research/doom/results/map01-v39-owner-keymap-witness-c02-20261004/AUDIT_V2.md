# C02 temporal-binding audit addendum

This addendum strengthens the retained C02 virtual-X11 audit without changing
or rerunning the candidate. The original `candidate.raw.json`, `FREEZE.json`,
and `audit.json` remain byte-for-byte unchanged.

The original auditor binds one admission to each key occurrence by token and
key, but does not require admission timestamps in its positive fixture. The
supplemental auditor requires exactly one matching event with integer
`admitted_ns`, `input_ack_ns`, and `valid_until_ns`, ordered as:

```text
pre_down.sample_finished_ns <= admitted_ns <= input_ack_ns
    <= post_down.sample_started_ns <= post_down.sample_finished_ns
input_ack_ns < valid_until_ns
post_down.sample_finished_ns < valid_until_ns
```

It reruns the original frozen checks in memory, then adds this temporal check.
On the retained C02 raw, both occurrences pass. The added mutation tests reject
admission before or after the down witness, acknowledgment after the post-down
sample, a keymap sample at/after lease expiry, missing timestamps, duplicate
admissions, cross-occurrence timestamps, empty evidence, and malformed rows. One regression
also confirms the parent auditor accepts the fixture with missing timestamps
while the supplemental temporal audit rejects it. A full-report regression
confirms malformed events that crash the predecessor evaluator produce a
failing report rather than aborting.

Validation: 13 temporal mutation tests pass; the supplemental auditor passes
all original checks plus the new temporal-binding check; byte-compilation and
`git diff --check` pass. No candidate, X server, game, model, or allocation was
run. This remains virtual-X11 construction evidence and does not establish
physical input, application effect, useful feedback, bounded recovery, or live
threat control.
