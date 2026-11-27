# P09 matched caller comparison — result

**Decision: incomplete for the preregistered full pass.** The experiment produced a matched, descriptive Fake X comparison, but the redactor changed JSON-like `.bin` files under `ledger/raw`. ProviderAttemptRecorder therefore rejects raw-response hashes in all six cells. The retained before/after hashes identify the transformations but cannot reconstruct the original bytes. Full raw custody and usage-to-ledger reconciliation are unverified.

Three counterbalanced pairs compared one direct `interface_guarded_input` click with one `interface_guarded_compiled` click. All six model turns selected `[16, 8]` from the exact public observation image. A post-hoc scorer that read only retained owner/provider evidence found 6/6 exact target clicks, 6/6 single effects with the expected red pixel, and 6/6 verified releases and closes. The runtime `task_success` remained null in every cell. This describes task effects on deterministic Fake X only; it does not qualify WSLc, live GUI, MAP01, blocked-I/O recovery, or broad reliability.

The original runner classified three cells as pass. The other three had local evidence-processing defects: P01/direct stopped while serializing a close receipt; P01/compiled and P02/compiled looked for click count and completion fields in the wrong response shapes. The original `RESULT.json` files and first outcomes remain unchanged. Additive supplemental scores confirm the underlying clicks/effects for all six; they do not repair the failed raw-ledger custody requirement.

| Measure | Direct public input | Compiled public caller | Paired difference, direct minus compiled |
|---|---:|---:|---:|
| Provider turn latency, median of 3 (ms) | 5,157.6 | 4,449.9 | +1,214.2 ms median paired difference |
| Observation-to-action return, median of 3 (ms) | 5,403.6 | 4,722.2 | +1,188.3 ms median paired difference |
| Total trial time | 7,195.1 ms median of 2 available | 5,353.2 ms median of 3 | +1,966.3 ms median paired difference over 2 complete pairs |
| Input tokens, median of 3 | 10,197 | 10,203 | −6 tokens median paired difference |
| Output tokens, median of 3 | 60 | 57 | +3 tokens median paired difference |
| Reasoning output tokens, median of 3 | 41 | 38 | +3 tokens median paired difference |
| Public tool calls / compiled transitions | 5 / 0 | 5 / 1 | same public-call count |

These are descriptive estimates from three pairs, not a reliability claim. The direct P01 total-trial duration was not emitted because that runner stopped after action/close; paired total-time comparison therefore has only two pairs. The observation-to-action metric was recovered from the retained observation capture and public response timestamps for that cell.

P09 also exposed a privacy-redaction defect. `privacy_redact.py` has been corrected to leave `ledger/raw` and `.bin` files byte-for-byte unchanged, and the new local regression test covers raw immutability plus nested JSON scrubbing. A post-hoc path scrub removed remaining local Windows paths from exports; the initial packet manifest and final packet manifest bracket those sanitized states. Both fixes apply to future runs only. The six P09 raw ledgers remain untrusted for exact reconciliation.

Evidence and independent checks are in [AUDIT.json](AUDIT.json), per-cell `run/*/SUPPLEMENTAL-SCORE.json`, original `run/*/RESULT.json`, amendments [001](AMENDMENT-001.json) through [005](AMENDMENT-005.json), [SANITIZATION-POSTHOC.json](SANITIZATION-POSTHOC.json), the [initial packet manifest](SHA256SUMS-PACKET-INITIAL), and the final [packet manifest](SHA256SUMS-PACKET). The preregistered conditions and source freeze are in [CONDITIONS.json](CONDITIONS.json) and [PRELAUNCH.json](PRELAUNCH.json).
