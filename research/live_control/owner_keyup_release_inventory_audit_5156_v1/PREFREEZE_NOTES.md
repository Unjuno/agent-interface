# Prefreeze notes

An initial exploratory runner failed because it referenced the fake display before the mocked constructor created it. The reference was corrected and the exploratory run passed, but all such runs predate the freeze and are non-confirmatory. The independent auditor had edge cases identified during prefreeze review and must be hardened before freezing.
