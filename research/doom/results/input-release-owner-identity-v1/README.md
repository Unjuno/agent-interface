# Missing owner identity release-batch control v1

## Question and frozen decision gate

- **H:** the v3 release-batch verifier may accept missing owner identity because
  Python treats `None == None` as true.
- **T:** submit one ordinary one-key release whose transition receipt and
  post-batch owner-state sample both carry `owner_id: null`; keep token, timing,
  empty-owned-state, and backend-ownership predicates valid.
- **D:** `owner_transition_verified` must be false and
  `owner_identity_matches_after_batch` must be false. Any true result fails the
  control.
- **C:** deterministic synthetic owner/backend fixture; no OS input, GUI,
  model, game, or container.
- **U:** tests fail-closed receipt identity validation only. They do not prove
  physical key release, application consumption, exact key-up time, useful
  feedback, recovery, or live behavior.

The baseline source was frozen before the red-first control:

| Source | SHA-256 before control |
|---|---|
| `research/doom/doom_retained_input_backend_v3.py` | `2b02a5c5186fdfae448bb58ad07131e8b229c3131adcc91be98b34ebe10e9db3` |
| `research/doom/test_doom_retained_input_backend_v3.py` | `1607f2532b96835e22b4add24c0712316c23642166bc4ba2d49573a98b4fb412` |

The first run, before the fix, was:

```text
python -m unittest research.doom.test_doom_retained_input_backend_v3.Tests.test_missing_owner_identity_fails_closed -v
FAIL: AssertionError: True is not false
Ran 1 test
FAILED (failures=1)
```

This confirms the hypothesis against the frozen implementation: absent identity
on both sides was incorrectly treated as a match.

After the fail-closed change, the source identities used for the retained
candidate are:

| Source | SHA-256 after fix |
|---|---|
| `research/doom/doom_retained_input_backend_v3.py` | `1b96e852fa5da4cee531bdcb4832345a1f8355574bdcaa87665ac50c667b9f55` |
| `research/doom/test_doom_retained_input_backend_v3.py` | `f210cc2cb4b360f6f925fe33cf06d9c0eaff34bd6e3da1e215374c4204d335b9` |

## Candidate and audit

The adapter now accepts identity agreement only when the post-batch identity
and every release receipt identity are nonempty strings and equal. Explicit
key-up and cleanup behavior are unchanged. Reproduce and audit the retained
receipt from the repository root:

```text
python research/doom/results/input-release-owner-identity-v1/capture_candidate.py
python research/doom/results/input-release-owner-identity-v1/audit_candidate.py
```

`candidate.json` retains the post-fix synthetic receipt. `audit_candidate.py`
independently checks that the null identity is the relevant failing predicate,
the transition is marked unverified, and physical authority remains false;
`audit.json` retains the result and candidate hash.

Local verification after the fix:

```text
python -m unittest research.doom.test_doom_retained_input_backend_v3 -v  # 14/14 PASS
python -m unittest research.live_control.test_input_transition_owner_v3 -v  # 8/8 PASS
python -m unittest research.doom.test_map01_overlap_controller_v40 -q  # 3/3 PASS
git diff --check  # PASS
```

This is construction evidence. It does not satisfy the current goal's live
threat-control, useful-feedback, matched-condition, bounded-recovery, or MAP01
completion requirements.
