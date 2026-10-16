# Owner-issued per-admission identity A03

## Question and scope

**H.** A successful KeyPress admission can receive a stable, monotonically sequenced `admission_id` inside the owner thread, and that same value can be carried through the caller's explicit per-key release transition and the nested owner KeyRelease/XSync receipt. Identity remains exact for one key, reverse-order releases of two held keys, and successive admissions of the same key. Identity mismatches fail closed. The existing XTest/XSync operation order and all false-authority fields remain unchanged.

**T.** After the pre-freeze construction test passes, run the frozen candidate exactly once in the pinned WSLc Python image. It uses fake Xlib and a stubbed outer action executor to exercise three fixed traces: A down/up; A+B down then B+A up; C down/up twice. A raw-only auditor independently checks case context, owner-generated IDs and sequence, exact identity across admission/release/nested owner receipt, event order, call order, monotonic interval nesting, neutral final fake keymap, and false authority. The auditor also applies 12 corruptions to copies of the raw result and requires every corruption to be rejected.

**D.** `PASS_OWNER_ADMISSION_ID_SCOPED` requires candidate and auditor exit 0, exact frozen-source hashes, exactly the three declared cases, no runner error, admission ID format `<owner_id>:admission:<sequence>`, increasing owner-local sequence, equality of each ID at all three event surfaces, correct identity under reverse release and repeat cycles, one exact owner receipt for each release, caller interval enclosing the owner key-up/XSync interval, exact interleaved XTest/XSync calls, verified empty final keymap, false authority, and rejection of all 12 corruption controls. Any mismatch is FAIL/STOP; there is no retry.

## C / U

**C.** This uses a deterministic fake Xlib server, not an X server. It does not model OS scheduling, X server errors beyond the stub, key delivery to an application, or game behavior.

**U.** This is construction evidence for explicit identity propagation only. It provides no live physical key-up, useful feedback, recovery, MAP01, latency, safety-rate, task-effect, or product-readiness evidence; it does not allocate the #59 live lane. Authority remains false.

## Frozen lineage and execution

The source baseline is origin/main `a9352dc53c783f1501046d762bc36c34bc6ab480`. The copied baseline blobs are InputOwner v10 `341b3c01649943ddaad5f28431a792c4889cc36e`, transition wrapper v3 `99dfc7c9907b018e7473bc2ba8a7393a5b221f51`, and retained backend v4 `81484e6146bb8b93a007f338df3e504620924a45`. Candidate deltas are owner v12, wrapper v5, and backend v5, isolated in this package.

The one-shot environment is cached image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, linux/amd64, Python 3.12.15). Candidate and auditor use separate disposable containers, one CPU, network disabled, read-only source and distinct writable output. No memory limit is set because this host's effective cgroup/swap limit has not been verified. No image pull or retry is allowed. `FREEZE.json` hashes every source and protocol input used for the candidate or auditor.
