# Direct saved-data science review

Reviewer: /root/a05_science_audit. Independent of producer/client author; authored auditor.py and construction_checks.py, so this is not a non-author review of those programs. Read-only review; no imports, scripts, tests or containers executed.

Reconstruction agrees with six exact keys, source/fixture hashes, saved wire/journal hashes and raw/audit results. Healthy callers echo at 4.013083/3.891067/4.762381 ms. Held main: 404.901613 ms, 70 request bytes, two journal rows; held composed: 401.287938 ms, zero peer bytes, one intent row; held bounded: 50.472099 ms, zero peer bytes and journal rows.

Readiness precedes every caller. Scheduled checkpoints occur at 252.847–260.803 ms; release begins at 400.100–400.235 ms. All peers exit zero through driver-triggered EOF and are reaped before client.close; all saved endpoints close without errors.

No merge-blocking scientific finding for archival of the fixed V1 package. Approval is scoped to sent-journal acquisition in this finite fixture. No hard 50 ms guarantee, close-alone efficacy, V2 qualification or general product benefit. A sent row alone proves neither send nor no-send; peer receipt and source-derived OS-entry inference remain distinct. Five corruption controls cover only their declared evidence failures.
