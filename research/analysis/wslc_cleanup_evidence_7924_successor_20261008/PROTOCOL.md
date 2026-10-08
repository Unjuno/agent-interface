# WSLc cleanup receipt contract — offline successor

## H/T/D/C/U

**H — hypothesis.** A scoped cleanup verifier that emits a structured receipt before deciding PASS/FAIL can preserve the owned container identity, query exit code, and exact response for both confirmed absence and unverified cleanup; it will not interpret malformed, non-empty, null, or failed-query responses as absence.

**T — treatment.** The PowerShell helper classifies a supplied exact-ID query result and serializes the full identity/status/raw-response tuple. The current-main smoke script writes that receipt before throwing on an unverified result.

**D — design.** Six deterministic responses: compact empty array, whitespace-formatted empty array, non-empty exact-ID row, malformed text, nonzero query exit, and JSON null. Candidate output must retain the same 64-hex ID, exit code, and raw response for every row. No runtime service is called by this protocol.

**C — comparison.** An independent Python auditor decodes the raw JSON and exit code using Python's JSON parser rather than importing PowerShell or reusing the helper. It checks literal coverage and classifications and rejects four mutations: false absence for a remaining row, erased response, erased ID, and query error classified as absence.

**U — uncertainty and limits.** The original unregistered WSLc invocation on main exited 1 after read-only bind verification, because its scoped query did not satisfy the empty-array check. Its `finally` removed the temporary CID and no raw query output was logged. We cannot reconstruct that response or infer whether the container remained. This offline contract does not explain the original response, prove WSLc cleanup, or qualify a runtime.

## Frozen inputs and commands

The six cases are literal source fixtures in `test_wslc_cleanup_receipt.ps1` and are pinned by `FREEZE.json`. The formal candidate is one invocation of that PowerShell script writing exclusive `results/candidate.json`; the formal independent auditor is one Python invocation writing exclusive `results/audit.json`. Unit tests are construction checks and are not counted as formal candidate/auditor runs.

## Stop rules

- Do not invoke WSLc, Docker, inspect/list containers, or attempt cleanup from this offline package.
- Candidate runs once; run the auditor only if candidate exits 0 and output exists.
- No retries or edits to frozen source, fixture, or protocol. Any correction gets a new successor package.
- This is `PASS_RECEIPT_CONTRACT_SCOPED` only if all six rows match the independent interpretation and all four audit mutations are rejected. No WSLc runtime, migration, memory, speed, parity, or cleanup claim follows.
