# Notification failure retirement probe r545

One isolated Linux Fake X/MCP run tested the preregistered fixed-order cases.
The known positive control, successful notification while send was gated, and
injected notification OSError with gated send passed. In the latter, the
prototype retired the spawned owner before the gated send resumed; no synthetic
target effect was recorded. Its close report recorded owner exit -15,
`cleanup_status=UNKNOWN`, no confirmed release, and no replay. The separate
case injecting UNKNOWN after child admission still produced a synthetic effect
and failed; overall test exit was 1.

**The setter-driven retirement prototype was not adopted.** Independent static
review found it can retry the failed notifier while retiring, block or raise
before cleanup, race concurrent retirements, overwrite custody evidence, and
miss a child that is starting but not yet registered. Existing queued server
requests are not withdrawn by process termination. Its exact pre-run diff is
preserved in the archive; it is not a safe implementation recommendation.
This test injected a notifier exception and used Fake X, not a naturally failing
kernel write, real cancellation, physical input, confirmed key-up, or MAP01.

`raw.zip` SHA-256
`628d9e2f029cb91abd02dd885b843d831b0ab3f051efb365de15c7cb2d20ebc6`
contains the pre-run conditions, base, diff, output, exit status and synthetic
case data. Members were integrity checked. Image digest and container flags
are recorded conditions, not attested by case JSON. Temporary image references
in reports may refer to original container paths. This single trial is not a
hard bound or evidence that already queued X requests have stopped.
