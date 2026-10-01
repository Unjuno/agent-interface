# O3 G6 duplicate formal-allocation launch guard v1

## Scope

This is a coordination/reproducibility result, not a MAP01 efficacy result. The immutable code/evidence base is `810479785d1adb7e785962d3e16d6b1e4bd29f79`.

At the GitHub API snapshot used for this result, two distinct GitHub Actions run IDs were simultaneously `in_progress` for the same workflow path and the same head SHA:

- `34968759795`, run number 1
- `34968781910`, run number 2

Both were for `.github/workflows/map01-measurement-integration-live-02.yml` at `810479785d1adb7e785962d3e16d6b1e4bd29f79`. Each job had reached dependency installation and had not yet reached the one-shot MAP01 allocation step when inspected. This result does **not** infer why the duplicate launch happened and does not claim either run should be cancelled after the fact.

## H / T / D / C / U

**H** — A narrow launch guard keyed by explicit workflow path plus immutable head SHA can detect concurrent duplicate executions of one frozen allocation without confusing historical completed runs, another workflow, another commit, or duplicated API rows with a live conflict.

**T** — Run eight deterministic unit cases in a network-independent container, then evaluate the retained two-run GitHub API field snapshot. Separately scan a 100,002-run synthetic payload for implementation overhead. No model, GUI, ViZDoom, OS input, formal allocation, or existing result tree is modified.

**D** — PASS for detection mechanics requires all eight unit cases to pass and the current two-active-run snapshot to return `FAIL_DUPLICATE_ACTIVE`. FAIL if same-run API duplication is misclassified, different workflow/SHA is conflated, or two active matching run IDs are missed. The observed repository condition itself is a retained **failure condition**, not converted into a success result.

**C** — The two runs may have been intentionally or accidentally launched by separate ref-update/push events; a later completed/cancelled state may remove the live conflict. Those possibilities do not change the snapshot claim that two distinct matching run IDs were concurrently active.

**U** — The snapshot contains selected GitHub Actions metadata fields rather than an exported full API response. GitHub-side event provenance that explains why two runs were created is not established here. Container timing is environment-specific and is not an end-to-end GitHub latency benchmark.

## Results

- Unit tests: **8/8 PASS**.
- Observed snapshot classification: **FAIL_DUPLICATE_ACTIVE**.
- Matching active run count: **2**.
- `safe_to_launch_another`: **false**.
- Synthetic scan: 100,002 rows, 30 iterations, Python 3.13.5 on Linux x86_64.
- Synthetic scan median: **11.182 ms**; min **10.090 ms**; max **12.519 ms**.

The timing only characterizes the local linear scanner. It is not evidence that GitHub launch prevention itself has this latency.

## Disposition

**RETAIN FAILURE + RETAIN GUARD CANDIDATE.**

The current duplicate launch observation should remain visible even if both runs later complete successfully. A successful experiment outcome would not erase the coordination failure mode.

The guard is intentionally not wired into the currently running workflow because modifying or restarting an in-flight formal allocation would contaminate the retained first outcome. A later separately reviewed launcher/workflow revision can use the detector or native GitHub Actions `concurrency` semantics, but must preserve explicit allocation identity and must not cancel a legitimate already-running allocation silently.

## Files

- `duplicate_formal_allocation_guard_v1.py` — field-level detector.
- `test_duplicate_formal_allocation_guard_v1.py` — eight deterministic cases.
- `observed-runs.json` — selected immutable fields from the GitHub API snapshot.
- `observed-result.json` — detector output for that snapshot.
- `benchmark.json` — container scanner timing conditions/result.
