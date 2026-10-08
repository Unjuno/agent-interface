# Preregistration — Issue #5919 locale-conditioned semantic invariance T0

**Frozen:** 2026-10-01 08:32 UTC  
**Source main:** `cdfebdb125e0566d2cbe741c4925b94eb17b439b`  
**Branch:** `research/locale-semantic-invariance-5919-t0-20261001`  
**Allocation:** deterministic, model-free, synthetic in-memory V8 contract evaluation. No GPU or container is allocated; neither helps this finite symbolic check, and the machine's C: volume is full with Docker unresponsive.

## H / T / D / C / U

**H.** A typed locale relation over independently specified expected effects accepts presentation-only locale changes, rejects wrong target/value/authority/input mappings, and yields UNKNOWN where translation equivalence is ambiguous. At least one seeded semantic regression will be missed by the English-only and visual-proxy baselines but caught by the typed relation.

**T.** Evaluate the frozen eight-case fixture once with the candidate. It contains two benign paired tasks (theme setting; decimal amount entry), five injected faults (misread translation, swapped target, mutated parsed amount, keyboard-layout mismatch, weakened authority), and one ambiguous translation. The candidate checks perception mapping, logical input, target, value, authority, effect count/status, and receipt lineage. Baselines are frozen in the fixture: exact rendered-string equality, English-only outcome, and a declared *synthetic visual-similarity proxy*. Then run the independently implemented auditor once against the raw fixture and candidate output. The auditor also checks three deliberately corrupted candidate-result copies.

**D.** `METHOD_PASS` iff both benign cases produce PASS; every injected mutation produces FAIL at its declared primary stage; the ambiguous case produces UNKNOWN; and the independent auditor reports zero mismatches while rejecting all three corruption controls. `H_PASS_SCOPED` additionally requires at least one injected FAIL for which the English-only and visual-proxy baselines both fail to flag a regression, with no false PASS. Otherwise report FAIL/UNCERTAIN exactly as observed. No retries.

**C.** The source outcome could be detected by a better locale-aware model, parser, or ordinary symbolic validation without this paired relation. The visual-similarity flag is fixture metadata, not a measured image metric; expected mappings/effects are stipulated by the synthetic oracle and receive no independent translation adjudication.

**U.** This can establish only contract behavior on these synthetic pairs. It says nothing about natural translation quality, any model's multilingual competence, real apps, assistive technologies, user preference, end-to-end equivalence, or global novelty.

## Frozen execution and integrity rules

- Fixture seed/id: `locale-semantic-5919-t0-20261001-v1`; no random sampling.
- Candidate invocation limit: exactly 1. Auditor invocation limit: exactly 1. A startup/binding failure is retained and is not retried.
- The candidate and auditor are separate source files; the auditor must not import/call candidate code.
- Preserve raw outputs, source blobs, run metadata, and all discrepancies. A failed/unknown result cannot be promoted.
- No model/provider, network, GUI, Docker, GPU, or host subprocess is part of this T0.
