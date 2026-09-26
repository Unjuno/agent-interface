# Post-formal auditor correction

The first independent audit output is retained as `audit.json` and reports
`FAIL_OR_HOLD_INDEPENDENT_AUDIT`. The raw formal data are unchanged. The error
was in that auditor's expected row schema: it looked for a two-element
`offset_interval_ns` array, while the frozen runner intentionally stores the
same endpoints as `lower_offset_ns` and `upper_offset_ns`. This caused 120
false `sample_N_interval_reconstruction` findings. It did not change the
formal runner, source modules, container, raw journals, clock bounds, or Lease
decisions.

No formal rerun occurred. `audit_corrected.py` is a separate post-hoc auditor
that reconstructs endpoints directly from the four raw timestamps and checks
them against the two frozen scalar fields. The original frozen `audit.py`, its
manifest hash, and the first STOP result remain untouched. The corrected audit
result is retained separately as `audit-corrected.json`; this source correction
is transparent post-outcome audit maintenance, not part of the preregistered
formal source bundle.
