# Public X11 release versus PNG persistence — Issue #6999

Successor to closed #810 under #17. Owner `01a0b98b-5ce3-7f53-82f3-e09294f24d57`.
The main research goal remains unfinished. This package adds a narrowly scoped
integration witness, not a production repair or whole-Issue completion claim.

## Frozen hypothesis and decision

- H: A release queued behind synchronous PNG persistence stays coupled to that
  persistence. A serialized cleanup-only thread can release the same owned input
  backend before the actual PNG write resumes.
- T: `PLAN.json` fixes 12 cells: 3 repeats × coupled/separate × healthy/blocked.
  Each gets a fresh private Xvfb and task-owned window. The unmodified public
  session executes focus → F8 down → observe/write PNG → release_all. A scoped
  `Path.open` wrapper pauses the actual exclusive PNG handle.write, not capture,
  an invented backend, or a replacement observation. Fault resume is request
  +400ms, checkpoint request +150ms. F8 autorepeat is disabled on the private
  server. Independent connections record physical keymap and app key events.
- D: All 12 exposures must complete with exactly one press/release, no additional
  press, neutral whole keymap/buttons, and verified public release. Healthy arms
  must finish before checkpoint. All 3 coupled fault cells must be down there
  and release after resume; all 3 separate fault cells must be up before
  checkpoint while writer/program remain pending. Otherwise the saved-only
  auditor retains HOLD or stops on invalid exposure; no outcome-based tuning.
- C: This is an intentionally paused persistence call. The thread wrapper and
  mutex are probe-owned instrumentation, not an exported cancellation API or
  committed production control plane. The mutex only serializes cleanup; it
  never spans PNG persistence. There is one backend/input owner, no concurrent
  new task input. A sleeping/Event wait releases the interpreter; CPU-bound
  callbacks, other locks, concurrent input and server failures differ.
- U: No hard deadline, general reliability, arbitrary X-server stall, natural
  disk latency, fsync durability, macOS/Windows/Wayland, host display, game,
  model, useful feedback, task/token efficiency or production integration claim.
  The 2s lease is an admission guard only and is deliberately not the fault.

## Roadmap and execution boundaries

1. Read current main/docs/open and closed Issues/PRs/branches; compare #810 and
   #17 transport/Condition owners. Abstract order/cutset analysis predicts the
   coupled path; real Xlib threading, XTEST, readback and application events are
   the empirical residual. No old evidence or production path is changed.
2. Test the saved oracle with hand-derived records (RED then GREEN), verify the
   exact main source snapshot and dependency imports without consuming a cell.
3. Freeze source/image/plan hashes, publish freeze witness, invoke candidate once
   and independent saved-only auditor only after candidate successful exit.
4. Local CI, saved-record negative controls and independent review; batch push
   and PR integration. Stop the owned VM after all named containers are terminal.

Run `python3 run_stage.py candidate`, then `python3 run_stage.py auditor` only
after the first succeeds. The driver refuses existing stage directories and
source drift. Never run candidate on this consumed allocation a second time.
Container: private OrbStack VM Docker daemon, immutable local arm64 image,
network none, read-only root/source, dropped capabilities/no-new-privileges,
1 CPU, 512MiB/no swap, 128 PIDs, 64MiB /tmp. The VM shares host hardware and
normal-mode filesystem integration; this is not kernel/security isolation.
`runs/*/receipt.json` retains creation flags, before/after inspection, first
command output, exit and ownership-bound timeout cleanup.

Physical sampling brackets release; the first confirmed-up time is not the
exact XTEST injection/acceptance instant. App receipt timestamps include receiver
scheduling and are not controller emission timestamps. Source GetImage has
already returned before the injected write; this does not exercise a blocked
Xlib reply or shared transport lock. Frozen source and original raw remain
unchanged even if later interpretation or packaging finds an issue.
