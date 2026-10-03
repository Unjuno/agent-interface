# App-server EOF evidence rescue — 2026-10-03

This note records the disposition of the research material from PR #6953.

- The 161 research-side paths from `research/appserver-eof-stop-59-01a0ff51-20261003` are preserved here in `main`, including the finite baseline/candidate captures, audit receipts, source pins, the research client change, its regression test, and the live-control index entry.
- The material documents app-server stdout-EOF handling for the scoped inert-child experiment. It does not establish a global deadline, downstream/product behavior, model/provider behavior, GUI/input behavior, or a general host guarantee.
- Original and repaired evidence remain side by side. No formal allocation or promotion claim is made by this rescue.
- `runtime/integration_checks/native.py` was intentionally excluded. Its CI-suite registration change needs a separate current-`main` review and is not part of this evidence-only rescue.
- The source branch is retained for the implementation follow-up; deleting it is safe only after the research package and this disposition remain verifiably present in `main`.
