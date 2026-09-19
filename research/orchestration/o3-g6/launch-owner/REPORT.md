# O3 G6 one-shot formal allocation launch ownership guard v1

## Purpose

The prior duplicate-active detector can identify a coordination failure, but a one-shot formal allocation needs a stronger rule: exactly one GitHub Actions run must own the right to enter the formal step, and later runs must fail closed even after the owner has completed.

This candidate is intentionally **not wired into the live workflow** because changing the existing workflow file would itself satisfy its push-path trigger and could create another formal execution. This commit only retains the ownership algorithm and tests.

## Rule

For an explicit `(workflow_path, head_sha, allocation_id)` scope, deduplicate by run ID and rank matching runs by GitHub `run_number`, then run ID as a deterministic tiebreak. The earliest matching run is the canonical launch owner.

- canonical owner: may enter the formal step;
- later matching run: must stop;
- completed canonical owner still blocks a later run;
- current run missing from the API view: fail closed;
- malformed matching run: fail closed;
- another workflow or head SHA: ignored.

This is launch ownership only. It does not transfer experiment authority, validate the experiment, cancel an existing job, or decide which scientific result should be accepted after a historical duplicate has already happened.

## H / T / D / C / U

**H** — deterministic earliest-run ownership prevents a second run for the same frozen workflow/head from becoming a legitimate one-shot allocation, including after the first run has completed.

**T** — ten network-independent unit cases plus the two retained live-02 run records. Benchmark a 100,002-row synthetic run list over 30 iterations. No model, GUI, ViZDoom, OS input, workflow edit, or formal allocation.

**D** — PASS mechanics requires 10/10 tests; historical run number 1 must be owner and run number 2 must be rejected. Any missing-current or malformed matching case must fail closed.

**C** — GitHub API visibility may be eventually consistent. A launcher integration should combine this ownership check with serialization/concurrency so both concurrent jobs do not pass before seeing each other. This candidate alone is not a proof against every API race.

**U** — `run_number` is GitHub workflow metadata and is treated as the ordering key; cross-workflow ordering is irrelevant because workflow path is part of scope. No end-to-end launch-race probability is measured.

## Results

- Unit tests: **10/10 PASS**.
- Historical live-02 run `34968759795` / run number 1: `PASS_CANONICAL_OWNER`.
- Historical live-02 run `34968781910` / run number 2: `FAIL_NOT_CANONICAL_OWNER`.
- Synthetic 100,002-row scan, Python 3.13.5/Linux x86_64, 30 iterations: median **5.690 ms**, min **4.677 ms**, max **9.882 ms**.

The timing is local scanner overhead only.

## Integration constraint

A safe future workflow should use a **new allocation ID** and a launch protocol that serializes contenders before this check (for example, a non-cancelling concurrency group plus ownership verification). The currently consumed `map01-measurement-integration-live-02` must never be reused to test this guard.
