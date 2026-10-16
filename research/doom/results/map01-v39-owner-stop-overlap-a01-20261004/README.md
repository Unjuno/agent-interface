# Owner stop-overlap A01

This construction experiment exercised the exact current-main InputOwner v10
source from main commit `8094af4631fc7bc5d92990e5151d5e89477ee39f` against a
deterministic fake Xlib boundary. It compared a normal explicit release with
`stop_requested` set after `release` had been dequeued and before its branch
executed.

Both cases emitted one fake KeyPress and one fake KeyRelease, left no fake key
down, and returned once from the explicit release call. The baseline had one
owner release record at the comparison boundary. The stop-overlap case had two:
the lease-bound `release` record and a verified-empty `stop_requested` record
with `valid_until_ns: null`. Thus this interleaving produced an extra shutdown
record without a duplicate fake input event. The record is distinguishable by
the missing lease deadline.

The independent auditor checks the package manifest, exact source identity,
and saved records (18/18). The result narrows the RUN-08 race: the tested owner behavior preserves
the one observed key-up while adding a separate shutdown record. It does not
establish server-visible or physical key state; it also says nothing about GUI
delivery, useful feedback, recovery effectiveness, model timing, threat
control, or task outcome. This is construction-only evidence, not an allocation
or a live-control result.

Reproduce with `python3 -B run.py` followed by `python3 -B audit.py`. The runner
refuses to overwrite either retained case.
