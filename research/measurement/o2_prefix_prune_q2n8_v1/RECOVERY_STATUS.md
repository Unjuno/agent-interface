# Recovery status (2026-10-01)

This delivery preserves the original branch's plan, report, compact-publication
metadata, restorer, and all publication fragments that were present. The
fragments are intentionally unchanged, including integrity defects:

- `part03.b64` is absent (the manifest declares eight parts).
- `part02.b64` is 5,295 bytes instead of 12,000 and does not match its declared
  SHA-256.
- `part04.b64` is 12,001 bytes instead of 12,000 and does not match its hash.
- `part07.b64` is 11,728 bytes instead of 11,729 and does not match its hash.
- Present parts 00, 01, 05, and 06 match their declared lengths and hashes.

Running the supplied `restore.py` stops at `part02.b64` integrity validation;
it does not reach compact-archive hash validation or extract an archive. The
reported 6,289-check local verifier result and 24-condition scientific outcome
in the Issue/report remain historical claims, not independently reproduced
from these repository artifacts. No missing part or byte was reconstructed,
and no experiment was rerun.

This is an incomplete publication-recovery snapshot, not a valid compact
evidence package and not runtime qualification. Preserve the original
fragments unchanged; recover exact original bytes before attempting the
read-only verifier. Issue #4423 remains open.
