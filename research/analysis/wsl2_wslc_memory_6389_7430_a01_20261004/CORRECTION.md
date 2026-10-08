# A01 post-preflight process ownership clarification

This note is additive to the immutable first outcome in `README.md`; it does
not change the disposition, candidate count, or any measurement.

After the README and Issue #7430 comment were first recorded, process-parent
inspection resolved part of the WSLc CLI snapshot:

- The WSLc snapshot contained five `wslc.exe` processes. PID 26832 was this
  task's read-only `wslc.exe container ls --quiet`, launched from this task's
  still-running PowerShell wrapper PID 47108. It was an additional leftover
  from the earlier compound diagnostic, distinct from the later foreground
  CLI session that had already returned exit code 1 on local interruption.
- Only PIDs 26832 and 47108 were terminated, after verifying their exact
  parent-child relation and command lines. This stopped this task's own
  stalled read-only inventory probe and its sequential wrapper; no container
  lifecycle command followed.
- The four other WSLc CLI processes observed in that snapshot were left
  untouched. A subsequent snapshot showed concurrent `wslc ps`,
  `wslc images --digests`, `wslc container ls --quiet`, and
  `wslc container list --all` commands. Another `wslc ps` appeared during the
  follow-up check. These process observations do not establish which commands
  had returned, the runtime's internal state, or the cause of the delay.
- The 17 Ubuntu `native_mcp_v1.py` processes were not touched. No container
  was started, stopped, inspected or removed by this task.

The WSLc shared-runtime delay remains **unattributed**. This is evidence of
concurrent WSLc control-plane calls and an unresponsive local read-only probe,
not proof of a product defect. Issue #7430 remains on HOLD until an idle/image
gate can be established under an uncontended, attributable host snapshot. Do
not restart WSLc, terminate other processes, or rerun A01 based on this note.
