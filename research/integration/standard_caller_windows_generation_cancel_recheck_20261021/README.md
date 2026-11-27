# Windows standard-caller generation and cancellation recheck

## Result

The three selected `OwnedProcessMCPTests` passed under both normal Python and `python -O` (3/3 each). They cover compiled-caller mid-action refusal after process-generation change, alias refusal after target-generation change, and owner retirement after blocked platform sync while keeping release `UNKNOWN`.

This adds Windows-host standard-MCP/Fake X regression evidence for the target-generation refusal path. The tests use repository fixtures and do not establish X11 server behavior, physical input release, application task effects, or release while a real platform call is blocked.

## Reproduction and custody

The exact test selectors, runtime, revision, source SHA-256 values, and limits are in `conditions.json`. Captured outputs are `public-evidence/raw/normal.txt` and `public-evidence/raw/optimized.txt`. `public-evidence/SHA256SUMS` covers the sanitized publication copy.

The earlier test-selector typo was a unittest loader error before any named test ran; it is not part of the experimental result. The corrected invocation is captured in these two output files.

No production code or tests were modified. No WSLc allocation or external service was used.
## Shared evidence copy

The local `raw/` tree retains the original unredacted records and is intentionally excluded from publication. `public-evidence/` contains text-only redacted copies, the publication redaction record, and a separate `SHA256SUMS`. Only local checkout/user-profile/cache paths and the local host name were replaced; measured values, statuses, timings, request records, and synthetic images are unchanged. Run the public-copy auditor from `public-evidence/` where provided.
