# Managed owner lifetime integration construction

The existing default lets a managed child survive normal MCP server termination.
An opt-in ownership-pipe candidate moves that child into its existing cleanup path
at cooperative boundaries. These are three distinct construction cases, not the
frozen #4124 formal allocation or a reliability/performance comparison.

1. Actual MCP/NativeAllocation with an inert substitute harness: after server exit,
   the same PID/starttime remains live. An explicit fixture stop then reaps it at 0.
2. Actual MCP/NativeAllocation with --owner-lifetime and a cooperative inert harness:
   server exit yields pipe EOF, the fixture records owner_ended, exits and is reaped
   at 0. No rescue signal. The reused driver's cleanup console says explicit stop;
   its marker is written only after the EOF exit observation, not as its cause.
3. Actual managed Calc on private Xvfb, source 83f408368, seed 991318: native_start
   delivers a blank sheet, then the actual MCP server context closes without input.
   The harness detects EOF, records an error and invokes existing cleanup. External
   waitpid records owner exit 1; all three tracked process PIDs are absent afterward.
   No request or task evaluation is produced, and no external rescue is used.

Exact source hashes/plans, RPCs, screenshots, errors and cleanup are retained.
The two first cases record a base commit plus exact modified source hashes; those
hashes identify the candidate before its commit. The GUI case uses the committed
candidate. The probe acts as a Linux subreaper solely to collect its own orphaned
child; this is not a production containment mechanism.

The GUI receipt still has owner_exit_verified=false and descendants_verified=false.
The external owner wait and tracked-PID checks are separate evidence, not grounds
to rewrite those fields or claim arbitrary descendant closure. Return codes of
tracked application components include nonzero termination; task success is not
claimed. No input was held or submitted. Server SIGKILL, killed worker, blocked
setup/feedback, active-input interruption and escaped descendants remain untested.
The option remains opt-in and checks cooperative boundaries rather than providing
immediate cancellation. No latency, model-token, speed or generic cleanup claim.

Run `python3 runtime/results/native-owner-lifetime-01/verify.py`. The standard-library
verifier checks saved bytes and records in memory without extracting or executing
archived code. It does not independently re-observe live processes or validate pixels.
