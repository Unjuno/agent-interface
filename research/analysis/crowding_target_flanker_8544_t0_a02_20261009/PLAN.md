# Issue #8544 T0 A02 — target–flanker endpoint scorer method check

## Scope and successor reason

This new allocation follows A01's `STOP_CANDIDATE_LOG_REDIRECTION`. A01's shell could not open logs under a nonexistent `results/` directory; the Python candidate never started and the auditor correctly did not run. A01 remains unchanged. A02 uses a fresh allocation and output namespace. Its wrappers create `results/` before any redirection, write a start receipt before invoking the formal role, refuse retries, retain exit/stdout/stderr and output hashes, and gate the auditor on candidate exit 0 plus a retained raw file.

The test is the Issue's no-model T0 measurement-method check. It does not test any VLM or crowding transfer signal. Authority is `NONE`. The current-main anchor at allocation is `a6343bb76e4dc0a4afa32a29c8a485a617faeff8`; no runtime source is consumed or modified by this finite scorer.

## H / T / D / C / U

**H.** A preregistered scorer can distinguish correct target binding, neighbor substitution, miss, abstention, schema error, ambiguous identity, correct rejection, and false alarm while preserving detection separately from identity binding. A fully crossed synthetic ledger can keep spacing, image-space eccentricity proxy, target size, flanker condition, placement, and presence balanced across disjoint development/held-out seeds with global control count fixed.

**T0.** Generate 5,632 planted response cases over presence (present/absent), spacing (24/72 px), image-space eccentricity proxy (120/360 px), target size (24/48 px), flanker similarity (near duplicate/dissimilar/text-distinct/no flanker), placement (inward/outward), eight layout seeds and endpoint templates. Six seeds are development and two held out. A raw-only auditor independently reconstructs exact fixture IDs and denominators, binds every ID to its row payload and allocation, scores response schema/identity/point against frozen target and neighbor rectangles, checks paired seed support and split isolation, verifies complete factor crossing at constant global control count, and applies seven mutations. The endpoints are planted; this does not estimate spacing effects or predictor performance.

**D.** `PASS_METHOD_SCOPED` only if all 5,632 cases appear exactly once; all eight endpoint classes match; wrong-neighbor binding remains distinct from miss; target-absent correct rejection and false alarm remain distinct; held-out seeds do not overlap development; every factor stratum has all eight seeds; global control count is four; factorial crossing is complete; all seven mutations are rejected; and both formal roles complete once with retained outputs and zero exit. A failed scientific gate is `FAIL_METHOD`; invocation/custody errors are retained as STOP/HOLD with no retry.

**C.** This checks a deterministic scorer on planted JSON outputs only. It does not validate an image renderer, natural-language prompt, independent image annotation, or endpoint stability on model responses. Global item count is controlled while local geometry and flanker conditions vary intentionally.

The construction audit was strengthened before A02 freeze after noticing that A01 checked the fixture-ID set and row-factor balance separately without asserting that each row's factors encoded in its ID matched its payload. A02 explicitly binds the row identity and allocation and adds a mutation that changes a factor while retaining the old ID. This is a scorer-integrity gate, not a new transfer claim; A01's first outcome is unchanged.

**U.** No model call, image-based judgment, human participant, GUI actuation, or empirical predictor comparison occurs. No transfer signal, null transfer finding, human equivalence, cross-model generalization, real-app safety, or runtime adaptation follows. Host CPU and Python standard library only; no network, external effect, user data or container semantics.

## Frozen execution

Construction suite must pass before freeze, with formal `results/` outputs absent. Freeze exact source/input/script hashes on the A02 branch and preregister the freeze commit on Issue #8544 before either formal command. Then run `sh run_candidate_once.sh` once. Only when its retained exit is zero and raw exists, run `sh run_auditor_once.sh` once. No retries or post-freeze edits to frozen inputs/source/scripts. The wrappers create their output directory before redirecting logs and enforce one-shot receipts.
