# Local CI — Issue #5404 T0

Executed after the formal raw and independent audit were immutable. No simulator or auditor rerun was part of these checks.

- `python research/analysis/check_index.py --write`: PASS; generated index refreshed to 206 retained result/failure directories.
- `python research/analysis/check_index.py`: PASS; 206 indexed.
- `python .github/check_public_navigation.py`: PASS; 26 documents, 902 repository-relative links.
- `python -m py_compile research/analysis/typed_resumption_packet_5404_t0_v1/experiment.py research/analysis/typed_resumption_packet_5404_t0_v1/audit.py`: PASS.
- `git diff --cached --check`: PASS.
- `python research/check_workspace_index.py`: cannot pass in this sparse checkout; numerous pre-existing top-level research paths are intentionally not hydrated. Full-checkout hosted CI remains required for this gate.
