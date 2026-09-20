# Compact role-adapter graph — preregistration

Allocation: needle-role-graph-3779-compact-v1
Tracking Issue: #3780
Branch: research/needle-role-graph-3780-compact-20260921
Base: current main at branch creation
Candidate SHA-256: b9f92af480255b11febc607feb527827334ffa2ec26b1881b1c2166afd3cd5b8
Auditor SHA-256: 7c6c20f86471231b550a502f17a9190e7819698538b82762caf6e3f647dd9c67

## H/T/D/C/U

**H:** three separately learned role adapters composed in a receipt-gated A→B→C skill graph preserve each role's held-out proposal competence while stale, unknown, skipped, wrong-version, duplicate, unverified, and wrong-scope transitions fail closed.

**T:** Preserve the predecessor #3778 model, seed 3775, CPU deterministic PyTorch, base/adapter data sizes and steps, held-out data and thresholds exactly. Only result serialization changes: each (expected,predicted) two-bit label pair is packed losslessly into one nibble; two rows per byte. For each 4,096-row role retain 2,048 bytes of packed rows and SHA-256. Independent auditor decodes all pairs and recomputes exact row count, correct count, accuracy, and flat/graph identity. Preserve generation logs, 8 negative controls, stale-generation replay, adapter snapshots and base-immutability checks. Formal allocation once.

**D:** PASS only with exactly 4,096 reconstructable pairs per role, verified packed hashes, recomputed accuracy >=0.90 for A/B/C, identical flat/graph packed rows, valid A→B→C transitions in both generations, eight fail-closed controls without mutation, rejected old receipt in generation 2, exact B/C adapter state roundtrip, immutable base, and zero independent-audit errors. Missing/corrupt output is STOP; no retry.

**C:** Docker read-only check still reports unavailable Linux engine named pipe. Run locally on host CPU if it remains unavailable; never call this a container result. No restart/repair, image pull, disk cleanup, network task action, GUI/input, runtime authority, or local checkpoint files.

**U:** One synthetic family and seed, hand-authored graph and fixture receipts. No realistic transfer, true application effects, production authorization, concurrency, durable cross-process skill loading, or product-level claim. Construction-only packed-code roundtrip and source compile are not formal evidence.

## Preflight output bound

Each role serializes 2,048 packed bytes to 2,732 base64 characters (plus metadata); all three packed streams are ~8.2 KB before JSON compression. The complete raw evidence should fit well below the prior stdout limit. No model allocation is consumed by this sizing calculation.
