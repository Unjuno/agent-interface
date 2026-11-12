# Conservative input-release observation bounds

`input_boundary.py` retains a bounded stream of caller-supplied key-state reads
and audits a lease-expiry boundary. It does not dispatch input or establish
application delivery, task success, or the absence of queued messages.

For the last fully pre-expiry DOWN read `[down_start, down_end]` and the first
fully post-expiry UP read `[up_start, up_end]`, the observation instant inside
each read is unknown. The upper bound on the observed transition interval is
`up_end - down_start`. The inner gap `up_start - down_end` is diagnostic only.
The checker exposes both values and qualifies the outer bracket against the
fixed limit. Missing, malformed, errored or unknown observations do not pass.

An observed regression had a 19.9903 ms inner gap but a 20.0044 ms outer
bracket. Comparing only the inner gap falsely accepted a 20 ms limit. The
regression test retains these interval widths and checks the inclusive exact
limit plus a one-nanosecond overrun. The old result must be preserved separately
from corrected offline adjudication; do not rewrite raw evidence or change a
threshold after seeing an outcome.

Run the standalone, input-free checks from the repository root:

```text
python -m unittest discover -s research/integration/map01_numeric_ammo_oracle_20261111 -p test_input_boundary.py -v
python -O -m unittest discover -s research/integration/map01_numeric_ammo_oracle_20261111 -p test_input_boundary.py -v
```

Clock-domain compatibility is a caller prerequisite. Lease timestamps and the
paired lease-clock fields must share their actual clock and epoch. QPC fields
measure ordering and interval width; the audit does not convert arbitrary
epochs or prove a hard real-time bound from a finite sample.
