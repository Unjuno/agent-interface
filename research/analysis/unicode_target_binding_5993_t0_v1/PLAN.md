# Issue #5993 T0 plan — synthetic target binding

## H / T / D / C / U

- **H:** Exact fresh comparison of independent intended target ID to
  application-resolved target ID can refuse wrong-target effects without
  blanket refusal of legitimate multilingual exact IDs. A string-only decision
  can act on the fixture's resolved target even when its displayed label equals
  the requested label but its exact ID differs. A Unicode-skeleton warning is
  informative only and is not authorization.
- **T:** A frozen, exhaustive 15-case finite table × 3 policies = 45 rows (one
  row per case/policy; no statistical population estimate). Each case records
  requested label, authored displayed label, independently intended exact ID,
  resolved ID (or absent), freshness, resolver rule and fixture class. Compare
  literal-label-only, skeleton-warning-only and exact-fresh-ID-binding.
  Candidate and raw-only auditor are separate programs; the auditor does not
  import candidate code. Construction controls test missing/duplicate rows,
  wrong effects, unsafe authority, label mutation and missing bidi warning.
- **D:** `PASS_METHOD_SCOPED` only when all 45 rows independently reconstruct,
  exact-fresh binding has zero wrong-target effects, benign fresh exact IDs are
  accepted (including RTL/multiscript), all six declared aliases reach the
  string-only effect path, the five skeleton-colliding aliases warn, the
  unrelated mismatch does not spuriously warn, stale/missing IDs fail closed,
  and warning-only never suppresses the effect or gains authority. Any
  inconsistency is `FAIL_AUDIT`/`FAIL_METHOD`; no GUI/security PASS is possible.
- **C:** An authored fixture alias is not a rendered-glyph collision. Skeleton
  matches are not visual equivalence, authorization or semantic equality.
  Actual app normalization, font shaping, screen/accessibility representation,
  focus races and resolution behavior are not observed here.
- **U:** Synthetic table only; no GUI, model, real targets, files, messages,
  credentials, destructive action, prevalence, exploitability, safety or
  product claim. `unicodedata` behavior is Python's bundled UCD 15.0.0 while
  mapping/property inputs are pinned Unicode 18.0.0; this mixed-version
  limitation is recorded. A T1 requires a separate disposable GUI fixture,
  allocation and current coordination check.

## Freeze boundary

Formal execution must not start until the exact source/corpus/plan hashes,
Unicode input hashes, interpreter, command and current-main base are committed
to an additive branch. Run candidate once; run auditor once only if candidate
exit is zero. No retry or repair of a formal outcome. This run is CPU-only and
does not use the shared Docker/OrbStack allocation. Local Docker CLI inventory
and `docker info` previously timed out; the Docker Desktop UI showed Engine
running but did not establish a usable daemon connection.

## Repair history before freeze

The first unformalized preparation omitted separate requested/displayed labels.
A bidi boundary probe showed equal Unicode 18 internal skeletons but produced
no string-only effect or warning because the case was marked unresolved. That
preparation was not formally run or published as a result. The repaired fixture
now states each label and exact ID independently, includes an authored bidi
label-alias mapping and explicit resolver rule, and asks the raw auditor to
reconstruct those fields. The alias is deliberately authored; no glyph claim is
made.
