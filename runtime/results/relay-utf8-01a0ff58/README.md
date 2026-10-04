# Strict UTF-8 relay admission repair

Author repair of [assigned df63's V4 HOLD](https://github.com/Unjuno/agent-interface/pull/6879#issuecomment-5965959875),
after [author acknowledgement](https://github.com/Unjuno/agent-interface/pull/6879#issuecomment-5965974550)
and [prospective ordinary repair scope](https://github.com/Unjuno/agent-interface/pull/6879#issuecomment-5966111931).
No df63 original producer or historical formal allocation was replayed.

## Change and observed result

The public relay previously read inherited text stdin. Native Windows CPython3.12.14/MCP1.30.0 private probes report utf8_mode0, stdin cp932/errors surrogateescape. The exact UTF8 escaped/literal U+1F600 duplicate crosses SDK and consumes ID1 because cp932 gives the literal a different decoded string. SDK serialization raises UnicodeEncodeError; sameID1 is refused. This is an actual local SDK uncertainty, not evidence the server executed input. It preexists the finite/unique-key guard.

Read an available stdin binary buffer; decode bytes/bytearray strictly as UTF8 inside the pre-admission try block. This keeps literal/escaped decoded-key equality, rejects invalidUTF8 and UTF16/32 before consuming IDs, preserves exact valid Unicode arguments in mocked client calls, and keeps already decoded source text streams compatible. All SDK-entry failures still consume accepted IDs and prohibit replay. No environment/encoding configuration is changed globally; output remains JSON with existing ASCII escapes.

The same four new test definitions (SHA9eaa0aee8e84d3fee7a1cf342a415fec148335e55a2738cc13b914564802aa70) first expose four subtest errors in two methods, while the other two methods pass. After the minimal source fix all4 methods pass. The first related15-method run has14pass/1missing research sparse source error; restoring only the exact current Git legacy relay makes15pass. Old research source is not changed. That first combined packaged check built the then-committed85d source; it is not the UTF8 candidate package. The later combined15 check builds committed75d.

Three explicit actual committed-archive SDK cells retain18 responses. Original85d reproduces first duplicate uncertainty/ID consumption; candidate75d gives refused/returned/returned/refused/returned/returned with nextIDs1/2/3/3/4/5. Current-contextd37d, including the newly merged compiled-effect dependency, gives the same boundaries. Both repaired static Unicode programs report static_valid true/backend_checked false/task_success null, and neutral close reports no backend connection close attempt. All three actual relay exits are0. Independent SDK server exit codes/PIDs are not separately captured; a later scoped OS process snapshot is only an observation if provided, not a replacement exit receipt.

## Preserved unexpected first result

First original SDK capture's strict author checker exits1 after the six-row/relayexit0 receipt: it incorrectly predicted that the Japanese-plus-emoji static program would also produce a serialization error. Actual row2 returned static_valid true. The first helper/BEFORE/stdin/stdout/stderr/receipt/zip are retained; no RESULT is fabricated for that failed check.

Separate post-result saved-byte inspection shows that cp932 decodes that text to different Unicode while UTF8 retains the authored text; the static validator deliberately does not echo input. Thus static_valid true is not exact transport proof. This byte inspection is a post-result author diagnostic, not an independent scientific oracle or a replacement PASS. The first six outcomes remain [unknown,refused,returned,returned,refused,returned], nextIDs2/2/3/4/4/5. The extra byte-invalid request can map to a valid control character under cp932 and enter SDK; its server invalid_request is different from pre-SDK byte refusal.

## Source context and scope

Original committed source85d1cab22de72155b019faedbb72837d92190e40 composes historicalfe42 and mainfb556. Repaired75d87cb296814d07b9f1b730bb6d1516ccf9777a changes only relay/test/MCP documentation. Updated contextd37d128c23ed5ed1a38f99381e61cf9abe363336 merges main4cd7649777c8a042d486b2058fd1bcbc18a90727. Each SDK cell separately checks all51 packaged source Git blobs plus generated entries. The matched original/candidate75d differ only in this repair's three paths; the extra current-context cell is not pooled as a matched causal trial.

Source condition: native responsive pipes, selected CPython/MCP versions, sequential JSON lines with no BOM, idle/static validation/clock/close only. No observe/dispatch/native input/model/GUI/display/resource lease, actual physical release/application effect/task success/noncooperative failure/latency/cost/general OS guarantee. SDK static validation provides no server input echo; exact forwarding is checked by the source/mock controls and retained byte interpretation. Four new source/SDK-mock methods are ordinary regressions. Full unrelated runtime/hosted CI or formal producer/auditor invocations are absent.

[Python standard-stream documentation](https://docs.python.org/3.12/library/sys.html#sys.stdin) explains locale streams/binary buffers; [RFC8259 encoding and string comparison](https://www.rfc-editor.org/rfc/rfc8259.html#section-8.1) supplies the interoperable UTF8 premise. Actual version/configuration comes from the retained probe, not the current documentation's patch version.

## Custody and nonexecution

CUSTODY maps each private original/public SHA and size. Original files remain private and unchanged. Only local-home prefix spellings and closed transient SDK session/call IDs are consistently projected; reviewer identities are untouched. UTF8 text newlines remain byte-preserved. Invalid-wire and captured ZIP bytes remain byte-identical binary artifacts after checking private marker absence. Captured CLI ZIPs are retained as .pyz.bin under this evidence folder; **do not invoke the historical original archive**. They contain runnable captured code but are not added to default imports, test discovery or workflows. Python helper/snapshot files are txt; no new automatic producer/auditor is added. Manifest covers every file except itself. Archive-local attributes prevent Git newline normalization.

V1–V4 data, first failures and approvals stay historical. Changed head/current dependency/encoding conditions require a new fixed V5 proposal before votes. Separate current-base/head/tree/apply_id nonauthor confirmation, real GitHub requirements/identity/sole expected-old forward main-only apply remain required. No main write or application request in flight.
