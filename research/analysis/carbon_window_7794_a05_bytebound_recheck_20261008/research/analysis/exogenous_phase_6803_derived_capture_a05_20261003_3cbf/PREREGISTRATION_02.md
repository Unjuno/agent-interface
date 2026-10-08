# Prospective command-only allocation 02

Allocation: `PHASE-6803-A05-ORBSTACK-20261003-3CBF-02`.
This amendment supersedes only allocation/path/runner-control portions of the
original PREREGISTRATION.md. All H/T/D/C/U, scientific sources and gates remain.

Allocation 01 stopped during pre-stage Docker inventory with socket permission
denial. Candidate/probe/auditor starts were 0/0/0. Its full original sources are
preserved at Git commit `82100b79c845db3200d9637e070f6bde86db8832`, including
FREEZE.json; PREFLIGHT_01.md preserves diagnosis and disposition. No original
output/container directory was created. No identical retry is permitted.

Command delta: runner.py uses `orbctl run -m research-6183-t0-20261003 -u root`
solely for Docker administration/inspection/run. Guest file staging and transfers
remain ordinary user taka. Container UID/GID stays 501:501; network none, CPU 1,
512MiB, read-only root, capabilities ALL dropped and no-new-privileges unchanged.
No socket permissions, user groups, service configuration or image are modified.

Guest source/output prefix becomes `phase-6969-a05-3cbf-02`; local formal output
becomes `formal_02/`. FREEZE_02.json binds the revised runner, this amendment and
unchanged scientific files. Publish its source Git commit before the one-shot
formal candidate -> separate legacy diagnostic -> independent auditor sequence.
STAGING_02.json records exact read-only source custody and guest output ownership.
Any run-stage nonzero exit consumes allocation 02 and stops downstream launches.
