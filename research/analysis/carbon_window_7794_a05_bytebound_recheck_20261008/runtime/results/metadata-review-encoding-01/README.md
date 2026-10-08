# Retained metadata lookup — avoid discarded image encoding

Baseline portable build: `73d3475dd478766e5d35da929a5f340244f5b3a6` from
`public-inkscape-batch-01`. Candidate: `65f326e87` (full source revision in its
build manifest). Public observe/dispatch retained-result lookup now passes
`include_image` into review, retaining the exact path/digest/PNG-signature checks
but not Base64-encoding an image the caller explicitly omits. Ordinary image
presentation is unchanged; management/guarded presentation uses its old route.
The Python review API also accepts the explicit bool, default true.

A read-only integration probe loaded each committed archive with Python `-I`
from `/tmp`. It injected the same retained 35,165-byte PNG from the prior actual
Inkscape drawing into server observation acquisition; this was not a new live
GUI task or MCP stdio round trip. Both servers acquired once, then used the real
`interface_results` implementation. Instrumentation counted review Base64 calls:

| build | omitted lookup | included lookup |
| --- | --- | --- |
| baseline | 1 call / 35,165 input bytes | 1 / 35,165 |
| candidate | 0 calls / 0 input bytes | 1 / 35,165 |

Within each build, omitted/included metadata is identical except the existing
omission marker; only included returns the PNG content block. Lookup leaves the
raw report unchanged and does not reacquire. Altering the diagnostic copied PNG
makes both builds return `needs_review`, with zero further encoding. The frozen
original PNG/report were never changed. Missing/hash/signature controls are also
covered by unit tests. No parsing, admission, input scheduling or replay behavior
was changed. This removes conversion work, not transmitted-image tokens (those
were already omitted). No CPU/wall-clock, actual token/cost, useful feedback or
model-quality comparison is claimed.

48 focused tests pass and the full local native check passes (311 protocol,
135 harness);
raw logs are retained. Initial new unit test failure was an incorrect mock
signature (missing positional target mapping), corrected before commit. An outer
probe preparation forgot `import json` and stopped before launching either
process; setup-failure.json records this, and no partial trial was overwritten.
No formal experiment allocation was consumed or rerun.

`raw.tar.gz` includes both portable builds/manifests, the retained source PNG and
report, probe source/output, diagnostic server records and altered copies, plus
native logs. Historical absolute paths are not portable authority. Verify with
`python -O verify.py`; this rechecks file identity and recorded response parity,
not model perception, producer authentication or a general performance claim.
