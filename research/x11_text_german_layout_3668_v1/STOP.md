# Allocation disposition: STOP before hypothesis test

Date: 2026-09-21 JST
Allocation: issue3668-german-xkb-text-v1
Frozen source/scripts/protocol: commit 879bbce6f257efa0723400e5e636756236932925

The first fresh private Xvfb row (de-01) stopped at the frozen XKEYBOARD/XTEST extension prerequisite. The runner returned STOP_OR_FAIL with xkb_extension=false. It stopped before setxkbmap, receiver-window creation, backend construction, planner call, or any XTEST/key/button event. No layout change or task input occurred. Exact row is results/de-01.json (SHA-256 D6210BD35BF85CE435B2D62C28039BD6A4EB403159F3490FA75FCA411C6C31C0).

This is a setup/harness STOP, not evidence for or against the German text-delivery hypothesis. The remaining three rows were not run, and the independent matrix auditor was not invoked because the frozen matrix is incomplete. No retry, package install, alternate server, or source change was made under this allocation. Any diagnosis or corrected test requires a distinct successor allocation; preserve this STOP unchanged.

Container evidence: none. The run used the preregistered WSL host-Xvfb fallback because Docker Desktop and the WSL Docker daemon are unavailable.
