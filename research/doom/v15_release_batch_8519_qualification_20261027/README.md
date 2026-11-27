# V15 release-batch source qualification — PR #8519

The T5/T6/T7 packages are preserved as the exact 45 Git blobs from PR #8519 head `dd4d8baef726ca113d5c73f3f5ba5564c6ec0524`. Before preservation, T5's publication manifest verified 20 entries, T6's manifest 14, and T7's manifest 8. The normal/optimized stored results and first outcomes are unchanged; no candidate or auditor was rerun.

T6/T7 freeze backend blob `193c2bd231795e7ee57de64aedfd741c8b814013` at historical main `e627b8954ecfbdd90ccfe35a81441a00d88047c8`. At main `04d9b23abdbc97aed1f693feeeef49ce3814172d`, that backend blob is `f79ef249545594815963148185be4bf2bb418442`; the stored producer/adapter composition is not current-source validation. The related V39 composition's separate private custody and nine changed source blobs are documented in [#9661](https://github.com/Unjuno/agent-interface/pull/9661).

These records use synthetic owner/scorer/sink inputs. The incomplete-before-acceptance result remains HOLD; the stored-after-acceptance result is scoped to rows observed and explicitly does not establish causal attribution. They do not prove physical release, useful feedback, live GUI, task effect, recovery, WSLc or MAP01 success. Any reproduction must use fresh paths and not overwrite retained data or silently treat the historical freeze as a current allocation.
