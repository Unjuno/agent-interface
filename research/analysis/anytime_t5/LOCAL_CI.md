# T5 local validation

- `python3 -m py_compile research/analysis/anytime_t5/*.py` — PASS.
- Containerized independent audit v2 and corruption controls — PASS; 4/4 mutations rejected.
- `python3 research/analysis/check_index.py --write` then `python3 research/analysis/check_index.py` — PASS; 211 retained result directories indexed.
- `python3 .github/check_public_navigation.py` — PASS after staging the new tracked target (26 documents, 912 repository-relative links).
- `python3 research/check_workspace_index.py` — NOT PASS in this sparse worktree: the checker sees only a subset of tracked top-level research directories, while README indexes also name omitted directories. This is a checkout-coverage limitation, not an experiment result; do not rewrite repository indexes to mask it. The hosted full-checkout workflow remains the authoritative check for this gate.

No app/runtime test suite is applicable to this exact-math research artifact.
