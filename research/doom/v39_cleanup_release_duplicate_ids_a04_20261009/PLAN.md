# A02 plan

Issue #8681 follow-up to the retained A01 `FAIL_METHOD`: after adding duplicate
identity rejection to cleanup receipt reconstruction, run one stdlib-only
synthetic candidate and one independent raw-only audit against the exact source
hash frozen in `FREEZE.json`.

Controls: one valid accepted/terminal pair; one legacy tokenless terminal; one
mismatched release token; and two distinct accepted/terminal identities.
Ambiguity probes: duplicate acceptance IDs with only one terminal, and
conflicting duplicate terminal rows in both orders.

PASS requires all four controls to preserve their intended results and all
three ambiguity probes to report incomplete terminals and no verified-empty
release. No game, model, GUI, runtime process, OS input, or physical release is
invoked. This test cannot establish that duplicate event IDs occur in
production or that physical input was released.
