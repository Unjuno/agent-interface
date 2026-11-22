# A06 run result

The candidate started once in the preflighted local WSLc Python 3.12.15 amd64 image. The captured runner record is `RUNNER_OUTPUT.json`; it contains the full synthetic trace, owner records, release rows, and the frozen auditor output. The first keycode 31 release was dropped by FakeXlib, the owner injected a retry and verified the key-up, the wrapper published two verified release rows with empty final synthetic state, and querymap samples occurred between UP injections.

Run command: `wslc run --rm --pull never --network none --cpus 1 --memory 512m --tmpfs /tmp:rw,size=32m --volume <A06-directory>:/src:ro --workdir /src --env PYTHONDONTWRITEBYTECODE=1 python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B runner.py`.

The frozen auditor returned **FAIL** because its `per_key_receipts_match_rows` check compared `receipt.keycode` with `release_row.keycode`; release rows have a `key` field and the nested owner receipt has the keycode. The post-hoc audit reads only the captured runner record, confirms the raw behavior and identity fields, and does not rerun or replace the frozen auditor verdict. Therefore the allocation status remains `FAIL_FROZEN_AUDITOR_CHECK`; the raw trace is useful composition evidence, not a protocol PASS.

WSLc emitted: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” The run used configured one-CPU, 512 MiB, and 32 MiB tmpfs limits, but no claim is made that the memory cap was enforced. The candidate bundle was bind-mounted read-only and network access was disabled.

Scope is synthetic owner/wrapper composition only. It does not establish real X11 behavior, OS-input effect, V15 session startup, V39 threat handling, useful feedback, or live task success. A04's earlier synthetic ordering PASS remains scoped to its original source; A06 shows that this retry candidate's querymap sampling changes that ordering.
