# A01 first outcome — STOP before candidate process

Allocation A01 is preserved as an infrastructure STOP, not a scientific
candidate result. The Docker container started with the frozen command and
exited 2 after all three attempted writes to `/out` failed with `Permission
denied`. `docker inspect` showed OOM false, source mounted read-only, output
mount writable in Docker metadata. On the guest, output is owned by `taka:taka`
(UID/GID 1000), mode 0755. Container ran as UID 0 with all capabilities
dropped; without DAC override it could not write the owner-only directory.
The shell's failed redirection prevented `candidate.py` from starting.

No candidate raw output exists, so no independent audit was run. The first
outcome was not retried. This is an executor configuration defect, not support
for or against threshold-persistent topology. Exact stderr and diagnostics are
retained in `RUN.json`; the subsequent allocation A02 has a distinct output
path and changes only container UID to 1000:1000. It is separately frozen
before execution.
