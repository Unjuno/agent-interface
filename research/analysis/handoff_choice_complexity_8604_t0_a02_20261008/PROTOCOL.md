# Issue #8604 T0 A02 — fresh synthetic card/key audit

Successor to A01 `STOP_CANDIDATE_OUTPUT_CONTRACT`. A01 remains immutable; this fresh allocation specifically tests the end-to-end CLI/file-custody and independent card/key audit contract. It does not test human behavior.

## H / T / D / C / U

**H.** For the frozen finite input specification, the candidate CLI will create one complete matched card per family/condition with exactly 2/3/4 dispositions, while preserving family facts and no-dispatch semantics; an independently implemented auditor will reconstruct every card and factual key and reject frozen semantic mutations.

**T.** Host CPython standard library, offline CPU. Eight synthetic families × C2/C3/C4 = 24 cards; five factual/authority/scope questions per card = 120 keys. The mandatory Stop safely disposition is present in every condition. Construction tests invoke real candidate subprocesses with temporary input/output paths, verify JSON stdout and requested file, assert exclusive-create refusal on a second write, and test the independent oracle plus mutations. After freeze, invoke candidate once and auditor once on `spec.json`; preserve raw files, stdout, status and hashes. No participants, human data, GUI, model, network, action dispatch, Docker or WSLc.

**D.** `PASS_METHOD_SCOPED` only if both frozen CLIs create the required files exactly once, candidate and auditor return success, all 24 cards / 120 keys reconstruct exactly, and all declared semantic mutations are rejected. Candidate output/custody failure is `STOP`; independent audit mismatch is `HOLD_AUDIT`; semantic/key failure is `FAIL_METHOD`. Any failure is retained without rerun.

**C.** The fixed oracle may share the protocol's conceptual assumptions; eight authored families do not establish stimulus realism or exhaustive handoff semantics. A content-valid card does not show that readers understand it. Keeping Stop present means option-count effects are not the full space of menu designs.

**U.** Even a method PASS is only finite synthetic artifact/key evidence. No inference about choice latency, Hick–Hyman transfer, option overload, human comprehension, usability, agency, runtime, safety, or product behavior. No participant study is authorized; any such study requires separate review and explicit approval.

## Allocation custody

Fresh branch and path; no reuse of A01 formal outputs. Construction tests precede freeze. Formal command outputs are exclusive-create and are never overwritten. Hash manifests separate freeze inputs/sources from mutable one-shot outcome artifacts.
