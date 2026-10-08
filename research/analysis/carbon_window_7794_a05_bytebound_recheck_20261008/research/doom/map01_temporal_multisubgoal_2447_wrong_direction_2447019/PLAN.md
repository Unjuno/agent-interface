# Issue #2447 — wrong-direction construction allocation 2447019

## H/T/D/C/U

- **H:** Following an independently image-confirmed temporal phase completion, a fresh observation whose pixel flow confirms a deliberate wrong-direction turn must cause a fail-closed stop before any subsequent subgoal.
- **T:** One fresh ViZDoom MAP01 no-monster episode, seed 2447019, temporal gate, heading 110°. Proceed to the wrong-direction fault only when the temporal phase directly reports `DROP_COMPLETED` and requests no continuation. Inject one Left turn where Right is expected; independently audit eligible saved PNG pairs using frozen LK flow thresholds; stop before any third subgoal. One invocation only.
- **D:** PASS_WRONG_DIRECTION_FAIL_CLOSED_STOP requires independent phase reconstruction, >=80 valid visual tracks and median dx >=+20px on the faulted turn, fresh observation binding, ordered and empty-verified release, `STOP_WRONG_DIRECTION`, and zero third-subgoal path/action. Violation is FAIL. Setup/phase/vision ambiguity is STOP/HOLD, never retried.
- **C:** Exact predecessor runner sources from STOP allocation 2447018 are reused without edits except a separately versioned auditor whose allocation identity is 2447019. Image `agent-interface-map01-lab:2447-preflight-20260927`, image ID `sha256:b99a3444e7b2b05d159976d9ba60d9e90f212d47406c4b7aa7773e5042a28713`, linux/amd64, network none, read-only root/source mounts, `/tmp` writable tmpfs, fresh empty evidence volume. The launcher must not pre-create the case output path; the frozen runner creates it with `exist_ok=False`.
- **C:** Main risk is environmental/setup STOP; visual thresholds derive from retained 2447006 paired turn images, not fitted to this allocation. Hidden scorer yaw is not available to the direction stop decision.
- **U:** One construction episode only; no paired gate comparison, rates, multi-subgoal transfer, recovery, general safety, MAP01 completion, or Issue #2447 acceptance.

## Allocation identity

`issue2447-wrong-direction-construction-2447019`, seed 2447019. Distinct successor after 2447018 stopped before entering the case runner. No result is replaced or pooled. Formal rows 0; retries 0.

## Launch invariant

The runner, not the launcher, creates `/evidence/issue2447-wrong-direction-construction-2447019`. Preflight must prove this exact path is absent in the mounted evidence volume. Any mismatch stops before runner invocation.
