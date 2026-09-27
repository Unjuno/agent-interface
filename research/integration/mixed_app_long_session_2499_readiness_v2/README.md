# Fail-closed readiness guard v2 for #2937

This successor addresses review findings from closed, unmerged PR #2944:
window IDs are strictly validated, malformed same-role candidates fail closed,
and operation admission requires current window and surface-generation evidence.
