# Container T1 freeze — #59 rejected-action continuation contract

Allocation: `MAP01-REJECTED-ACTION-COVER-CONTINUATION-T1-20261001-01`.
Owner: local Codex task `01a0b98d-3cbf-7710-b1a4-28c16e0b49da` only.
Reserved CPU OrbStack window: 2026-10-01 11:20–11:30 UTC, queue request
[#5930107044](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5930107044).

This is a new container-execution rung for the already disclosed retrospective
T0 construction result. It does not upgrade T0 into preregistered or live
evidence. Candidate and auditor sources are frozen at source commit
`abae554279f4ddfdb3846e75a188e9c5455172e1`; candidate SHA-256
`8ea40182f653ef0cf113ce76ac147662a4d4e7ecac51b70d48b6ce56bdf8bcf7`, auditor
SHA-256 `0331dab1b0b66e04a89083aba5e5f6dc4a032acfec6ee68a59bf687ce6c5b594`.
The exact six test cases and expected outputs are in `candidate.py` and
`auditor.py`; source test file SHA-256 is
`2ffbe9ab6f47ebb6866e20583a868a4808f91274a497a3d620b79eaeedbb1418`.

## H/T/D/C/U

- **H:** The frozen finite candidate and separately implemented oracle produce
  the previously retained six outcomes in an isolated pinned container, while
  no input authority is emitted.
- **T:** Candidate runs once in
  `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
  (`linux/arm64`, already present); auditor runs once in a distinct container
  only after candidate exit 0. Network disabled, root filesystem read-only,
  source bind read-only, only the initially empty output directory writable,
  CPU 1, memory 512 MiB, pids 64, no capabilities, no retries.
- **D:** `PASS_METHOD_SCOPED_CONTAINER_REPRODUCTION` only if candidate exits 0,
  produces exactly six rows, auditor exits 0 with `PASS_METHOD_SCOPED`, and
  all no-authority/fail-closed controls match. Any failed start gate is
  `STOP_BEFORE_CANDIDATE`; any candidate or auditor failure is retained once
  and not retried.
- **C:** This validates one container/platform execution of deterministic
  contract arithmetic and audit separation only; it is not a policy executor.
- **U:** No enemy/threat, action semantics, live observation, input, GUI/game,
  model, timing-benefit, safety, survival, task-effect, or MAP01 outcome claim.

At slot start, refresh exact owner/thread, queue, main, branch/head, Docker
context/image, running-container list, and unique empty output directory. If
any gate differs or the daemon is unavailable, stop before candidate and
record the reason. Candidate and auditor receipts (CID, stdout, stderr, exit
code, inspect) live under `results/container-t1/receipts/`; their only shared
data is the candidate JSON in the dedicated initially empty `output/` folder.

The frozen study mount is
`/Users/taka/Documents/Codex/2026-09-19/new-chat-7/work/agent-interface-59-rejected-action-cover-continuation-t0-20261001/research/analysis/map01_rejected_action_cover_continuation_59_t0_20261001`;
the output mount is its `results/container-t1/output` child, while receipts
are in the sibling `results/container-t1/receipts`. After creating those two
directories and verifying output is empty, run the candidate exactly once:

```sh
docker --context orbstack run --pull=never --name ai59-cover-cont-t1-candidate --cidfile /Users/taka/Documents/Codex/2026-09-19/new-chat-7/work/agent-interface-59-rejected-action-cover-continuation-t0-20261001/research/analysis/map01_rejected_action_cover_continuation_59_t0_20261001/results/container-t1/receipts/candidate.cid --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/work/agent-interface-59-rejected-action-cover-continuation-t0-20261001/research/analysis/map01_rejected_action_cover_continuation_59_t0_20261001,dst=/src,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/work/agent-interface-59-rejected-action-cover-continuation-t0-20261001/research/analysis/map01_rejected_action_cover_continuation_59_t0_20261001/results/container-t1/output,dst=/out --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 512m --cpus 1 --env PYTHONDONTWRITEBYTECODE=1 --workdir /tmp python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/candidate.py --output /out/candidate_output.json > /Users/taka/Documents/Codex/2026-09-19/new-chat-7/work/agent-interface-59-rejected-action-cover-continuation-t0-20261001/research/analysis/map01_rejected_action_cover_continuation_59_t0_20261001/results/container-t1/receipts/candidate.stdout 2> /Users/taka/Documents/Codex/2026-09-19/new-chat-7/work/agent-interface-59-rejected-action-cover-continuation-t0-20261001/research/analysis/map01_rejected_action_cover_continuation_59_t0_20261001/results/container-t1/receipts/candidate.stderr
```

Only after exit 0 and a valid six-row candidate file, run the auditor once in a
separate container with the same isolation/resource flags and mounts, using
the distinct name `ai59-cover-cont-t1-auditor`, CID file
`results/container-t1/receipts/auditor.cid`, command
`python -B /src/auditor.py --input /out/candidate_output.json --output /out/audit.json`,
and stdout/stderr files `auditor.stdout`/`auditor.stderr` in the receipts
directory. Capture inspect JSON by container name. Do not remove containers.
