# V39 static-cover health response posthoc A01/A02

## Result

**A01: STOP. A02: PASS for the narrow posthoc stale-policy observation.** The retained v39 coast-liveness event stream records one accepted 16-step `cover-5` program. Its immediately preceding typed sample (sequence 166) reports health 61. After the static program begins, the first typed health sample (sequence 167) is 55; the last sample before the cancel request (sequence 218) is 48. The 52 typed samples span 9.043272486 seconds from the first to last cover sample. The program reached step 11 after completing steps 0–10, while the originally accepted 16-step program remained in force. The raw stream records no `revoked` or early `input_released` event for this program before the external cancel request.

The cancel request came 164.939131 ms after the last typed sample. Terminal evidence records verified empty input 0.813066 ms after the request and terminal cancellation 14.183481 ms after that verification. This bounds what the log shows; it does not measure physical key-up or establish that the policy caused the health loss.

## H/T/D/C/U

- **H:** A static accepted cover can continue after sampled typed health has declined, without a logged local cancellation/revocation before the external cancellation request.
- **T:** The candidate and independent standard-library auditor reconstructed the fixed command, step events, typed health samples, cancel, empty-release, and terminal timestamps from the SHA-bound original raw stream. A mutation control replaced the reported last health with 999.
- **D:** A02 passed all raw-to-summary checks; the primary audit passed, and the altered summary was rejected. A01 remains STOP because its CRLF shell runner failed parsing after the candidate and primary audit, before the mutation control.
- **C:** Health loss may not be avoidable by another policy; values are sampled and may miss intermediate state; the repeated cover may have remained task-appropriate; runner intent and guard evaluation are incompletely logged. No alternative policy was tested.
- **U:** This is a posthoc observation from one live trace, not a new allocation or causal comparison. It does not establish independent useful task-feedback onset, bounded recovery efficacy, survival benefit, matched performance, exact key release, or MAP01 completion. Run score remains 1 kill, 0 deaths, no exit.

## Provenance and audit

The retained event stream SHA-256 is `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`; its source manifest SHA-256 is `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`. A02 used the cached Python 3.12 image pinned by digest, network disabled, and a read-only checkout mount. WSLc warned that swap limits are unsupported; strict total-memory enforcement is not claimed. The candidate, independent auditor, runner, raw output, parsed reports, mutation result, run metadata, and package audit are retained beside this file.

The stale-policy interval is a concrete requirement for a future fresh allocation: evaluate whether a bounded health-triggered local stop/alter/escalate guard can react before the slow model returns, while measuring useful task effect and release. This record alone does not authorize such a run.
