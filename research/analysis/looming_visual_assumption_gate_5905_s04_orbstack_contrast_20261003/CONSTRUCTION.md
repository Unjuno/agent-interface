# S04 construction and runner gates

S04 keeps the Image-only candidate implementation separate from its independently
written raw auditor. Construction checks build 36 rows and exercise candidate,
auditor, threshold-mask equality and five corruption challenges on a temporary
fixture. This host-side validation is not the formal result.

The dedicated OrbStack machine is
`research-6808-s04-contrast-20261003`, Ubuntu 24.04 arm64, created with
`--isolated --cpus 2 --memory 2G --disk 12G`. Its private Docker daemon is
`117a5cd8-e2f2-4469-b028-fbd0cf35be1a`. Docker Engine 29.1.3 reports cgroup v2;
the VM cgroup is `cpu.max=200000 100000`, `memory.max=2147483648`. A
pre-formal `--network=none --cpus=1 --memory=512m` infrastructure probe observed
`cpu.max=100000 100000`, `memory.max=536870912` from inside the container.
Thus requested VM and per-container CPU/memory limits were directly observed.

During the preflight review, the first generated bundle exposed family and
photometric labels in PGM filenames. It was never mounted into a container or
executed. The exact local bundle was preserved under
`preflight-label-leak-rejected/`, and the VM copy was renamed
`candidate_input_label_leak_rejected`; neither is a formal input. The fixture
builder now emits opaque filenames and shuffles public rows. Rebuild and check
all bundle hashes before freeze. This is a pre-invocation construction defect,
not a scientific outcome.

The exact local arm64 image is
`python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`.
It was pulled before freeze. The probe used `--rm`; private-daemon inventory
was empty afterward. No other VM/container was modified. The existing shared
OrbStack Docker daemon is not used for candidate/auditor execution.
