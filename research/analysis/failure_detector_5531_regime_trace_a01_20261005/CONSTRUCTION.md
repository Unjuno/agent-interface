# Construction record

The first unit run failed before formal freeze. Python equality let `False`
alias integer sequence value `0`. The first outcome is retained in
`results/construction/AUDIT_TEST_FAILURE.json`. The raw console stream was not
redirected; the retained record is explicitly a structured summary, not a raw
log. The auditor helpers were tightened to require exact integer types for
sequence and monotonic fields, and the test rejects boolean aliases. The
corrected focused suite passes 3/3.

A separate 3-second construction capture used allocation
`FAILURE-DETECTOR-5531-REGIME-TRACE-A01-CONSTRUCTION-01`, outside formal output
path `results/a01/`. It exited 0 and retained 30 heartbeat records, 3 progress
records, and 3 Windows host CPU samples. A second 2-second binary-stream
construction used `...CONSTRUCTION-02`; it exited 0 and retained 20 heartbeat
records, 2 progress records, and 2 host samples. Raw child stdout bytes are
retained next to the observer-enriched event stream. These only check capture
plumbing; they are not formal traces, and neither is passed to the formal
auditor.

The corrected focused unit suite and formal freeze checks must pass before A01
starts. Construction evidence is never counted as formal or used to adjust the
frozen 50% host-regime threshold.
