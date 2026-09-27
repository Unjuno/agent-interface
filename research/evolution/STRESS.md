# Shared active-input interruption stress

`results/stress-01` extends the same pinned full-presentation runtime used in
readiness-01. Before executing, the harness writes source hashes and eight cases:
XTerm, Chromium, Calc and Inkscape × active cancellation / active expiry.
Seeds are 980101 and 980102 respectively. No runtime source was changed.

Each case requests a 1,000 ms Control hold followed by `bad` text. Cancellation
is sent after receiving `keys_held`; the other arm uses a 200 ms absolute lease.
The harness requires zero completed steps, verified release and no start of the
text tail. A fresh intent then performs the original app task and saves output.
These are scripted functional stress cases, not assistant/human performance runs.

All eight interruptions behaved as required, and all eight subsequent saved
tasks passed. All twenty accepted programs and eight owner shutdowns verified
release. Ninety packet frames match archived PNG pixels. The audit independently
checks output text/form data/workbooks/SVGs, source identity, terminal status,
tail suppression, full event delivery and release records.

Terminal release verification is not the earliest key release. For example,
Chromium cancellation reports owner verification 3.054 ms after the cancellation
record's timestamp, while terminal release verification arrives 69.152 ms after
that timestamp. Calc expiry similarly has separate owner and worker records.
Full per-case values are in `audit.json`. These are local observations, not hard
latency bounds. The cancellation timestamp is emitted after setting the cancel
flag, so it is not an exact start-of-request timestamp. No independent external
key-state sampler was attached in this cohort; owner verification queries X11.

This extends the common evaluation beyond rejection at admission, but only with
one modifier key and one seed per interruption type per application. Focus
transfer, disconnect/process failure, critical-event retention, continuous motor
control and DOOM are not covered. Environment versions were not collected before
this cohort; the earlier retrospective environment record is context, not proof
of an identical frozen machine state. The manifest freezes runtime source and
case specification only. This does not qualify for Research Freeze.

No new architecture mechanism is introduced. No failure was observed in these
declared cases; global new-class counts remain unknown pending historical audit.
The result is indexed separately from self-use performance data.

Run from the repository root in the documented Ubuntu/WSL environment:

```sh
python3 research/evolution/stress_probe.py --out results-local/stress-new
python3 research/evolution/audit_stress.py research/evolution/results/stress-01
```

The harness is a frozen research revision. Its retained `scope` label says
readiness smoke; the manifest and `stress` field specify the active interruption
extension. Choose new output paths and preserve failed cohorts when changing it.
