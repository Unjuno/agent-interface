# Additive T1 audit correction (v2)

The original [verify.py](verify.py) result remains immutable. Its earlier report asserted that no row was silently dropped, but the script had no frozen expected cohort size. Deleting a row could therefore pass validation and change the denominator. The original `METHOD_CONSTRUCTION_PASS_SCOPED` label is narrowed: it covered the two arithmetic examples and two controls only; it did **not** establish denominator integrity.

The corrected, separately retained [verify_v2.py](verify_v2.py) requires `expected_n=10` and rejects four mutations: missing row, duplicate launch ID, unknown terminal type, and negative event clock. It independently computes incidence by per-row risk sets and by grouped event-table mass flow. Both agree on the complete cohort at t2 (2/5) and the censored cohort at t3 (3/8); intentionally wrong success-only KM values are 1/2 in both examples.

Execution: `python work/issue5593_competing_events_t1_v2.py` on the host with CPython 3.12.10; exit 0. Local source SHA-256 `8a1f4a133d7e950ddd838bc13a8ff3f164db63f949b193c0069649d6309b2c8c`. Raw stdout:

```text
{'complete_incidence_t2': '2/5', 'complete_wrong_KM_t2': '1/2', 'censored_incidence_t3': '3/8', 'censored_wrong_KM_t3': '1/2', 'corruptions_rejected': ['missing_row', 'duplicate_id', 'unknown_event', 'invalid_clock']}
```

Independent hand check: after two administrative censors, the t2 risk set is 8 and two stops leave survival mass 6/8; at t3, three of six remaining episodes succeed, so cumulative success incidence is (6/8)(3/6)=3/8. If those stops are wrongly censored, the success-only KM view yields 3/6=1/2. In the complete cohort, direct success fraction is 4/10=2/5, while censoring its two stops gives 4/8=1/2.

This is still a host-only synthetic construction check. No shared Docker lease, real agent episode, independently justified censor mechanism, empirical estimate, or production result is claimed. No earlier Issue result or raw input was altered. Same-time censor/event ties and nonterminal recovery are outside these controls.
