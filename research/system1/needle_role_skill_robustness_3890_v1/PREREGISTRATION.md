# Issue #4479 — cross-seed robustness of reloadable role-skill graphs

Allocation: `needle-role-skill-robustness-3890-v1`  
Branch: `research/needle-role-skill-robustness-3890-20260926`  
Additive path: `research/system1/needle_role_skill_robustness_3890_v1/`  
Base main: `5dd2b9b18fc5f3e73e8ff9adf808806a49a121ce`

## H / T / D / C / U

**H.** The role-specific LoRA graph exported as an inert JSON skill remains competent and exactly reloadable across fresh training seeds; the narrow seed-3789/C score of 0.900635 in #3890 is not representative.

**T.** Ten fresh seeds: 3792, 3892, 3992, 4092, 4192, 4292, 4392, 4492, 4592, 4692. The 100 spacing prevents overlap among the fixed seed+1..seed+12 data/update substreams. Keep #3890's three-role synthetic family; 8→16→4 core; rank-2 output LoRA; A base pretraining 512 rows/400 AdamW steps; separate B/C adaptation 16 rows/120 steps; 4,096 held-out rows per role; data-only JSON package; two fresh loader containers; A→B→C receipt lifecycle. Provenance and exact parameters are inherited from the merged #3890 source and independently pinned here. No architecture, optimizer, support size, training schedule, evaluator, threshold, or graph changes.

For each seed, both loaders must match builder predictions for all 12,288 rows, with loader-reported artifact SHA matching the exact raw package; audit independently recomputes logits from package tensors and retained inputs. Verify package bytes before/after both loaders. Exercise generation-current graph replay and stale receipt rejection, plus all existing negative controls. Every refusal must preserve cursor/package and fixture emission count.

No fitting during construction. Freeze issue contract/hash, source/tests/auditor hashes, cached image digest, schedule, Docker commands, and output transport before a single formal orchestration. Ten seeds, no retries, tuning, exclusions, or replacement seeds.

**D.** PASS only if every one of 30 seed×role accuracy cells is ≥0.90; both loaders exactly match independent reconstruction across all 12,288 rows per seed; the package digest is bound at each load and bytes remain unchanged; valid graph transitions and all negative controls pass; and audit errors are zero. Any competence or lifecycle miss is FAIL; provenance/audit ambiguity is HOLD; unavailable cached environment or capture is typed STOP.

**C.** Cached `needle-pilot05:local`, exact image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64, CPU only, 1 CPU/2 GiB/64 pids/64 MiB tmpfs per container, network none, read-only source/root/package, separate writable evidence directories. No model API, GUI/input, real effect, authority, image pull, daemon repair, or cleanup.

**U.** Ten seeds still cover one hand-authored synthetic family and fixture oracle only. No real Astra teaching, general skill transfer, hostile artifact authenticity/security, cross-device portability, concurrent adaptation/inference, production latency, marketplace behavior, real application effect, or execution authority. SHA-256 is an integrity digest, not a signature.

The exact public Issue body is retained in `ISSUE_CONTRACT.md`; its raw UTF-8 SHA-256 is pinned in `FREEZE.json`.

