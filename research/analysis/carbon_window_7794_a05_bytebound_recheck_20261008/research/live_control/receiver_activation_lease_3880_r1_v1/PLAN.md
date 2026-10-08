# Receiver-local activation lease r1 — frozen plan

Issue: #4442. Base main: `3666992ab2b5e1b41b159b361d1c690d8e720fdf`.

H/T/D/C/U and the 20-case matrix are frozen in Issue #4442. Scientific source is `source/{lease.py,server.py,run_case.py,run_formal.py,audit.py,controls.py,test_receiver.py}`. Construction is excluded. Formal command after public source readback:

`python -S -B source/run_formal.py --out formal/run01`

Then read-only audit and corruption controls:

`python -S -B source/audit.py formal/run01`

`python -S -B source/controls.py formal/run01 --out formal/CONTROLS.json`

No same-ID formal rerun, replacement, exclusion or post-result gate/source tuning.
