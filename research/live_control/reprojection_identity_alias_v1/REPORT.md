# Reprojection identity alias v1

Issue: #956  
Publication base: `2221053ba1bc0a85d61cb4d68eeb6655b7e0e28e`  
Pinned current controller blob: `0e44f30660d4ef2b4a78ac2b92db7991e7d1c48a`  
Decision: **`REJECT_LOCAL_PATCH_AS_SEMANTIC_IDENTITY_SCOPED`**

## First outcome

One deterministic formal invocation produced 12 rendered cases under Inkscape 1.4; reruns/replacements/tuning were zero.

| Stratum | Gate eligible | Independent semantic identity at reference target point | RGB relation |
| --- | ---: | --- | --- |
| stable identity | 4/4 | `task-target` 4/4 | reference/current decoded RGB identical 4/4 |
| ID-only swap | 4/4 | `decoy` 4/4 | reference/current decoded RGB identical 4/4 |
| changed-color negative | 0/4 | `task-target` 4/4 | intentionally different |

The current gate's exact contract was preserved: radius 5 (11x11 patch), same-shape/in-bounds requirement, maximum per-channel RGB-code error <=8.0. All stable/swap patches had maximum error 0. Changed-color controls were rejected.

The ID-only swap changes no rendered geometry or style: it swaps only the semantic IDs of two visually identical circles. Because the rendered RGB is identical, the current local gate necessarily accepts the object at the old target location even though the authored semantic identity at that location is now `decoy`.

## Interpretation

This rejects **local patch equality as semantic identity**, not target reprojection as a location/currentness hint. It confirms the limitation already stated by the retained visual-followthrough report with an explicit first outcome.

The result is representation-level: if two candidate objects are pixel-identical in the observed patch, no local RGB-only test over that patch can distinguish their authored IDs. A successor should therefore test one additional *current* relation at a time (for example bounded uniqueness/context or action/effect provenance) rather than making the historical patch authoritative.

No repair mechanism is implemented in this rung.

## Scope / uncertainty

The experiment uses headless Inkscape rendering at 640x480, not the full X11 pointer-admission path. The XML identity oracle is audit-only and never enters `gate.py`. No model, GUI task action, user data, token, latency, cross-domain or production claim follows.

## Integrity

- formal deterministic invocations: 1
- reruns: 0
- audit errors: `[]`
- false alias acceptances: 4/4
- source/result hashes are retained with the result; renderer version is recorded in `result.json`.
