# Issue #7367 — closed workflow source contract A01

**Disposition: `PASS_CLOSED_WORKFLOW_CONTRACT_SCOPED`.** A declarative workflow manifest can serve as both the machine's executable transition/read plan and the source from which the future-use graph is derived. In this bounded prototype, liveness preserved every declared consumer, while dynamic reads, changed source, unknown edges, and undeclared dispatch failed closed. This does not prove coverage of future user intent or arbitrary model-visible conversation; the model rung remains HOLD pending independent review and an applicable task contract.

## H / T / D / C / U

**H.** When a restricted executor reads only fields declared by an immutable workflow manifest and can transition only along its declared edges, deriving liveness from that same manifest prevents hidden in-manifest consumers from being evicted. Unsupported dynamic access must retain all records as `UNKNOWN_KEEP`.

**T.** Run a finite manifest through a compiler, an interpreter that exposes only declared fields, and the unchanged A01 liveness function. Independently enumerate reachable manifest uses. Add a declared audit consumer, then test unsupported dynamic operations, unknown successors, source changes after compile, and undeclared dispatch.

**D.** Pass only if the baseline liveness set equals the independent reachable-use set, a declared consumer is both executed and retained, and each unsupported/tampered/undeclared case keeps every canonical record.

**C.** A model or user may still refer to facts outside the machine manifest. The prototype is sound only while the actual runtime routes all context reads and continuation choices through this restricted interpreter; it does not establish that an open-ended assistant interaction is covered by such a manifest.

**U.** Host-side Python 3.11.9 only; no production runtime, model, GUI, input, token, or task-effect test. One synthetic workflow is not evidence of general completeness or practical benefit.

## Result

The candidate and independent auditor passed **12/12** checks. The baseline manifest retained exactly the independent oracle's five live records and evicted four dead model-context records. Adding an `audit` node that reads `completed-note.terminal_receipt` caused liveness to retain that record, and the interpreter returned only the declared receipt field. An unsupported dynamic read, unknown successor, manifest change after compile, or undeclared `hidden_audit` transition returned `UNKNOWN_KEEP` with no eviction.

The source contract removes the self-asserted `graph_complete` bit for this closed machine-workflow subset: the graph is compiled from the exact manifest that the interpreter consumes. It does not certify that the manifest fully represents user intent, other processes, or unmediated model context. The prior completeness counterexample remains valid outside this restricted execution boundary.

## Reproduction and provenance

Run `python run_a01.py --out RAW.json`, then `python audit_a01.py RAW.json --out AUDIT.json`. Inputs and source hashes are listed in `SHA256SUMS.txt`. The only reused source is the frozen A01 candidate/workload from commit `0c4be66bcaac697f1019916e3d8ada889abd5ced`; current main's A01 candidate blob remains unchanged. This new host probe did not repeat the original A01 allocation.
