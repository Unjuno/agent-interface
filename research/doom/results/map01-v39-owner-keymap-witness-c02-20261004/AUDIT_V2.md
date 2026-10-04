# C02 temporal-binding audit addendum

This addendum strengthens the retained C02 virtual-X11 audit without changing
or rerunning the candidate. The original `candidate.raw.json`, `FREEZE.json`,
and `audit.json` remain byte-for-byte unchanged.

The original auditor binds one admission to each key occurrence by token and
key, but does not require admission timestamps in its positive fixture. The
supplemental auditor requires exactly one matching event with integer
`admitted_ns` and `input_ack_ns`, ordered as:

```text
pre_down.sample_finished_ns <= admitted_ns <= input_ack_ns
    <= post_down.sample_started_ns <= post_down.sample_finished_ns
```

It reruns the original frozen checks in memory, then adds this temporal check.
On the retained C02 raw, both occurrences pass. The added mutation tests reject
admission before the pre-down sample, acknowledgment after the post-down
sample, missing timestamps, and duplicate admissions. One regression also
confirms the parent auditor accepts the fixture with missing timestamps while
the supplemental temporal audit rejects it.

Validation: 7 temporal mutation tests pass; the supplemental auditor passes
all original checks plus the new temporal-binding check; byte-compilation and
`git diff --check` pass. No candidate, X server, game, model, or allocation was
run. This remains virtual-X11 construction evidence and does not establish
physical input, application effect, useful feedback, bounded recovery, or live
threat control.
