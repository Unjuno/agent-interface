# Reproduction and rerun policy — Issue #3711 downstream truncation

The formal result for allocation 02 is immutable evidence. Its result directory is already populated; **do not run the one-shot experiment into `formal-02/` again**. The historical container command in `formal-02/CONTAINER_RUN.md` records how that already-completed run was executed, but its output bind mount is not a safe rerun command.

## Reproduce from a fresh checkout

The experiment scripts are one-shot and verify frozen source hashes. To independently reproduce the method, first create a **new successor allocation** with a unique identity, preregister its H/T/D/C/U on [Issue #3711](https://github.com/Unjuno/agent-interface/issues/3711), freeze the new runner/auditor/source hashes, and use a new empty output directory outside the committed evidence tree. Do not reuse allocation 02's identity or overwrite any formal artifacts.

Example host-side setup (choose a genuinely new allocation name and verify the directory is empty before execution):

```sh
allocation=issue3711-downstream-truncation-successor-03
output="$(mktemp -d "${TMPDIR:-/tmp}/${allocation}.XXXXXX")"
test -z "$(find "$output" -mindepth 1 -print -quit)"
```

A new allocation must have its own frozen runner and auditor; do not invoke the allocation-02 scripts with this path because those scripts and their hashes are bound to the historical freeze. Adapt the runner and auditor container commands in [the formal-02 run record](formal-02/CONTAINER_RUN.md), replacing the output bind source with the new empty directory and mounting it at `/out`. Keep the frozen image, network, read-only source, resource, and platform constraints only if the successor preregistration specifies them. Save all new outputs under a distinct successor evidence path after the run and independent audit; preserve formal-02 byte-for-byte.

For allocation 02, the published files are for inspection and offline verification only: [report](formal-02/REPORT.md), [raw evidence](formal-02/raw.json), and [independent audit](formal-02/audit.json). The committed formal-02 directory is not a scratch/output directory.
