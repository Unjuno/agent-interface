# Public task context in the MCP observation response

Observed integration gap: native_observe originally exposed a source receipt and
image, but the model needed the harness's separate stdout to know the task. The
MCP successor includes the existing public goal.json and exchange-contract.json,
each with the hash of the exact parsed bytes. These are recorded context, not
freshness/authority or scoring. It does not read evaluation.json or infer goals
from pixels. Missing fields are unavailable; malformed records need review and
do not erase a valid observation/image. The goal's semantics are not validated.
Goal/contract/image are not claimed to be an atomic cross-file snapshot.

Validation:38 tests pass, including the actual stdio protocol, public goal/hash,
exchange bound, private-score exclusion, missing/malformed/NaN input, unchanged
bytes and retained image despite a malformed goal. The primary assistant also
read the enriched historical Inkscape observation through the SDK bridge; it now
exposes rightward movement with geometry preservation and max_stages2 together.
This is read-only historical presentation, not a new GUI execution/model trial.

`check.py` compares the two retained MCP result files, checks all
prior metadata and the complete image block are identical, and verifies both
context sources/hashes. Exact before/after responses and context source bytes
are archived here; original absolute paths are provenance, not reproduction
requirements. The predecessor live evidence is separately archived in
native-mcp-live-01. This check does not independently validate task semantics.

No sensor, runtime admission change, extra model, new GUI allocation, host
registration, speed claim or token-saving claim. Added task context costs bytes;
whether it improves model decisions or avoids host turns remains unmeasured.
