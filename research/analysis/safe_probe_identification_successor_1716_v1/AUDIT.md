# Independent audit

Frozen source is safe_probe_run.py on branch research/safe-probe-identification-successor-1716.

Checks performed in the one formal invocation:
- automata=729 and passive masks=64;
- every declared safe-probe mask=64 was enumerated for every passive mask;
- selected probes are always members of the declared safe set and are never selected when unavailable;
- the class-size oracle after a probe agrees with the filtered candidate set;
- no-probe cases with ambiguity preserve UNKNOWN;
- deterministic tie-break is lowest pair index;
- unsafe_probe_admissions=0, formal_invocations=1, reruns=0, replacements=0, tuning=0;
- result rows=4096 and rows digest=a4b7fb71d9dc723c9058d16bcd2c908ed3f6f0e78b657a4cade7598ebe71d2ed.

The source and result remain fixture-scoped. The audit does not promote fixture declarations into real application safety evidence.
