# Shared sampled-target contract candidate

sampled_target_contract_v1 extracts the fixture-specific menu guard into an application-independent evaluator. A trusted caller declares name, box, point and max_age_ms; the model proposal names that intent and execute_once=true. The evaluator validates the contract, new observation ordering, sampled focus/binding consistency, empty owned-input samples, matching image shape and exact target pixels. It returns a point, current sequence and capture-derived deadline as evidence for existing admission. It sends no input, does not renew a lease, and does not maintain a once-only execution ledger. The caller still needs the existing unique program identity/command-receipt mechanisms.

The experimental age bound is1–1000ms. Click point must lie inside both the declared patch and observed surface geometry; boxes must be valid image bounds. Booleans cannot substitute for numeric age/sequence fields. Malformed observations produce a structured refusal. Source and fresh before/after focus samples must agree with the binding. Focus need not equal surface: actual desktop applications use a child input focus inside a top-level client. The contract remains a sampled-pixel predicate, not an application readiness or semantic target identity proof.

probe_sampled_target_contract_v1 replays four existing actual observation cases, with source artifact hashes retained:

- Mindustry positive click case: eligible point/deadline identical to the earlier guard.
- Mindustry real overlay case: target_patch_changed, no promotion to eligible.
- Mindustry real focus-loss case: binding_changed.
- Inkscape X-coordinate field: source frame12 to frame15. A tooltip appears outside the declared field; the field patch remains identical, and distinct focus/surface IDs are retained. This is archived eligibility, not a new click or saved-document validation.

The Inkscape box509,90–606,123 and point550,106 were chosen after inspecting the actual screenshots. The probe uses historical image_ready_ns for the comparison time, explicitly not current time. This is development replay, not a held-out benchmark. Nine controls reject boolean age, point outside patch, expired observation, boolean sequence, disagreeing focus sample, held key, numeric execute_once, changed pixels and reused sequence. Results live in results/sampled-target-contract-01/report.json; no new model calls or live inputs were performed.

Example trusted contract: {"name":"focus_x_coordinate","box":[509,90,606,123],"point":[550,106],"max_age_ms":1000}. Proposed intent: {"intent":"focus_x_coordinate","execute_once":true}. A positive evaluate result is not permission to send arbitrary coordinates: callers must use that result's sequence/deadline with the normal shared owner, honor refusal and avoid implicit replay. Do not let an untrusted model silently expand the box or action scope.

Remaining work: wire one new desktop live episode through this evaluator, verify the intended application effect independently, and measure the complete decision-to-input path. Also test the gap between sampled patch validation and input; exact pixels do not protect against hidden semantic changes or changes after capture. Existing live menu versions remain frozen and this contract is not a promoted default. Avoid making variants of the same guard without moving it into an actual caller.
