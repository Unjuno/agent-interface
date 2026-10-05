# Formal run receipt

- Status: `PASS_PROVENANCE_BOUNDARY`
- Base `main`: `18bf390d0c230b5a2ee9675cebffbc0e51bfea2d2`
- Runtime: Ubuntu WSL, CPython 3.12.3, CPU; no Docker/WSLc container, model, GUI, GPU, network request from the candidate, dispatch, or external task effect.
- Generator: 1 pre-freeze invocation; candidate: 1 post-freeze invocation, exit 0; auditor: 1 post-freeze invocation, exit 0; retries: 0.
- Candidate and auditor source/input hashes matched the frozen values in `FREEZE.md` immediately before candidate execution.
- Candidate input SHA-256: `5be1bb09bb7ad6554d830e138e46869f5acb69b0b1c88f4d53669a73567c9547`.
- Candidate output SHA-256: `605325703b751209ffc75da44fd90fb235aa502d4623ffb928cf234fadee84ba`.
- Audit output SHA-256: `365bc99aae446f9a8881c10afadd79598d2b0b0901176f9b6a2797d221602248`.
- Oracle: all 10 outcomes matched. Statuses: SAT 1; complete conflict core 2; invalid provenance 3; stale revision 1; missing hard background 1; immutable-background block 1; unknown 1.
- Core checks: pair-conflict core exactly `{pair_x0,pair_x1}`; independent MUS set exactly `{mx0,mx1}` and `{my0,my1}`; immutable background was not offered as relaxable.
- Authority: `dispatch_allowed=false` and `input_authority=false` on every row.
- Mutation controls rejected (8/8): omit core member, dispatch UNSAT, offer hard background, promote bad source, tamper source bytes, shift span, reuse stale revision, remove hard background.

Exact formal commands, each invoked once:

```text
wsl.exe -d Ubuntu -- bash -lc 'cd /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_7501_source_provenance_a02_20261005 && python3 candidate.py'
wsl.exe -d Ubuntu -- bash -lc 'cd /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_7501_source_provenance_a02_20261005 && python3 audit.py'
```

The candidate stdout is retained exactly in `CANDIDATE.json`; the independent audit receipt and exact rejected-control names are retained in `AUDIT.json`. No second invocation or retry occurred.
