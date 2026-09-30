# Verifier registry T0 v2 successor

Review-driven successor to v1; v1 files/results are immutable. This version validates plans using the actual frozen #5268 IR v0.1 validator, consumes accepted and requested output roles, applies hard-rejection precedence over unavailable resources, and has a raw-only literal auditor separate from candidate and test oracle.

The retained invocation is host construction only, not formal/container evidence. It is single-use and writes to a fresh output directory. Do not rerun it in-place or regenerate the freeze over retained output. For a new run, create a new allocation and output directory, use a separately granted container lease when required, and freeze/audit as a new successor.

The #5268 `deadline` field is a nonnegative integer without a qualified unit; the finite fixtures adopt the millisecond interpretation used by the existing #5269 profile boundary. These synthetic cases do not qualify or change the general IR deadline semantics. All registry cost values are synthetic estimates, not measured latency.
