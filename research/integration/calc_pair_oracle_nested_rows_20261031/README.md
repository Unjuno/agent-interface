# Calc two-cell scorer: nested-row false acceptance

A05/A04 exploratory scoring used the archived `calc_pair_fods_oracle_20261031` scorer. Its direct-child row traversal silently ignores rows inside ODF row groups or header-row containers. A synthetic document containing the correct two direct rows plus a grouped extra cell 999 was incorrectly scored as passing. This is a scorer defect, not evidence that the retained A04 file contains such an extra cell.

This successor preserves all historical raw files and fails closed with `pass_effect: None` when a row is nested under the sheet. It deliberately does not claim full ODF structure support; unknown is not success. The regression test was observed failing before the change. Seven tests pass in normal and optimized Python. Rescoring the retained A04 FODS yields true; A05's blank saved FODS yields false. The retained independent A04 XML audit is separate evidence. No GUI, provider, latency, or broad ODF qualification is implied.

Run: `python -m unittest discover -s research/integration/calc_pair_oracle_nested_rows_20261031 -p test_pair_saved_oracle.py` (also with `python -O`).
