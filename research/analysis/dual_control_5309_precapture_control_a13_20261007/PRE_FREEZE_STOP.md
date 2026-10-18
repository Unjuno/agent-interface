# A13 pre-freeze execution STOP

- Issue: [#5309](https://github.com/Unjuno/agent-interface/issues/5309)
- Allocation: `5309-PRECAPTURE-CONTROL-A13-20261007`
- Status: `STOP_PREFREEZE_CANDIDATE_EXECUTED`
- Base checkout: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2` (`origin/main` at checkout)
- Container smoke available: pinned Node 26.10.0 Alpine image; this does **not** mean A13 ran in a container.

## H/T/D/C/U (planned; no scientific disposition)

- **H:** A witness-preservation constraint improves independently verified task completion only when an action would destroy the sole source-bound effect witness. It should add no benefit when a valid independent readback exists, should not treat state-perturbing capture as evidence, and should yield before information collection on urgent stop.
- **T:** Planned paired finite actions with identical admissibility, utility, cost and predicted information gain; controls for sole-witness loss, independent readback, perturbing capture, prior receipt and urgent stop. Candidate/environment/auditor were intended to run in separate isolated containers, with oracle truth excluded from candidate.
- **D:** The intended gate required exact independent reconstruction, an advantage only in the sole-witness-loss stratum, no gain in the independent-readback control, no credit from perturbing capture, no action after urgent stop/prior receipt, and zero authority.
- **C:** Authored finite transitions can encode the expected distinction; no costs or observation channels are calibrated.
- **U:** No GUI, model, physical input, live authority, natural task, latency, user/product benefit, or safety claim.

## What happened

Before a freeze commit or checksum freeze existed, the candidate was invoked once on the host using public candidate cases:

```sh
node candidate.mjs candidate_cases.json /tmp/a13_choices.json
```

The command wrote the retained choice JSON reproduced byte-for-byte in `pre_freeze_candidate_raw.json`; its SHA-256 is `d9edb4d44a9232ff77bc5702df5e5332a0aef7313292816e1dba1b2ac28b5a59`. The combined shell call did not capture the candidate's individual exit status, so it is **unknown**, not inferred from later commands. Candidate-specific stdout/stderr were not separately captured. The host Node version observed afterward was v26.7.0; the command was not run in the separately-smoked Node 26.10.0 container.

The separate container availability smoke was:

```sh
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m --cpus 1 --memory 256m --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges node:26-alpine node --version
```

It returned `v26.10.0` using image ID/repo digest `sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`. This was only a runtime smoke; no A13 source was mounted or executed in that container.

Formal-stage counts: candidate invoked 1 (pre-freeze, host, invalid for the planned experiment); environment 0; auditor 0. No hidden oracle was mounted or passed to the candidate, and no effect environment was run. The output is a candidate-choice artifact only—not a PASS, FAIL, effect, or scientific result. No retry or post-freeze rerun is authorized for this allocation. Any successor must use a distinct allocation and an independently frozen source/input/gate before its first candidate invocation.

Construction/syntax checks also ran in the same shell call and printed `construction assertions: PASS (8)`; this is construction evidence only. They cannot rehabilitate the pre-freeze invocation. Full command outputs and exit statuses were not individually recorded, which is an additional logging limitation.
