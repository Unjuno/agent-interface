# T10 execution report — startup gate PASS

## Outcome

**PASS_START_GATE_ONLY.** The PR-open, attempt-1 workflow built the pinned
`linux/amd64` image on a native x86_64 GitHub-hosted Ubuntu 24.04 runner.
`wmctrl` was present during the image build and the constrained runtime
preflight returned `/usr/bin/wmctrl`, version 1.07. Both dedicated evidence
mount probes passed. The single real `session_map01_v13.py` child reached
`ready`, emitted an exact sequence-1 initial observation with matching PNG and
recomputed RGB hashes, received only neutral `finish`, and exited 0. No input
admission occurred. The independent raw-only auditor exited 0 with no errors.

This closes only the frozen startup/first-observation gate. It is not an
attack, task-effect, onset-phase, recovery, or product result.

## Frozen allocation and artifact identity

- Allocation: `MAP01-ATTACK-ONSET-STARTGATE-4223-T10-20261001-01`.
- Frozen source commit: `eafb113e1493b55cf22cd4ca8061325dfccb3465`.
- Frozen base main: `b3d3ed8315d016967f361a36b2d3d022adad66f0`; workflow observed
  live main `975aed8ad7923a109cfb445b4028d18a10088f63`. The workflow confirmed
  the frozen commit is an ancestor and its scope-drift gate passed; the exact
  `main-drift-paths.txt` is preserved in the artifact root alongside the
  `main-freeze-gate.txt` receipt.
- Workflow run: [36799782678](https://github.com/Unjuno/agent-interface/actions/runs/36799782678),
  attempt 1; both startup-gate and replay-gate passed.
- Workflow artifact: ID `11135148749`,
  `map01-attack-start-gate-t10-36799782678`, 85,679,261 bytes,
  SHA-256 `0151b24244a12c442f28c6aef9326c5e600a77dfab2698ad1538fbabec321bcf`.
  The downloaded ZIP matched exact metadata size/digest and passed `unzip -t`.
  The immutable ZIP and extracted package evidence are retained in `evidence/`.
- Runner: GitHub-hosted Ubuntu 24.04, native `x86_64`; Docker Engine 28.0.4.
- Immutable runtime artifact 10398313098, SHA-256
  `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`;
  verifier passed 2,592/2,592 sources and 12/12 wheels. All 26 runtime source
  hashes recorded by the candidate independently match the artifact manifest.
- Image: `sha256:e096462b398defb30f1da172ca5b2b20cebe3c68d0b341ece7df2a3317c0839e`
  (`linux/amd64`); Python 3.13.5; ViZDoom 1.3.0.
- `wmctrl` build-time check passed; constrained container preflight exit 0,
  `/usr/bin/wmctrl`, version 1.07.

## Candidate and audit accounting

- Candidate invocations 1; retries/replacements 0; candidate child/container
  exit 0. Child PID 11; elapsed 4.349241 s.
- Candidate output mount: host mode `0o777`; container probe UID:GID `0:0`,
  exit 0. Auditor output mount: same mode/UID:GID, exit 0.
- Events include `ready`, one exact initial observation (1280×800), one
  `finish`, one post-control score; input-admission count 0. RGB SHA-256
  `c275d19e806e0956458e5ca1278d9c91d961a5445977a6c3991bc502640c4d3a`;
  retained PNG SHA-256
  `3f339ccdec2cd3bd2c0fb3053847eb3ad781108272ed670cd5014448c9ed7678`.
- Independent auditor invocations 1; exit 0; 36 checks passed, zero errors.
  It independently recomputed PNG/RGB hashes and confirmed source-manifest
  closure, container constraints and receipt consistency.
- `evidence/OBSTAC_EXECUTION.json`, `candidate/RAW.json`, child streams,
  initial PNG, all candidate runtime files, mount/build/preflight logs,
  `audit/AUDIT.json`, verified manifest/source snapshot and immutable run ZIP
  are preserved. `evidence/EVIDENCE_SHA256SUMS.txt` lists 2,619 extracted
  artifact files (including the ZIP) with SHA-256; all entries reverified.

## Interpretation / limits

The specific T9 stop was repaired: native startup did not repeat the missing
`wmctrl` failure, and the game reached the exact first-observation gate. T8's
OrbStack arm64→amd64 SIGSEGV therefore remains an unresolved host/emulation
contrast; T10 does not prove its cause. The observed initial HUD signals were
health 100 and ammo 50, and the neutral post-control record had zero kills,
zero deaths, reward 0, and no map exit. Because no attack input was issued,
these are startup context only and do not test the T10 H about attack timing or
the parent onset hypothesis. No attack/effect/onset/recovery/model/latency or
product claim follows. Any gameplay experiment requires its own existing
preregistration and allocation.
