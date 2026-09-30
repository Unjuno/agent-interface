# Issue #5126 strict-lineage finite contract result

**Disposition: `PASS_STRICT_LINEAGE_FINITE_CONTRACT` (synthetic host-only).**

## H / T / D / C / U

**H.** A finite contract can reject whitespace/non-string lineage IDs and
missing/duplicate source-event references while retaining a valid synthetic
positive and preserving non-authoritative state feedback.

**T.** One fixed 13-case corpus was classified by the candidate and a
structurally separate oracle; a raw-only auditor independently reconstructed
physical and effect eligibility from raw rows. Seven focused unittest methods
include blank/non-string/canonicality mutations, duplicate source identities,
and a corrupted raw-lineage sensitivity check. Python standard library only;
no GUI, model, input, network, GPU, or container.

**D.** Candidate/oracle mismatches **0/13**; frozen expected-gate mismatches
**0/13**; raw-only corpus audit errors **0**; corrupted raw record detected by
the auditor; focused tests **7/7**. Authority flags stayed false. The raw-only
auditor does not import candidate or oracle.

Formal corpus SHA-256:
`536de27a25cdc7b9936235dc1ef900cf174f2acbf16239a696474ede5f69fa9f`.
Audit SHA-256:
`40a1ec9b417505857ff24ad35c6e761024cf4d8a917186a0a64d1fcff7756d26`.

Commands (repository root):

```sh
python3 -m unittest discover -s research/doom/map01_task_effect_contract_5126_v1 -p 'test_*.py' -v
python3 research/doom/map01_task_effect_contract_5126_v1/run.py
python3 research/doom/map01_task_effect_contract_5126_v1/audit.py
```

**C.** This is a synthetic finite serialization/lineage check on host CPU,
not container evidence or a formal live allocation. The valid positive uses
source-event IDs constructed for the synthetic corpus.

**U.** It establishes no production schema availability or live unique-ID
attestation, event causality, actual input, task efficacy, MAP01 outcome,
model usage, efficiency, or product readiness. The prior v1 whitespace defect
is recorded additively in its `CORRECTION.md`; all v1 source, freeze, and result
bytes remain unchanged. Do not promote this result into runtime acceptance.
