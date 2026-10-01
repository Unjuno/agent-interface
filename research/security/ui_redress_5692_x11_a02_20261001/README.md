# Issue #5692 A02

Finite X11 fixture study of whether screenshot-visible pixels and the actual input recipient can diverge under a transparent, input-receiving overlay. This fresh allocation follows A01's terminal technical STOP; it does not edit or reuse A01's frozen source.

See PLAN.md for the preregistered H/T/D/C/U and one-shot decision rules. candidate.py runs the target/overlay fixture and retains raw crop bytes plus independent process event logs. independent_audit.py independently replays the raw JSON without importing the candidate. The standard-library test suite is construction-only.

The experiment runs host-locally in Ubuntu WSL2 under a private xvfb-run display. Docker Desktop/OrbStack is not used: Issue #5085 still records four nonterminal Created containers with unresolved ownership/release, so A02 requests no shared lane and performs no container operation. This cannot establish runtime integration, compositor behavior, platform-general effects, adversarial prevalence, or production security.
