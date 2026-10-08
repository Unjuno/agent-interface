# Follow-up 01 — text-mode full-pipe baseline

## Purpose

The original `baseline-run-02` is retained unchanged. Its receipt shows `finish_send` failed with `TypeError`, because its child stdin was opened in binary mode while the frozen helper writes a Python string. The original `PASS_BASELINE_BLOCK_CONFIRMED` audit is therefore a false pass for the synchronous-write hypothesis.

This follow-up is a separate allocation. It changes only the probe's child stdin to text mode, keeps the same byte-pinned historical helper and pipe-fill/barrier/owned-child cleanup protocol, and executes exactly once. It does not overwrite or reinterpret the original artifacts.

## H / T / D / C / U

**H:** With text-mode stdin, the frozen synchronous `finish` write blocks on a full pipe while the child ignores stdin; at the 0.5-second barrier the child remains alive and planner close has not run. Killing only the owned child should release the blocked write with a broken-pipe error and let cleanup finish.

**T:** Verify the frozen helper/probe/runner/auditor hashes, then run `probe.py` once in cached WSLc with networking disabled and the retained image. Capture argv, stdout, stderr, exit status, final probe result, and the controller-failure receipt.

**D:** Pass only if the pipe accepted bytes; the worker remains alive, child alive, and planner open at 0.5 s; the finish stage ends as `BrokenPipeError` after the explicit probe kill (not `TypeError`); the original exception is preserved; and the worker/planner retire afterward. Any mismatch is `FAIL`; execution or infrastructure failure is `HOLD`.

**C:** One deterministic local Python child and one filled stdin pipe. No game, model, GUI, physical input, shared service, or runtime allocation.

**U:** This establishes only the constructed pipe-write boundary for the pinned helper. It does not establish physical input release, process-family cleanup, scorer completion, or a universal deadline.

## Frozen repair-runner contract

The historical repair runner captured child exit codes but always returned zero, masking failed red/green phases. This follow-up adds a checked wrapper whose expected subprocess code is `1` for the intentionally failing red control and `0` for the green repair. A standard-library contract test checks the mapping and rejects unknown phases. The wrapper is not used to reinterpret or overwrite the original frozen repair outputs.
