# Preregistration — Issue #5333 contextual-flow disclosure T0

Status: construction and formal execution pending. This is a new finite successor-style test within open Issue #5333, not a rerun of the local predicate-only toy noted in that Issue.

## H / T / D / C / U

- **H:** With actor authorization, source confidentiality/integrity labels, and source datum held constant, a recipient-and-purpose-bound flow policy can distinguish one allowed disclosure from a prohibited disclosure, preserve one explicitly scoped release, and fail closed when context is incomplete.
- **T:** Eleven deterministic synthetic flow cards; compare `ACTOR_ONLY`, `LABEL_ONLY`, and `CONTEXT_BOUND` decisions. The matched recipient/purpose cases have the same actor capability and data labels. Include narrow task purpose, a different recipient, explicit release with exact field/purpose/revision, recipient or purpose missing, excessive requested fields, stale release revision, low-integrity evidence to a high-integrity sink, one known PUBLIC source, and one OPAQUE/unknown source label. Independent audit reconstructs each decision from frozen input and policy records and rejects eight planted output corruptions, including an unapproved extra output field and an opaque-label false allow.
- **D:** `PASS_METHOD_SCOPED` only if all expected rows reconstruct, the matched allowed/forbidden pair differs only in recipient or purpose and is correctly separated, exact scoped release is preserved, for CONTEXT_BOUND, missing/opaque/stale cases do not disclose while a known PUBLIC source remains allowed, low-integrity influence is not accepted at the protected sink, and each corruption is rejected. This is a protocol fixture result, not an implementation or information-flow enforcement claim.
- **C:** Norms and policy tuples are stipulated by this fixture. The result depends on the exact schema and eleven rows; it does not establish that natural-language or pixel-derived context can be inferred correctly.
- **U:** No model, human, real personal data, GUI, network, runtime enforcement, covert-channel analysis, privacy benefit, safety, or production suitability is tested. Labels and receipts are synthetic policy evidence only.

## Frozen execution boundary

- Runtime: locally cached WSLc Python image `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4` (Python 3.12.14), network disabled; no image pull/build.
- Candidate: one invocation. Independent raw-only auditor: one invocation, only after candidate exit 0. Retries: zero. Construction checks are excluded from the formal candidate/auditor counts.
- One CPU, requested 256 MiB, unprivileged UID 1000, read-only source mount and separate output mount. Requested memory is not treated as proof of enforcement; retain WSLc/cgroup warnings and host observation.
- No GPU: this finite string/record semantics workload contains no tensor or parallel numeric kernel. No GUI, model/provider, external effect, or private data.
- Formal freeze: record current main SHA, file SHA-256 values, runtime image identity, container command, and clean output path in `FREEZE.json` immediately before construction and candidate start. If any source/policy/hash/image/output gate fails, preserve STOP without invoking the formal candidate.
