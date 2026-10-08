# A01 — runner setup STOP

**Disposition: STOP before candidate source execution.** The frozen command specified a candidate output directory, but the invocation passed the existing `/out` bind-mount root. The candidate refused with `output exists; refusing to overwrite first outcome` and exit 1 before Xvfb startup. No candidate raw was produced and no key or X server was touched.

`results/RUNNER_STOP.json` records the exact invocation arguments, frozen-command mismatch, observed error, and classification. This setup failure is retained; it is not a scientific result. A02 is a separately versioned construction successor with a fresh output subdirectory.
