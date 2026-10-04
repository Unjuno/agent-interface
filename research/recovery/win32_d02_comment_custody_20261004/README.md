# Win32 D02 recoverable comment archive

This is data-only archival custody, not a new experiment, auditor verdict, adoption vote or runtime patch. The complete 75-member `capture-D02-data-v1` packet is retained inside three comment-body strings in the adjacent JSON snapshots. These are recoverable original Base64/gzip payloads, not merely external links. No member was extracted or executed by this cleanup.

## Contents and provenance

- `win32-d02-comment-5971141305.json`: original result and limitations.
- `win32-d02-comment-5971141547.json`, `win32-d02-comment-5971141870.json`, `win32-d02-comment-5971142214.json`: ordered packet parts 1 through 3. Concatenating the fenced Base64 blocks in this order, ignoring whitespace, recovers the gzip bytes.
- `win32-d02-comment-5971172604.json`: later public readback and insertion-count correction.
- `win32-d02-comment-custody-proof-20261004.json`: all 75 member names, sizes and SHA256 hashes, three original-body UTF-8 hashes and 21 tested-source Git blob joins.
- `check-win32-d02-comment-custody-20261004.ps1.txt`: independently authored checker retained as inert text for methodological transparency. Not imported or run automatically. Its optional Git-pin mode refers to the cleanup operator's original local clone path; this is not a portable runtime tool.

The comment snapshots contain selected API fields and locally canonicalized JSON. Original body strings, including CRLF, remain preserved through JSON escapes. Snapshot JSON bytes are not original HTTP response serialization. Body hashes, snapshot-file hashes and member hashes are distinct domains. Original links are present in each snapshot.

Fixed capsule: 131144 Base64 characters; 98357 gzip bytes, SHA256 `520d80a4bccbb5e9ed37376d99d07a43fb465dcdb721d471d62f738bd276b0e7`; 580124 decoded JSON bytes, SHA256 `0ead2654497b08474c5d91179d381aaec00ea88ab181fec6daaf5e12bbaaf787`. The JSON members carry their exact bytes as Base64. Independently checked: 75 unique safe paths, all declared lengths/hashes, and 21 tested-source witnesses matching source commit `0cbf4b7286a700d65c7f96311a61ee2cc83b3791`. This is byte custody, not scientific regrading.

## Source and acceptance scope

PR #7147 merged at `42387b402421be815e85ffbf4046dfdee73e089a`, actual first parent `b50fd3674352c741381a02e7ba202a71bc285c77`. That merge changed only `runtime/backends/win32_v1/backend.py` and `test_integration.py`; this archive separately preserves its native proof packet. Source commit `0cbf4b7286a700d65c7f96311a61ee2cc83b3791`, tree `41681574babe11679acd1616311e2ffefcea2e6a`, content-review base `951beae4caf0cad4e788d329f4db670348afee26`.

The author's PASS_OWNED_MEMORY_CAPTURE_CANDIDATE covers four candidate captures (304 BGR coordinates) and a properly deselected direct baseline (256 coordinates). GetDC/ReleaseDC is adapted to an owned memory DC. It is not real-window, screen, PrintWindow, input or causal proof for the earlier A01 blank-capture failure. That prior failure remains a separate result, preserved under `research/integration/win32_owned_capture_622_480b_a01/`.

Historical author auditor receipts and ten copied mutation controls remain historical evidence, not new cleanup executions. The historical pure-helper module receipt has empty `source_pins`; today's independent joins do not retroactively fill it. The first launcher used a nonexistent cwd and was refused before child process creation: no child PID or missing initial timing/stream reconstruction is claimed. Later successful readback is separate evidence. The correction states 5 backend insertions and 98 test insertions (103 total), not a new experiment or changed scientific result.

Historical prospective committee/vote statements are not current adoption authority. As observed during preparation, Issue #622 was already closed and child PR #7173 remained open on main at `685d9fb60705f4f6515fb75eab910ff577ab355b`; these are timestamp-dependent preparation observations, not instructions or approval. This archive does not reopen the Issue, merge the child, transfer votes or independently revalidate broader acceptance.

## Preservation gate

Source branch retirement remains a separate action requiring verified actual-merge/current-main custody, full open PR head/base dependency inspection and an exact-tip lease. This archive's presence alone is not a retirement receipt. No runtime, tests, workflows or historical patches are applied here. Recover retained programs as data only; do not execute archived producers or auditors as part of cleanup.
