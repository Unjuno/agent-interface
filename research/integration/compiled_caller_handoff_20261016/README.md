# Compiled execution → caller handoff: retained counterexamples

2026-10-16 JST. Current main `955f85ef0238c44b05a4477f607578b026390568`.
Ordinary local construction/characterization; **FAIL_CURRENT_COMPOSITION**.
No runtime change is adopted by this packet. No native GUI/input, provider/model,
WSL/container, formal allocation or historical producer was run.

## Question and actual path

The v3 caller now retains completed execution and bounded effect references,
but `integrated_efficiency_compiled_execution_v1.py` still imports caller v2.
Does that existing composed entry retain known input/effect facts through outer
effect failure, receipt-sink failure and unverified release? Is changing only
the imported caller enough?

The probe executes the actual exact-value compiler, compiled core, helper and
caller. Observation, admission, execute/release and effect callbacks are inert.
They return explicit synthetic values; no X connection or OS input is involved.
The supplied effect reference is a literal, not independently retrieved app
evidence. Core `TASK_SUCCEEDED` means this method completed under those values;
it does not establish a real task effect.

Two selected source configurations run six cases each under normal and actual
optimized Python: the existing v2 import, and a **directed import-swap control**
using the real v3 caller. The latter adds `local_repair_on=[]` to its spec and
temporarily replaces the helper's imported `run_caller` in this isolated probe.
It is not an advertised v3 entry point, a production migration or a matched
performance comparison. The source functions themselves are not rewritten.

## Observed handoff results

| Condition | Retained core fact | Existing helper + v2 | Imported-v3 control |
|---|---|---|---|
| Healthy inert control | Two completed/released transitions | Completed, confirmed, outer synthetic success | Same, plus bounded effect reference |
| Outer effect failed/unavailable | Two completed/released transitions | TASK_NOT_VERIFIED, confirmed delivery, but execution_progress is null | TASK_NOT_VERIFIED with completed progress and effect reference |
| Receipt sink throws after core returns | Two completed/released transitions; outer verifier never called | CALLER_FAILED, delivery and progress null | CALLER_FAILED, delivery_uncertain, progress null |
| Release unverified on first input | Zero completed transitions, one returned input terminal with release_verified=false | Failed summary, no current delivery/release distinction | Same |
| Release unverified on second input | One known completed/released transition, second input terminal unverified | Only status=failed; completed prefix lost from caller summary | Same |

Each mode has **12 cells: 8 fail the stated information-preservation requirements
and 4 are inert positive controls**. Process exit 0 and saved-reader success mean
the characterization ran and was read back correctly; they do not turn the eight
counterexamples into qualified control. No condition retries or replays input.

The first and second release cases have one and two synthetic execute callbacks
respectively, no outer verifier call and no model attempts. A reported held-key
list is an injected fixture value, not measured physical input. The complete
compiled receipt still holds evidence omitted by the helper's summary; this
is not a claim that all raw evidence disappeared.

## Evidence and checking

- [CONDITIONS.json](CONDITIONS.json) predates these runs and identifies source,
  cases and the three requirements. This is ordinary construction, not a formal
  scientific allocation or live reliability estimate.
- [SOURCE_PINS.json](SOURCE_PINS.json) records five Git blobs, separate Git-byte
  and worktree-byte hashes and AST joins for the actual selected functions.
- [PROCESS_RECEIPTS.json](PROCESS_RECEIPTS.json), complete stdout/stderr and two
  full row archives retain source configuration, core receipt, caller receipt,
  callback counts and journal events. [RECORD_ARCHIVES.json](RECORD_ARCHIVES.json)
  joins each gzip archive to its complete original JSON bytes.
- The separate saved-only reader checks all 12 rows per mode against the fixed
  callback counts and exact observed source-specific outcomes. It rejects four
  copied contradictions: hidden input, invented prefix, false neutrality and
  false success. Audit streams and process receipts are retained. It does not
  execute the candidate, import the caller or independently score an application.
- `probe.py.txt` and `saved_reader.py.txt` are inert reference sources with
  original local path bindings; neither is a registered test/actor entry point.

## Resulting integration decision

Do not promote the legacy helper, or an import-only v3 switch, as the qualified
current #57 composition. Do not weaken the reference arm or infer new timing/
token gains from these cells. Keep all historical frozen live outcomes unchanged.

The next repair needs an explicit v3 composition contract that retains both a
completed prefix and unresolved current input, and detaches the returned core
receipt before auxiliary persistence can fail or mutate it. It must preserve
known input progress after sink failure, skip unsupported outer effect claims,
retain the original error and prevent blind replay. Regress those boundaries
through actual core/caller functions before selecting the future live runner.
Then connect actual task/effect and model-stage adapters and qualify the fresh
matched comparison. Native release bounds, app success, bounded semantic
recovery, live provider accounting and second-domain economics remain open.
