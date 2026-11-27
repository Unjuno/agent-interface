# R26: Explicit foreground activation repeat

A one-attempt prospective repeat of the R24 delayed-effect and bounded orphan-recovery boundary, frozen on main `490d7bcb4d84927116112e5ff348cdeadfc489d6`. It retains the R25 fixture, lease (2 s), effect delay (6 s), horizon (2 s), and one public dispatch / one possible recovery call. It changes only setup: the runner pauses after the fixture is ready; Computer Use must select exactly one window with the expected title and raise it; the independent foreground probe must match the recorded HWND and PID before MCP observe or dispatch.

R25 is not resumed. No retry is permitted. If foreground verification fails or times out, the single R26 attempt is stopped and retained as pre-dispatch failure.
