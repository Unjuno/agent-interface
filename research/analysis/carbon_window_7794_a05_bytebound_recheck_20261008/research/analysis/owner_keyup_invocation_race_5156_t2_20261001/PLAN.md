# #5156 T2 — independent-process exclusive-claim test

## H / T / D / C / U

- **H:** On this Windows local NTFS volume, two independently spawned Python
  processes can both pass an ordinary “no marker exists” check and perform a
  one-shot dispatch; replacing that check with `O_CREAT | O_EXCL` on a shared
  allocation claim will admit exactly one process.
- **T:** A frozen host-only runner launches two fresh `spawn` processes per
  trial, synchronized after the precheck. It repeats 20 fresh-directory trials
  for the unclaimed baseline and 20 for the exclusive-claim arm. Each inert
  candidate records one unique receipt. The separate auditor recomputes counts
  from retained per-trial files and checks frozen source hashes.
- **D:** Baseline must admit 2/2 processes in every trial; the exclusive-claim
  arm must admit exactly 1/2 in every trial, yielding one claim and statuses
  `[0, 2]`. Any timeout, missing receipt, extra admission, or hash mismatch is
  a failure/STOP; no reruns or replacement trials.
- **C:** One Windows host, one local NTFS workspace, CPython `spawn`, synthetic
  inert callbacks. This tests cross-process file creation, not agent identity,
  multiple hosts, network filesystems, crash recovery, or the production
  launcher integration. The permanent claim deliberately fails closed after a
  crash; availability cost is not measured.
- **U:** No Docker, X11, GUI, model, network, game, or formal input is used.
  This does not establish key-up, occupancy, MAP01 efficacy, reliability, or
  product behavior. It is a distinct host experiment extending the prior
  same-process thread test to independent OS processes.

## Execution order

Run the construction unit suite first. Freeze source/test hashes and the
execution environment, then invoke `run_mp_experiment.py` once. Only if it exits
0, invoke the separate raw-only auditor once. Preserve all outputs; no retry.

