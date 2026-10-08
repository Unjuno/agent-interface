# Host-local construction result — JSON primitive envelope boundary

Allocation: `PRIMARY-REFUSAL-TERMINALITY-5693-JSON-PRIMITIVE-CONSTRUCTION-20261001-01`.

**H:** JSON content bodies that parse to null, a string, number, boolean, or array must latch STOP inside the response-envelope boundary and must not permit a second effectful dispatch.

**T:** One host-local Node v24.6.0/Windows construction-matrix run against `primary-policy.mjs` SHA-256 `f8ddede770165eb66d988c8830e661fa5ce98c6dadd8ee4f7be68a92bea9c250`. Five synthetic JSON body types; each was passed through the actual caller factory. The primary caught the initial TypeError, attempted a second dispatch, and then used public close. Only the mock transport was replaced. The module was loaded from exact GitHub source bytes in a data URL because the local C: volume had no free space; behavior code was the retained `construction_matrix.mjs` except for that import binding.

**D:** `PASS_JSON_PRIMITIVE_TERMINALITY_CONSTRUCTION`: all five rows show STOP before the primary continues, second attempt rejected locally, effectful host calls fixed at one after retry, close allowed. Independent raw-only check: `PASS_JSON_PRIMITIVE_TERMINALITY_CONSTRUCTION`, five rows.

**C:** Synthetic caller-factory construction only. No Docker/OrbStack container or formal candidate CLI ran. The formal five-case #5693 candidate remains uninvoked pending a fresh exclusive resource gate and digest-pinned Node image.

**U:** Does not establish real MCP transport behavior, live refusal, GUI/game effect, input release, MAP01 control, safety rates, efficacy, latency, or product readiness. #5693/#59 remain open.

Exact one-line raw output is in `CONSTRUCTION_RAW.json`; its separate auditor output is in `CONSTRUCTION_AUDIT.json`. Reproduction sources are `construction_matrix.mjs` and `audit_construction.mjs`. A baseline RED for JSON-null replay and GREEN after the in-boundary shape guard was recorded on #5693 before this five-type matrix.