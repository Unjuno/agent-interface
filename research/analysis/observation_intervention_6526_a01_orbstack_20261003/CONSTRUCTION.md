# Construction log (not scientific observations)

Allocation `OBSERVATION-INTERVENTION-6526-A01-ORBSTACK-20261003-01` was run
once. Formal candidate=1, independent auditor=1. Its final classification is
`STOP_AUDIT_ERRORS`; no hypothesis result is reported.

## Construction results

- `CONSTRUCTION-01`: PASS. Image `sha256:a14e964ad615fa8315eec5f1e2539eb781f10647872c42e0cbe5b1400c15cb45`,
  linux/arm64, private OrbStack Docker Engine 29.1.3. With `docker run --init`
  and `--network=none --cpus=1 --memory=512m`, Tk 8.6.14 opened under Xvfb,
  `xwd` returned 5,246,059 bytes (receipt and digest retained next to this log).
- `CONSTRUCTION-02`: PASS, construction-only. One randomized block ran all six
  arm/schedule cells; independent raw check found 6 starts, 6 actions, 6
  deadline snapshots, 28 screenshot events and 51 sham ticks. All six
  effects and deadline snapshots exist. These rows are not formal data.
- Local package tests: 11/11 passed after mutation coverage was added for
  underfilled allocation, duplicate/reordered starts, mistimed action,
  missing actions/screenshots, stable-control failure and exact paired test.

The `--init` flag is required: without it, OrbStack's container PID 1 consumes
the Xvfb readiness signal expected by `xvfb-run`. Formal containers must use
`--init`; this is fixed in the candidate invocation and does not change trial
conditions.

## Retained setup failures

1. **WSLc predecessor (Oct 2, separate record):** Tk exited because `DISPLAY`
   was absent. This remains the historical environment STOP in
   `observation_intervention_6526_t0_20261002/`; it is not changed or retried.
2. **OrbStack isolated-VM install attempt:** container builds using APT could
   not resolve package mirrors when VM network isolation was enabled. Enabling
   networking on this dedicated VM fixed DNS for build-only package resolution;
   formal containers remain `--network=none`.
3. **VM-internal apt build:** Ubuntu/Debian package installation returned
   `Invalid cross-device link` from dpkg on this OrbStack engine. The same
   digest-pinned image was instead built on the host OrbStack Engine and
   transferred as a saved image archive to this private VM. Host/private VM
   image IDs were compared before smoke use.
4. **Image pipe transfer:** `docker image save | orb ... docker load` yielded
   an image whose commands were missing. Do not use that transfer form. The
   file-save → `orbctl push` → `docker image load -i` path now preserves the
   exact image ID.
5. **Xvfb smoke invocation 1:** executed the Tk smoke without its Xvfb wrapper;
   it exited 1 with `_tkinter.TclError: no display name and no $DISPLAY`. This
   is a bounded construction command error. Corrected command wraps the smoke
   in `xvfb-run -a`; the failed invocation produced no scientific row.
6. **Xvfb smoke invocation 2:** `xvfb-run` started Xvfb `:99` (PID 16 inside
   container `6ae7ee94ce3965f8af0746299c3f4c0bb46762166865453a72b1df1692e23945`)
   but remained waiting before launching Python because `xdpyinfo` from
   `x11-utils` was absent. Candidate=0, auditor=0, formal rows=0. This exact
   construction-only container was inspected and stopped; it is not a formal
   allocation outcome.
7. **Xvfb smoke invocation 3:** with `x11-utils` present, `xdpyinfo` and X
   authorization both work when run directly, but PID 1's `/bin/sh` is put
   into a signal-wait by `xvfb-run`; OrbStack's container init consumes the
   Xvfb readiness `SIGUSR1`, so the shell never reaches its command. Container
   `8feb787f745b530a6d9776f7d75aa02c308c93a25ae87638f54a621dbf0216f9` was
   stopped after confirming Xvfb alive and no child client. This is a runtime
   launch issue, not an observation or hypothesis result. Test the same image
   with Docker's `--init`; the next construction invocation passed (receipt
   retained under `results/construction/`).

## Construction gates

- `CONSTRUCTION-01`: run the Tk/xwd display smoke with `xvfb-run` in a
  network-disabled 1-CPU/512-MiB container and retain image ID, exit, JSON
  receipt, and cgroup values.
- `CONSTRUCTION-02`: run one separate randomized 6-trial (one block) fixture
  and independently audit all six records; do not pool these rows with A01.
- Remaining: freeze the 180-trial formal input, all source hashes, exact container
  invocation, and decision rule before candidate execution.
