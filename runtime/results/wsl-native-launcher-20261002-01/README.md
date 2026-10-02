# Windows to WSL native iteration launcher

The retained PowerShell launcher invoked the unchanged native integration runner
in Ubuntu directly using existing interpreters. Protocol 409 and harness 192
checks passed, with Windows process exit 0. Docker was not started and no package
installation or image build took place. The original direct UNC invocation was
refused by the host unsigned-script policy before any test started; the process-
scoped PowerShell invocation documented in WSL_NATIVE.md then ran the suites.
The host execution policy was not changed.

Two separate negative invocations returned exit 1: reusing the existing output
path (the Python runner refused before suites), and a relative Linux repository
path (the launcher refused before WSL). The passing result directory was retained
unchanged. Full suite logs, Windows logs and the launcher source are retained.

This is a native contract check and launcher lifecycle verification. It is not a
Docker timing comparison, GUI task-success result, peak-memory measurement or
proof of resolved OOM. Host .wslconfig activation is still pending a coordinated
full WSL stop/start; no other workload was interrupted.
