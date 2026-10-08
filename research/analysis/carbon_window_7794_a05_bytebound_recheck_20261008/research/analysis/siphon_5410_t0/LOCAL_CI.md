# T0 local validation

- Candidate and independent-auditor syntax were checked before preregistration with `python3 -m py_compile`; all three frozen scripts parsed/executed in the container context.
- Formal candidate: one Docker run; exit 0 and raw output retained.
- Independent raw trace audit: returned FAIL on the preregistered lease-expiry liveness gate; resource ownership/release checks had no errors.
- Four corruption controls: 4/4 rejected, each with a mutation-specific mismatch.
- `python3 research/analysis/check_index.py --write` then `python3 research/analysis/check_index.py` — PASS; 213 retained result/failure directories indexed.
- `python3 .github/check_public_navigation.py` — PASS (26 documents, 922 repository-relative links).
- Local Research Workspace Index is sparse-checkout-limited; hosted full-checkout workflow will verify.
- This is an intentional formal scientific failure, not a CI or infrastructure failure. Do not rerun the candidate to turn it green.
