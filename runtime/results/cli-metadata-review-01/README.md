# Metadata-only CLI review — integration use

Build source `d9b99b35a` (full revision in MANIFEST.json). `review --no-image`
connects the existing validated metadata-only Python review path to the CLI.
Default review still returns the PNG. CLI summary retrieval recipes now request
metadata-only review and carry the exact expected source digest. Image/source
validation and refusal behavior are preserved; no capture or input is performed.

A portable Python `-I` probe ran from `/tmp` against the frozen successful save
record from `cli-summary-primary-01/call-4`. It generated the new summary recipe
using the archive's own implementation, converted those exact arguments to CLI
flags, and ran the command. Included-file, omitted-file and omitted-stdin reviews
all exited 0. A whitespace-modified report copy exited 2 with invalid_receipt.
The original report was unchanged. Existing unit controls additionally check
image mutation refusal and default PNG delivery for both file and stdin.

Included-file output: 16,472 bytes. Omitted-file output: 3,857 bytes. The same
receipt, image reference and outcome are retained; only the encoded image and
explicit omission marker differ. Stdin retains its established received-byte
source representation. This is a concrete serialized CLI size result for one
record, not a model-token/cost/useful-feedback/human-tempo comparison. No new GUI
task, provider call, semantic revalidation or action replay was run.

64 focused tests pass; local native suites pass (312 protocol, 135 harness).
The build/probe commands, exact stdout/stderr, source report/PNG and native logs
are retained in raw.tar.gz. Historical absolute paths require explicit relocation
before reuse; coordinates/leases in the source report are not new authority.
`python -O verify.py` checks retained member bytes and response/source/image
identity; it does not establish model perception or production latency.
