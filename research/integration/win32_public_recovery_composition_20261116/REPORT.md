# Win32 public recovery and caller composition

## Scope

Candidate delta from current main `ad0c748f63ea0ee52cbd28055fbd11dcd7e09886`, sourced from local candidate head `246106bf9915c919ae7362cc7ca8455b41e9bcd6`. The delta covers the absolute authority deadline during execution, conservative UNKNOWN/recovery after late producer completion, provable no-dispatch close, exact public result lookup, foreground-receiver checks for orphan release, and the composed stdio regressions. It does not change the meaning of task success or permit replay after UNKNOWN.

## Local checks

- `runtime.cli_v1.test_mcp_supervised_win32`: 57/57 normal and 57/57 with `-O`.
- Six focused Win32 public stdio cases (expired start gate, oracle timeout, foreground refusal/drift, returned button release receipt, and late-input refusal/release): 6/6 normal and 6/6 with `-O`.
- G10 public stdio receipt and unknown-parent-effect cases: 2/2 normal and 2/2 with `-O`, after materializing two already-tracked FODS fixtures omitted by this sparse checkout.
- `test_win32_supervisor_helpers`, Win32 focus guard/recovery, and guarded-process cancellation subset: 96/96 with `-O`. The new G10 owned-process case and the two cancellation timing cases passed independently in normal mode; the new G10 case also passed with `-O`. The combined 173-test normal run had load-sensitive failures described below.

## Full-suite outcomes and limits

The first combined 173-test run in this sparse checkout could not read the two tracked G10 FODS fixtures. They were materialized from `origin/main` without changing their contents; the two affected cases then passed in both modes.

After fixture materialization, two combined normal runs reported 172/173 and 171/173. One failure was a semantic-plan test that passed when run alone. The second run's two failures were existing owned-process cancellation timing assertions: one measured 313 ms against a 300 ms bound; one observed a release worker before retirement/readback. Both passed when run alone against the candidate and against unmodified current main (2/2 each). Their source tests and assertions were not changed by this candidate. The full combined suite was not established as stable under this host's suite load, and the failures are retained rather than waived.

The exact terminal caller shape and delayed recovery behavior are covered by the passing Win32 focused cases and 57-test module. This packet does not claim a full clean pass for all 173 cases, native GUI task success, or #57 matched efficiency.

Raw PowerShell transcripts for the two combined normal runs are retained locally beside this report. They include workstation identifiers and are not published in this PR. The live R193 host packet remains in its separate local evidence directory with its own SHA-256 manifest.
