# Needle role-skill robustness — fresh-seed successor

Issue #4580; successor intake #4529; lineage #3890 / #4479. Allocation `needle-role-skill-robustness-3890-v3-fresh-20260927`.

## H / T / D / C / U

**H — hypothesis.** The exact merged #3890 A→B→C role-skill package remains competent across a genuinely fresh ten-seed block; every JSON-only package reloads in two clean containers with exact builder-prediction parity and generation-bound receipt behavior.

**T — treatment.** Current-main freeze base `e8c0e24ecdf409c74dc8266fe3e86ddad906ade4`. Reuse exactly the #3890 builder, loader, auditor basis, data generator, architecture, optimizer, graph, and evaluator after verifying their SHA-256 against #3890 `FREEZE.json`:

- runner `a0e99b991a8a3ab9b2f4b6f4f22f7c705989447ce64a14738026fcd763b55abb`
- loader `5ff6df91ea3929f68fe77ccd6156bdb1310d0fec86088489d8b99905a7c5854f`
- upstream auditor basis `4e53e241aa115202ce9ca2ce3a5b3df76599b80ad03290a61594bd6b0e35c3a0`
- upstream preregistration `b2ccbac02e0d759c662b955fb34127310ea87d2cbdfe72d91b356a750ffd3c7a`
- cached image `needle-pilot05:local`, ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`

Fresh seeds (do not replace): `2026092700, 2026092800, 2026092900, 2026093000, 2026093100, 2026093200, 2026093300, 2026093400, 2026093500, 2026093600`; all derived substreams are seed +1..+12. They are disjoint from #3890 formal/retired seeds and both contradictory, never-run #4479 candidate schedules. Exact Docker environment bindings are mandatory: `NEEDLE_SEED=<that seed>` and `NEEDLE_OUTPUT=/out`. Each builder has a unique empty writable seed directory; both loaders are separate fresh containers and only read the immutable package/expected fixture. Root/source/package read-only; `--network none`; CPU 1, memory 2 GiB, PID cap 64; cached image only. One host orchestration, no retry/tuning/seed replacement. The frozen upstream runner and loader bytes are executed in-memory after hash verification; read-only source files are mounted for provenance. The effective Python source bytes must match the upstream SHA-256 exactly.

**D — decisions.** `PASS_ROLE_SKILL_ROBUSTNESS_SCOPED` only if all 10 builders complete; all 30 role×seed accuracies are ≥0.90; both loaders reproduce all 12,288 predictions per seed exactly; artifact digest and read-only package immutability pass; graph A→B→C succeeds in two generations; stale generation and every malformed/invalid schema, version, edge, scope, duplicate and unverified control yields without invalid state mutation/emission; and the independent raw auditor reports zero errors. Any competence, reload or graph miss is FAIL. Provenance/runtime/audit ambiguity is HOLD or typed STOP. No model is promoted.

**C — controls.** Only the ten fresh training seeds vary. All other #3890 source, model, generator, optimizer, steps, role data sizes, package format, loader math, graph and thresholds remain fixed. No network/provider, GUI/input, user data, real effects, runtime authority, image pull, Docker cleanup or model promotion.

**U — limits.** One synthetic hand-authored three-role family and one local Docker image/host. This does not establish Astra-supervised transfer, online-learning quality, concurrent runtime behavior, adversarial artifact authenticity/security, production safety, application effects or release readiness. SHA-256 proves integrity, not authenticity.

## Provenance note

The #4479 branch never trained. Its contract proposed seeds 100000..100900, while its immutable FREEZE/formal source encodes 3792..4692 and omits required env bindings. #4529 correctly prohibited executing either schedule. This allocation uses a new range and is not a retry or a reinterpretation of #4479.

