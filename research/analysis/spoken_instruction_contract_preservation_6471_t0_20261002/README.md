# Issue #6471 — spoken-instruction contract-preservation T0

## H / T / D / C / U

- **H:** At the same word-error rate, a contract-critical slot gate can distinguish benign transcript noise from a wrong recipient, target, bound, negation, or speech-act change, while preserving a narrow clarification path for genuinely ambiguous source clauses.
- **T0:** A finite, authored, no-audio/no-model corpus supplies paired source text, source contracts, candidate transcripts, transcript slot labels and source/transcript character-span links. It includes equal-WER benign-vs-recipient substitutions, deleted prohibition, homophone target, numeric-bound change, quoted/explanatory source reduced to an imperative transcript, and genuine recipient ambiguity. Candidate emits a fail-closed disposition; independent raw-only audit checks the frozen oracle, span links, exact denominator and planted label/span mutations.
- **D:** `PASS_METHOD_SCOPED` only if all seven cases are present exactly once; the equal-WER pair has identical WER; all source/transcript span links reconstruct; all expected dispositions match; and every planted mutation is rejected. Any discrepancy is `FAIL_METHOD`; malformed or missing frozen evidence is `STOP_INTEGRITY`. This does not test ASR or the H.
- **C:** Human-confirmed transcript, richer-model clarification, or existing source review may dominate the gate. Hand-authored transcripts and slot labels may make the cases tautological. WER tokenization, fixture coverage and oracle authoring are potential artifacts.
- **U:** Audio/prosody, accents/languages/noise, speaker identity, intent truth, privacy/consent, model proposals, clarification burden, latency/tokens, GUI effects, authority enforcement, safety and deployment transfer.

## Frozen boundary

This is only the T0 representation boundary proposed in Issue #6471, not speech recognition. `source_text` is an authored text stand-in, and all offsets are Unicode character offsets into those authored strings—not audio timestamps. Candidate transcript slot labels are fixed synthetic inputs, not outputs from an ASR/model. An allowed disposition still grants no action authority; it means only that this fixture has no contract mismatch and must pass ordinary independent authority/effect gates.

Formal order is one candidate invocation, then (only on exit 0) one independent auditor invocation; formal retries are zero. Construction tests are separate from those caps. No network, model, audio, human, GUI, application or external effect is involved.

## Environment status

The task host is macOS/arm64 and does not expose `wslc.exe`/`wslc`. The governing experiment cadence requires WSLc for eligible local CPU work. Do not substitute the shared OrbStack/Docker daemon: this protocol has no Engine API, Compose, unsupported resource-control or GUI requirement. Host-only construction tests may check fixture integrity, but they are not the formal candidate/auditor allocation and cannot be reported as T0 PASS/FAIL.

Current disposition: `HOLD_RESOURCE_WSLc_UNAVAILABLE` pending a usable authorized WSLc lane. Formal candidate invocations = 0; formal auditor invocations = 0; formal retries = 0. The source freeze and construction check are retained for continuity; no model- or speech-level hypothesis is evaluated.
