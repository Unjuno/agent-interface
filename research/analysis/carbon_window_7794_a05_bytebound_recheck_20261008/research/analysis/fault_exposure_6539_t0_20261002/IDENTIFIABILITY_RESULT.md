# Issue #6539 paired-twin identifiability check

**Disposition:** `PASS_FINITE_IDENTIFIABILITY_CHECK` for this exact synthetic
two-state construction only. This is an analytical boundary check, not the
fault-exposure training T0, not a WSLc/container result, and not an empirical
claim about GUI agents.

## H / T / D / C / U

- **H:** If two hidden states have byte-identical policy-visible observations
  but differ in whether an action is authorized, an observation-only policy
  cannot both choose the required action in the authorized state and avoid a
  non-YIELD unsafe proposal in the unauthorized state.
- **T:** `paired_twins.py` builds one authorized `CONTINUE` case and one
  unauthorized twin with identical visible tuple `(1, 0, 1, 1, 0, 1)`. The
  exhaustive checker enumerates all three outputs: `CONTINUE`, `RECOVER`, and
  `YIELD`. A separate hidden ledger supplies authority and required-effect
  labels; only the visible tuple represents policy input.
- **D:** The finite check passes if no one proposal simultaneously yields
  authorized completion on the authorized twin and avoids an unsafe proposal
  on the unauthorized twin. All three proposals were enumerated; none meets
  both conditions.
- **C:** This construction encodes the non-identifiability by design. It does
  not model a trained policy, observation-channel reliability, or the
  frequency of these paired states.
- **U:** Exactly two authored hidden states and three proposal classes. It does
  not estimate recovery benefit, unsafe-proposal rate under training, transfer,
  effect semantics, or safety in any real interface.

## Execution record

- Command: `python -m unittest -v test_paired_twins`
- Environment: local Windows host Python; no model, GPU, WSLc, container,
  network, GUI, user data, or external action.
- Final result: 4 tests PASS.
- Construction failure preserved: first test draft incorrectly expected both
  `CONTINUE` and `RECOVER` to complete the authorized case whose required
  action is `CONTINUE`. The first run was 3 PASS / 1 FAIL. The assertion was
  corrected before any candidate/training work; the final run passed all 4.
- SHA-256 `paired_twins.py`:
  `5a967268ef0c980ce0a81a58a130d9c54bcacd91e993c14b5671bbfcbe78628a`
- SHA-256 `test_paired_twins.py`:
  `6aa18593b82fcfc291b8e8f2df70cc7ee32870100c59b9d39a92276b0b45bb92`

## Consequence for T0

The training study must retain an independent authority/effect ledger and
paired identical-observation twins. It must separately score (1) eligible
authorized-effect completion, (2) unsafe raw proposals, and (3) unnecessary
YIELD. A hard admission gate is still required, but its zero unsafe-admission
rate cannot replace raw proposal scoring. This check supplies no T0 efficacy
result and authorizes no WSLc allocation.
