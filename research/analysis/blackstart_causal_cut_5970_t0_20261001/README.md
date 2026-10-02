# Issue #5970 cross-issue T0: recovery reachability is not evidence coherence

This additive finite-model experiment combines Issue #5970's staged recovery witness question with Issue #5348's causal-cut evidence contract. It preserves both issues and their prior results. It does not grant action authority from visibility or from a graph path alone.

The model has three asynchronous streams: independent root/bootstrap evidence, surface focus/lease evidence, and invalidation/release events. Each event has a source-local sequence and explicit causal parents; message sends/receives are explicit. The output compares a graph-only `READY` decision with a cut-aware decision under exhaustive finite cut enumeration.

See `PLAN.md` for H/T/D/C/U, `REPORT.md` after the frozen run, `cases.json` for the traces, and the immutable raw candidate/audit records.

Docker Desktop is unavailable locally and the shared container lane is occupied/ambiguous. The T0 is deterministic standard-library work run in separate host processes. This is finite semantic evidence, not a container-isolated or empirical recovery result.
