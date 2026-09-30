# #5156 serializer successor — construction only

H: the allocation-04 stop is caused by passing a row containing `event` to
`dict(event="joined_release", **row)`. The caller's explicit event keyword
collides before any joined-release row is emitted.

T: reproduce that exact Python failure; construct a non-mutating envelope that
retains the owner event as `owner_event`; check a complete synthetic stream and
corruption controls with the frozen raw-only auditor.

D: all offline tests pass and the synthetic complete stream returns no auditor
errors. This is schema/serializer construction evidence only.

C: no X server, Docker/container invocation, or allocated experiment lane is
used. Synthetic timestamps and records are not observed experimental data.

U: no key-up duration, live-control efficacy, input safety, MAP01 occupancy,
or transfer claim. The consumed allocation-04 raw/result remain unchanged;
this work does not authorize or perform an X11 rerun.

Run with `python -m unittest -v test_serializer_successor.py` in this directory.
