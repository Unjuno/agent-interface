# Post-run environment qualification

The frozen `FREEZE.json` captured Python 3.12.13 from `python`, which was used for construction tests. The formal commands were recorded from `python3 --version` and actually ran under Python 3.14.5 on Darwin 27.0.0 arm64. The protocol named `python3` but did not pin its resolved interpreter version, and the freeze metadata therefore does not match the formal runtime.

This mismatch is discovered after the one candidate and one auditor invocation and cannot be repaired retroactively. It is preserved as an additional reason to withhold method promotion. No formal command is rerun and no threshold or outcome is changed. Any successor must freeze the resolved interpreter path and version before execution.
