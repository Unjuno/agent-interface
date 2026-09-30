# Run log — #5156 local Docker argv construction

## Predecessor T0.1 — preserved STOP

- Base main `5a22b42f0d851d0d4549d197d37680d550b709df`.
- Docker image inspection output was `Entrypoint=null`, `Cmd=["python3"]`; the freeze incorrectly reversed these fields.
- Four pre-freeze unit checks passed, but they did not validate image command metadata.
- One container invocation passed `/work/candidate.py` directly while leaving `Entrypoint=null`; Docker replaced Cmd and attempted direct OS execution of a source file without a shebang.
- Outcome: `exec /work/candidate.py: exec format error`. Python/candidate process did not start; no raw/audit; zero GUI/input; no retry.
- Immutable artifacts are in `predecessor_t0_01/`.

## Successor T0.2 — current construction test

- Frozen base main `241a0cac915df615f7f79b4ce2042b946ea7fbd7`.
- Image `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, amd64, local config `Entrypoint=null`, `Cmd=["python3"]`.
- Explicit override `--entrypoint python3`; frozen source/input hashes are in `FREEZE.json`.
- Five pre-freeze construction tests: 5/5 PASS.
- Candidate: one invocation, exit 0. Effective process argv exactly matched; preflight passed before the smoke callback. Raw retained.
- Independent raw-only auditor: one separate invocation, exit 0, `PASS_LOCAL_ARGV_CONSTRUCTION_ONLY`, errors `[]`.
- No formal #5156 runner, Xlib, Xvfb, X11 input, GUI, model, GPU, or network operation occurred.
