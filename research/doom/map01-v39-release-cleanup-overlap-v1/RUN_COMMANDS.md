# Executed commands

Baseline on the exact parent source (`fbed929f629dabaa9ae752019d0ee7151d4d2298`):

```powershell
python research/doom/map01-v39-release-cleanup-overlap-v1/run_baseline.py
```

Expected and observed: regression test fails because the baseline still marks
the overlapped release ordinary.

Earlier lower-level candidate, executed in cached WSLc image
`sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`
with network disabled, one CPU, 512 MiB accepted memory limit, read-only source
and writable evidence output:

```powershell
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume "${repoPath}:/src:ro" --volume "${resultsPath}:/out" --workdir /src `
  sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364 `
  python -B -m unittest -v research.doom.test_doom_typed_release_backend_v3
```

`RAW_CANDIDATE_WSLC_DIRECT_BOUNDARY.txt` retains stdout and stderr, including
the WSL swap/cgroup warning. The memory limit was accepted; swap isolation was
unavailable. Its exact test source SHA-256 is recorded in
`FOLLOWUP_EXECUTION.json`.

The current follow-up drives the same cleanup case through the adapter's
`execute` entry point and the inherited executor stub, verifying that the fake
owner records cleanup without an explicit key-release request:

```powershell
python -B research/doom/map01-v39-release-cleanup-overlap-v1/run_baseline.py
python -B -m unittest -v research.doom.test_doom_typed_release_backend_v3
python -B -m unittest -v research.live_control.test_input_transition_owner_v3
```

The exact #7378 parent failed this test; the host candidate passed 21/21 and
the current owner-wrapper suite passed 8/8. Raw outputs and their separate exit
receipts are retained. The host execute-path candidate ran once; the WSLc
candidate was not rerun after its original lower-level boundary result.

The earlier combined 29/29 run remains as historical validation of the direct
`raw()` boundary and wrapper tests. The current execute-path follow-up instead
records the backend (21/21) and owner wrapper (8/8) as separate host runs.

The adjacent-suite wrapper exits with an error when its saved exit code is
nonzero; it completed without that error, so `ADJACENT_EXIT.txt` records 0.
The original WSLc log-only auditor is preserved as
`results/RAW_AUDIT_WSLC_INITIAL.txt`. Its seven checks did not parse a unique
terminal summary or compare both exit receipts; the strengthened host-side
auditor and mutation tests are retained as the current audit result.

```powershell
python -B -m unittest -v research.doom.map01-v39-release-cleanup-overlap-v1.test_audit
python -B research/doom/map01-v39-release-cleanup-overlap-v1/audit.py
```

The current host-side auditor passed 12/12 checks and the mutation suite passed
5/5; its raw output and `AUDIT_EXIT.txt` retain exit 0. This follow-up reread
retained logs only; it did not rerun the backend candidate or WSLc container.
