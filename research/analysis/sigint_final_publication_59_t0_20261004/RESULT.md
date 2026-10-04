# Result — F03 final-summary SIGINT window probe

Executed 2026-10-04 in WSLc 3.0.1, session 1. The run used the pre-cached Linux amd64 image `python:3.12-slim`, image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, repo digest `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`. Network disabled; configured 0.5 CPU and 128 MiB; `/tmp` was tmpfs. WSLc warned: kernel lacks swap-limit capabilities/cgroup is not mounted, so memory was limited without a verifiable swap bound.

Command:

```powershell
wslc run --rm --network none --cpus 0.5 --memory 128m --tmpfs /tmp:rw,noexec,nosuid,size=32m --mount type=bind,source=C:\Users\junny\Documents\Codex\2026-10-03\new-chat-3\work\f03-sigint-final-window-probe-20261004,target=/work,readonly python:3.12-slim python /work/probe.py
```

Raw stdout: `{"child_returncode": -2, "child_stderr_has_keyboard_interrupt": true, "persisted_summary": {"verdict": "PASS_SCOPED_PIPE_NOTIFICATION"}}`. Python's `subprocess` reports a process terminated by SIGINT as `-2`; this is not a numeric shell exit code of 130.

An output audit checks the observed child return code and persisted PASS file. `probe.py` SHA256: `0212B5C187949CB8CC58CFE5AC97D2E53EA0C6D0F575A30BDD4FA1407A5BA463`; raw output SHA256: `3E6351949CFAD108684BC7640117270D97D782C46DD42FD9D09294E383B3EC00`.

Interpretation: Linux/Python signal masking allows a pending SIGINT to be delivered only after the PASS file has been written, yielding a persisted PASS while the child terminates from SIGINT. This independently reproduces the mechanism identified by source review of F03 `cd51958` without importing or executing any F03 source, runner, test, producer, or auditor. It does **not** qualify F03 behavior, summary durability, SIGKILL/power loss, active-reader interruption, custody, or the formal four-cell experiment.

The initial inline attempt printed a locally assigned value `exit_code: 130`; that value was not the child's observed process status. Its exact output is preserved under `attempts/preliminary-inline-output.txt` as a superseded, insufficient measurement. The corrected saved probe observes the real subprocess return code. The output audit was authored and run by the same worker; it is not an independent review. A later committed-tree check caught Git line-ending normalization not visible to a working-file-only hash check; package `.gitattributes` now preserve exact bytes, and the audit can verify both the working files and committed blobs.
