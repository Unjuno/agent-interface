# #3851 matched-seed rank-4 minibatch RNG comparison

Status: prepared, frozen runner/auditor under construction; formal CUDA run not yet invoked.

This successor compares the original #3807 five seeds under two rank-4 online adapter RNG streams. It preserves the original data/base/support generation and support row order (`seed+30`); the only intended intervention is minibatch-index RNG (`seed+35` legacy vs `seed+31` shared). Each arm starts from a copied identical adapter state and runs 16 arrivals × 8 updates. The formal host is the local RTX 3080 Laptop GPU, not Docker/CI.

Before formal execution, rerun only static/unit construction checks (no optimizer steps), freeze tests and hashes, and record all source hashes on Issue #3851. Formal allocation is one invocation with zero retries. Raw run output is to be retained additively here; independent audit must pass before creating a PR.

The immutable allocation, H/T/D/C/U and decision gates are at https://github.com/Unjuno/agent-interface/issues/3851.
