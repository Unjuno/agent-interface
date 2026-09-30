# Issue #5537 T4 — pairwise-compatible global-section obstruction

**Disposition: `PASS_SCOPED` (finite synthetic host experiment).** The parity-cycle bundle is pairwise compatible on every overlap but has zero global sections. The coherent equality control has two global sections, and the missing-context control remains `UNKNOWN`.

## H / T / D / C / U

- **H:** Pairwise compatibility does not imply a global section; gluing-aware admission should detect the higher-order obstruction and refuse irreversible admission.
- **T:** Three binary contexts over `x,y,z`: `x=y`, `y=z`, `z!=x`. Enumerate all eight assignments. Compare with `x=y`, `y=z`, `z=x` control and with the third context omitted. Candidate output is independently re-enumerated by a separate raw-only auditor.
- **D:** All frozen gates passed. Parity cycle: `pairwise_compatible=true`, zero global sections, `NO_GLOBAL_SECTION`, irreversible admission false. Equality control: two sections and `GLOBAL_SECTION_CERTIFIED`. Missing-context control: `UNKNOWN`, irreversible admission false. Auditor: zero discrepancies; 4/4 mutations rejected.
- **C:** Hand-authored finite binary relations, one three-context cover, and an exact finite domain. The pairwise-only comparator does not model other interface contracts.
- **U:** No general sheaf/cohomology solver, approximate tolerance, freshness, authority override, GUI, task effect, statistical performance, or production safety claim. T0–T3 Issue evidence is unchanged.

## Reproduction and provenance

- Current-main execution base: `da9b4b24999282f5168da969808827ad3ba6dbb0`.
- Source-freeze commit: `2fcd1a32b146f02e3ee7f5e8261caefbcfbe8eb5`; current-main plan refresh: `633cc7fb894dda5809ff4bb18035bd960e55e5c8`.
- Command (one invocation): `python3 research/analysis/gluing_parity_cycle_5537_t4_v1/experiment.py` — exit 0, 3 rows.
- Independent audit (one invocation): `python3 research/analysis/gluing_parity_cycle_5537_t4_v1/audit.py` — exit 0, `PASS_SCOPED`, errors `[]`, 4/4 mutation controls rejected.
- Runtime: host CPython 3.14.5. Container was not used: #5085 comment #5913845233 classifies the 2026-09-30 #5156 self-assigned slot as expired/unauthorized and permits only independent host-local work until a fresh assignment. No Docker daemon/image was inspected or used.
- Candidate SHA-256: `a474c96b2b950e91ac8e32a1246ca21bd5a31bb6f84e7263304d5360136f8a6f`.
- Auditor SHA-256: `b27bf3175dcc6eabd16abc07cd5bb3addb804c3095c8a76ae1f54972a4ba4a3b`.
- Raw JSONL SHA-256: `66eec513664ab11b4497aa7d0d0c58424f3790d604bdac835a0858c783f4bf44`.
- Audit JSON SHA-256: `c4b36cbc3cf7db4eca452812f1642647d94c07f882a53dace2b31e278bba243b`.

The container reproduction remains a separate future rung requiring a fresh exact allocation; this host result is not represented as container evidence.
