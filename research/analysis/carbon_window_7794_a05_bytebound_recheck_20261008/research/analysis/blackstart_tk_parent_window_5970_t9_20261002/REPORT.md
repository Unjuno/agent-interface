# Issue #5970 T9 — immediate-parent observer

## Disposition

Independent audit: `HOLD_PARENT_SELECTED_EVENT_MISSING`. The immediate-parent observer selected XIDs 2097170, 2097169, and 2097171, including the X RECORD recipient. Tk logged the expected Shift press/release; the observer logged three events (an additional release at the press timestamp), and X RECORD retained five server-delivery copies. The predeclared exact two-row cross-stream agreement therefore failed; candidate/auditor did not upgrade this to PASS. Cleanup release was attempted and the terminal keymap was neutral. Raw bytes and all event rows are retained.

This result supports only that a separate observer selecting the immediate parent receives at least the corresponding press/release classes in this one private-Xvfb run. It does not explain the extra Release or five RECORD deliveries (likely per-client delivery multiplicity is not assumed as fact), nor establish deployed #4135 behavior, generalized provenance, recovery, or task benefit. Docker Desktop remained unavailable; WSL2/Xvfb fallback. No formal allocation rerun.
