# Text-only acknowledgment integration and primary use

Source `1de997bb7d6db1872ae56d30aaf763ec0609e570` adds a separate
`acknowledgeText(attempt, {task, phase, reason})` to the public Node host.
The preceding [spine06](../post-release-spine-06/README.md) stopped when the
primary attempted image review on a text-only revoked-source refusal. This
addition records attribution to presented original text without weakening image
review or granting permission to retry. It does not retrospectively repair that
failed allocation.

The host binds retained reply bytes to their originally delivered digest and
requires completed presentation of that unchanged reply. Only nonempty text-only
content is eligible. Explicit MCP error status stays intact. The receipt is an
exclusive `text-acknowledgment-N.json`; a separate same-clock event joins it to
presentation. No tool is sent by acknowledgment. Missing attribution arguments
reject before beginning a host operation; evidence errors block ordinary calls
while permitting original transport cleanup. The existing image receipt API
continues to require its sourced report and image.

Tests first failed because the method was absent. A second test exposed that
retained reply bytes could change before presentation; it failed with a missing
rejection, then passed after original-delivery digest binding. All 58 Node tests
in the CI host/research relay command pass, including unchanged replies,
unpresented/changed/image rejection, original strict image-review rejection,
exclusive receipt writes, and no acknowledgment-driven dispatch. CI now includes
all public host test files.

The primary personally used the freshly built 345,798-byte Python runtime archive
and committed host bundle on WSL 3.0.1 / Ubuntu (WSL2 execution architecture).
This was a **one-shot text transport study**, not a GUI task or matched benchmark:

| Attempt | Actual call | Original result | Primary acknowledgment |
| --- | --- | --- | --- |
| 1 | `interface_validate` with empty program | `isError:true`, INVALID_PROGRAM / program schema mismatch; backend not checked, no authority | Original invalid-program text read and recorded |
| 2 | `interface_guarded_mint` unavailable in one-shot registration | `isError:true`, Unknown tool | Original error read and recorded; not a revoked-source recovery result |
| 3 | `interface_clock` | `isError:false`; no input, authority or lease | Original clock text read and recorded |

All three requests/replies, presentation events and acknowledgments are retained;
there were zero image reviews and no input tool calls. The same original relay
continued after the acknowledged errors and closed with exit 0. Transport close
does not establish application neutral state or GUI cleanup. The primary's
acknowledgment reasons are attribution, not attested model comprehension or
semantic-completion timestamps.

Before any dispatch, source inspection corrected the original plan's mistaken
tool names/cleanup expectations. Both the original plan and additive correction
are preserved. The unavailable-tool call is deliberate under the corrected
plan. A separate diagnostic invocation of `relay -- --help` exited 1 because help
text from the subprocess is not MCP JSON; no input was sent. An attempted test-log
redirection was interpreted by PowerShell and failed before launching Node; the
subsequent explicit Python subprocess invocation retained the full passing log.
These construction errors are not task runs and are not silently converted to
passing measurements.

The first shared Python runner used `/usr/bin/python3` without MCP installed:
protocol 236 tests, 10 import/errors, harness 149 passes, overall FAIL. Failures
were `test_mcp_relay`, `test_mcp_server`, `test_mcp_clock`,
`test_post_dispatch_capture`, `test_mcp_session`, `test_mcp_guarded`,
`PublicBriefMCPTests.test_opt_in_full_retrieval_and_failure_do_not_replay`,
`PublicSummaryMCPTests.test_opt_in_and_full_retrieval_do_not_change_persisted_report_or_replay`,
`test_native_mcp_v1`, and `test_native_mcp_relay_v1`; all arose from missing `mcp`.
The existing MCP virtual environment then passed protocol 337 and harness 149.
Both complete reports and logs are in the archive; asynchronous debug messages
are retained. No environment reinstall was needed.

`audit.py` independently checks the three-call denominator, exact host ordering,
original reply/receipt/event hashes, text-only content, typed error status, no
image review and original exit. `test_audit.py` rejects altered receipt status,
missing presentation and a rehashed changed error status, both normally and with
Python `-O`. These checks prove scoped evidence integrity, not full integration.

The archive manifest enumerates every retained file and digest. Extract into a
fresh directory, then run `python audit.py` and `python -O test_audit.py`.

**Full integration remains HOLD.** Next is to use this explicit acknowledgment in
the frozen primary caller and launch a newly fixed complete guarded/direct pair,
including the actual revoked-source control and original GUI task denominators.
Current-main promotion/compatibility, compiled baseline, other domain coverage
and actual provider token/cost measurements remain pending. No human-tempo,
general performance, speedup, token savings or product-completion claim is made.
