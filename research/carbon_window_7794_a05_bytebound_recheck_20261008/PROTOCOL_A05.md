# Carbon-window A05 — byte-bound replay protocol

Successor to Issue #7794 A04, PR #8183. A04 is immutable; this run replays reconstructed exact execution bytes in a new allocation after independent readback found manifest mismatches.

## Frozen hypothesis and decision

**H:** The checked-in A04 fixture, candidate, and auditor, each with exactly one additional final LF byte, reproduce their recorded execution SHA-256 values and the ten-row comparator result when those bytes are frozen before invocation.

**PASS_BYTEBOUND_REPLAY_SCOPED** requires all frozen blob IDs and SHA-256 values to match before execution; one candidate and one auditor invocation, each exit 0; independently reconstructed ten rows; the first nine A02 cases all agree between global-lexicographic and serial-ASAP comparators; the final discriminator differs with global schedule A=1,B=0 and serial-ASAP infeasible. Any mismatch is retained as FAIL/HOLD without retry.

This is a finite synthetic comparator-method result only. It does not repair or retroactively validate A04, and makes no operational scheduler, energy, emissions, or CO2 claim.

## Inputs and source identity

Current-main publication base: f72cd82d62c9d9f3860d4fa40980c56618bf5aaf.
A04 immutable source branch: research/carbon-window-7794-comparator-a04-20261005.
For each source below, `recovered_sha256` is the A04 manifest value reproduced by appending one LF byte to the exact Git blob bytes. `git_blob` binds the checked-in source; the recovered file is stored separately as the exact A05 execution input.
- cases: Git blob fc8f717c700e248198a5c8387ba9f85f5ea7e05e; checked-in SHA-256 afa9d6f50183125a1188f0c018fe41f1e2c7b142ceaddba76f6d278718af4be2; recovered SHA-256 782cc4f8d85364a6bed2de55ad2b399ba9ecbbf1b43cff9a494ddacd6ab019b5
- candidate: Git blob 1724b00b63bbf48dbbe253e9a1890728fa66ed65; checked-in SHA-256 c40d47d8350e698c35b0c57a2165118d9c8f0e122adc49b9afc680a59cd3dee0; recovered SHA-256 edf7c02f77859c67c6e5911a082e2eef456dec8d8c1b7bdbd5f835585a455022
- auditor: Git blob 85cffb6475655260db209d3998cdbcc1b88f6f7a; checked-in SHA-256 05e8b64a7c8ad87ecac4e74f71eef27ec1966a31596759cd1ae64a4f32d1053e; recovered SHA-256 ee79d184e4a89e2aee62ee43cb908a92332e27417ef48fa95d3ec83d5a710452
- construction tests: Git blob cf7743670b303732ada4d721a5fa84e217acf1c3; checked-in SHA-256 11e8dc1051a1e8b6eae5ecb85935c8c0411983cb239f7e1fa8d2f116feb8e7d5; recovered SHA-256 17db8c837b9800731ff5eb6de932af92c32533709097801a3634ea4557219b05

Candidate output path is isolated at formal_a04/candidate.json beneath this A05 working directory because the frozen auditor expects that relative path. The fresh A05 directory is distinct from every A04 result path.

## Execution boundary

No WSL/WSLc, Docker, GUI, network, model, user data, or external-effect operation. Python 3.12.10, Windows 11 x64, standard library only. This is a native task-host CPU fallback, not a container run and not WSLc migration evidence. Run construction tests before freeze only. Then candidate once, auditor once, no retry.
