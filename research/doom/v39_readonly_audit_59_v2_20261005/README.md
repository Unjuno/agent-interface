# V39 A01 read-only archive-audit successor

This additive construction repairs an evidence-integrity defect in the first A01 saved-output auditor without changing the archived A01 result or its auditor. The V1 `audit_a01.py` recomputes a verdict and writes it into the SHA256SUMS-covered `raw/AUDIT.json`. On Windows, Python newline translation changes the archived bytes even when the JSON values are identical.

V2 audits the saved A01 result and full archive inventory without writing to the source archive. It reports to stdout. Its tests use disposable copies to verify both the V1 write and V2 byte preservation; a deliberate tamper case verifies that V2 fails without further changes.

## H/T/D/C/U

- **H:** Auditing retained evidence should not modify any source, raw result, or manifest-covered audit output; a corrected auditor can verify the same saved projection result without writing to the archive.
- **T:** On exact PR #7662 head `719ef679c977a925db3a6d1fe15f9cd93cf2b42c`, copy the original A01 package into two temporary directories. Run V1 on the first and compare all file hashes. Run V2 on the second and compare every byte. Also tamper with a disposable copy and require a fail-closed result without additional writes.
- **D:** V1 mutation is reproduced only if its successful run changes exactly `raw/AUDIT.json`; V2 passes only if its archived-result checks pass and the archive remains byte-identical. The tamper control must fail without changing its post-tamper bytes.
- **C:** A byte rewrite can preserve JSON meaning yet invalidate the retained manifest and original auditor hash. This probe tests local archive immutability, not whether the projection itself is scientifically valid.
- **U:** The V1 byte change depends on platform newline handling; the test separately intercepts the write call so it also detects the defect on platforms where output bytes happen to match. No game, model, GUI, input, or container ran.

## Run

From the repository root:

```powershell
python -B research/doom/v39_readonly_audit_59_v2_20261005/probe_legacy_mutation.py --experiment-id V39-READONLY-AUDIT-59-A02-V2-20261005 --out MUTABILITY_RESULT_A02.json
python -B -m unittest -v research.doom.v39_readonly_audit_59_v2_20261005.test_readonly_audit
python -B research/doom/v39_readonly_audit_59_v2_20261005/audit_readonly_v2.py
```

The probe runs V1 and V2 against disposable archive copies. Each invocation requires a new `--out` path once its default result exists; the result file is outside the archived A01 package. The read-only V2 command prints its audit result and does not write into the archived A01 package. The frozen A02 invocation uses `--experiment-id V39-READONLY-AUDIT-59-A02-V2-20261005 --out MUTABILITY_RESULT_A02.json`.

## Result boundary

V1's saved verdict remains `PASS_SAVED_RESULT_AUDIT`, but its auditor is not read-only. V2 independently recomputes the saved result, verifies every file listed by the original `SHA256SUMS`, and returns `PASS_READ_ONLY_ARCHIVE_AUDIT` without changing the archive. This does not establish physical input duration, application consumption, useful game feedback, live safety, recovery benefit, or MAP01 progress.
