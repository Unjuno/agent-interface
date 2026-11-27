# Review of #8186: preserve Number replies and exclude unsent requests

Disposition: **REQUEST_CHANGES** for peer head
`a32c45581cf11727b373e822a7e751530d144c16`, over review parent
`1fbef34f244588bff3d79b7cbea423dcb510ef8f`. No main application.

The existing root and bugbot executions were assigned as a 2/2 nonauthor
committee before votes in [comment6036905867](https://github.com/Unjuno/agent-interface/pull/8186#issuecomment-6036905867).
Both request changes for canonical proposal SHA256
`2f43f0ecc21c2dbe6bda732d536e7fcf81add01b8108fbcd2bda0b9b1c5b460d`.
No current-main application certificate or platform approval is claimed.

## Findings

**P2: preserve the adopted equal-Number response behavior.** The new exact-int
filter refuses `id:1.0` for an active request whose ID is `1`. Main's adopted
#7222/#5156 stdio regression deliberately accepts this same-valued Number and
rejects Boolean replies. #8186 changes that fixture's float reply to an integer,
so its edited gate no longer checks the compatibility it removes. An actual
default-Popen test found that same-valued float successes and typed errors now
become notification timeouts. Retain numeric equality, excluding Boolean/string
and unequal/unissued IDs, alongside the new ownership test. [#7254](https://github.com/Unjuno/agent-interface/pull/7254)
already documents this distinction; this review is current-composition evidence,
not a novel discovery. The [JSON-RPC specification](https://www.jsonrpc.org/specification)
defines Number identifiers and same-value response correlation; the local
adopted stdio test is the concrete compatibility gate here.

**P2: a request awaiting the write lock is already response-eligible.** The ID
enters `_pending` before `_write` acquires its lock. The independent deterministic
inert-stream probe holds that lock, confirms no request bytes were sent, injects
an anticipated ID response, and observes it cached and returned after unlock.
This is a remaining gap in the proposed unissued-response exclusion, not a
new peer-authentication claim. Tie eligibility to acquiring the write slot while
preserving immediate-response handling; add the blocked-before-transmission
negative case. IDs do not authenticate a peer.

## Executed comparison

Current main `9fb2dd6782d1d1477a00d14be870487fd4c54fa2` versus exact composed
tree `5db80ff133c959510a65fb8e573bc5faf3adeaa3`, one fresh default-Popen child
per cell, five modes per arm. Full client bytes, protocol, freeze, commands,
wire journals, results, source hashes, two votes and independent probe are in
the passive `evidence.tar.xz` archive and verified by `MANIFEST.json`.

| Peer response | Current main | #8186 composition |
|---|---|---|
| Active integer success | Proper result | Proper result |
| Equal float success | Proper result | Timeout; packet retained as notification |
| Boolean poison then equal float | Proper result | Timeout; neither accepted |
| Equal float typed error | Original server error | Timeout; error retained as notification |
| Future-ID poison then proper response | Poison returned on later request | Proper later response; poison retained as notification |

This preserves the candidate's positive evidence: it fixes the exercised
future-ID cache problem. It also establishes the compatibility regression.
All ten runs exited normally and retired the owned child, reader and journal.
Bugbot independently reconstructed the source identities and raw wire ordering:
54/54 saved-data checks passed. Its first audit syntax error is preserved;
no producer was rerun. A chat-only proposal-digest typo was corrected against
the already-correct authoritative vote file, and that correction is retained.

To reproduce a protocol cell, extract the archive into a fresh directory, then
run `python number_reply_probe.py --source main --out fresh-main-float --mode float`
or use `--source candidate`. Other modes are `int`, `boolean_float`,
`float_error`, and `future`. The blocked-send probe is
`bugbot/pre_send_probe.py`, importing the exact client beside it. These are
ordinary inert construction tests, not formal/live allocations.

## Scope

The candidate's full six-file diff was reviewed. The author's edited 34-method
suite was not rerun after concrete counterexamples blocked adoption. No GUI,
model, external app-server, native input, VM, game or task-effect experiment was
performed. The .3-second request timeout is a test bound, not a performance
measurement. No duplicate-response, generalized concurrency, denial-of-service,
or resource-bound proof follows. Actual source and protocol changes must receive
a new proposal and reviews. Prior branches/evidence, including #7094/#7125/#7140,
were not changed or deleted; #8290's separate close repair was not included.

This review branch contains only passive evidence. The rejected composed source
tree is retained locally for reproducibility, and no main merge was requested.
