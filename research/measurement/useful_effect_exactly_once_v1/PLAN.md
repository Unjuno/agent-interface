# Useful-effect exactly-once v1 — construction

H: Holding parent #941 actuation/effect semantics fixed, each effect-delivery record needs an explicit nonblank `effect_id`; duplicate IDs fail closed, while identical payloads with distinct IDs remain distinct effects.

T: Pure standard-library/container construction. Reproduce parent double counting first, then use a wrapper record plus ID gate. Fixed duplicate/distinct/malformed controls, 100,000 seeded delivery sets with duplicate injection against an independent set oracle, and 50,000 all-unique traces proving predecessor role counts remain exact. No #946/#950/#953/#869 allocation is touched.

D: Construction passes only if predecessor duplicate double count is reproduced, duplicate or malformed effect IDs reject, distinct IDs never collapse solely because payloads match, and unique-ID role counts exactly equal parent counts.

C: A transport may already guarantee exactly-once delivery, but the guarantee must be explicit. Effect-record replacement/versioning is a different semantic and is excluded.

U: Synthetic record-delivery evidence only; no distributed durability/X11/MAP01/usefulness-quality/production claim. Formal authorization is false.