# Issue #6424 — finite speech-act/effect gate construction

## H / T / D / C / U

- **H:** For effect-critical user language, a source/turn-bound communicative-force ledger can distinguish a request to execute now from information, preparation-only, hypothetical, quoted/reported, and unresolved-force turns without treating imperative grammar as necessary or sufficient. A valid `EXECUTE_REQUEST` only proceeds to the separate ordinary admission gates; the label itself grants no authority.
- **T0:** Freeze a finite no-model multi-turn corpus and a separately authored actionability oracle. Exercise direct and conventional indirect requests; capability question; counterfactual; quoted third-party imperative; user quoting an earlier request for analysis; prepare-but-don't-send; negation; later explicit adoption; ambiguous force; and a false/unknown-world-premise control for #5977. Audit exact source spans/turn authors, effect, explicit prohibitions, permitted `EXPLAIN/PREPARE/EXECUTE/ASK/YIELD` transitions and the rule that execution labels are not authority. Mutations cross quote boundaries, drop negation, swap turn author, reuse stale prior instruction, and elevate a model-like paraphrase to source.
- **D:** `PASS_METHOD_SCOPED` only if all frozen labels, spans, effects and transitions match the independent oracle and all mutations reject the unsafe transition. The imperative-only baseline must miss the conventional indirect request; the unrestricted action-phrase baseline must over-promote non-execution cases; blanket-ask must ask even on clear direct/indirect cases. Any oracle disagreement or missing boundary is `FAIL_METHOD`; malformed inputs or evidence are `STOP_INTEGRITY`. This finite result cannot establish natural-language accuracy.
- **C:** Source-clause preservation (#5951), provenance/information-flow (#5333), and premise truth (#5977) cover adjacent but distinct questions. In a real system, ordinary source review or one scoped clarification may dominate a typed ledger. Authored cases can make the intended force artificially obvious; paraphrase/model output is not independent evidence.
- **U:** No people, model, GUI, live action, external effect, or prosody. No evidence about speaker intent truth, multilingual/cultural generalization, human burden, false action rates, runtime enforcement, consent, safety, or security. No T1 authority follows.

## Frozen finite contract

Corpus and independent oracle are authored in separate files. Every case names exact turn IDs and source spans; embedded/quoted text remains data unless the user explicitly adopts it in a later authenticated turn. `UNKNOWN_FORCE` may proceed only to narrow `ASK`/`YIELD` before a consequential effect; harmless explanation remains distinct. Explicit prohibitions dominate. The false/unknown premise case is a #5977 control, not attributed to speech-act grounding. The oracle also requires the normal authority/effect gate for every proposed execution, including clear requests.

Formal sequence: one candidate invocation; only on candidate exit 0, one independent raw-only auditor invocation. Retries = 0. Candidate and auditor are standard-library-only; auditor does not import candidate. Construction tests do not consume the formal allocation. No network or external effect.

## Runtime deviation

Current task host did not expose `wslc.exe` on PATH at preflight. This is a small deterministic finite T0; before the formal run, record exact host/runtime and verify no shared container is touched. The host-only execution is not WSLc/container evidence and does not satisfy claims requiring isolation. Do not launch Docker/OrbStack as a substitute without a frozen protocol requiring it.

## Formal outcome — `FAIL_METHOD`

Allocation `SPEECH-ACT-GROUNDING-6424-T0-20261002-01` was run once on 2026-10-02 with source frozen at main `4da4257ad481e9a4ea79133bdaf93c962e686fe7`. Candidate exit 0; independent raw-only auditor exit 1; retries 0. The candidate's eleven rows matched the finite transition oracle and all source spans, but the auditor rejected the allocation because its `turn_author_swapped` mutation check was not a real mutation: it compared the unchanged candidate row to the unchanged expected transition, so the case could not reject a changed turn author. Five other declared transition-corruption probes rejected, but they too are not a substitute for actually transforming and re-adjudicating the inputs.

Raw stdout/stderr/exit sidecars and candidate/auditor JSON are retained unchanged. Do not rerun this allocation or promote its partial row parity to PASS. A useful successor must explicitly generate mutated input variants, rerun only a pure frozen classifier over those variants, and independently audit both source author and resulting transition; it must not repeat the original candidate allocation. Host-only macOS/CPython execution is a declared WSLc deviation; no Docker/OrbStack container was started. No H-level, language, human, runtime, authority or safety conclusion follows.

Repository-local post-run checks: analysis index refreshed at 388 retained directories; workspace index 154 reachable directories; workspace-index unit test 1/1; `git diff --check` clean. These index/CI checks are delivery validation, separate from the failed T0.
