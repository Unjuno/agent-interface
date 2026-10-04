# Per-key cancellation interval package — manifest audit correction

The parent PR #7529's focused fake-Xlib suite reproduced independently at
16/16 on head `ebe86025e7f122f0a93b841cf41211bc50b715fe`. Its published audit
did not reproduce from a clean checkout: `audit.py` raised `FileNotFoundError`
on `baseline/__pycache__/executor_v3.cpython-314.pyc`.

The parent manifest has 20 entries. Seventeen are tracked and present with
matching SHA-256 digests. The other three are generated `.pyc` files that are
listed in `FILES.sha256` but absent from the frozen Git tree. `AUDIT.json` and
`FILES.sha256` themselves are tracked but intentionally not members of that
manifest. The original package, manifest and `AUDIT.json` are left unchanged.

The additive v2 auditor pins the parent Git head, verifies the exact tracked
tree membership and all 17 available manifest hashes, and explicitly records
the three missing bytecode paths. Result: `PASS_MANIFEST_GAP_RECONCILED`,
zero errors. This corrects only the audit reproducibility gap; it does not
convert the parent's original audit run into a pass on the original checkout,
and it does not modify or invalidate the 16/16 unit-test result.

## Scope boundary

The source change bounds each cancellation key-release request by a shared
XSync completion timestamp. Fake-Xlib construction validates record shape and
publication only. No real X server, physical key-up instant, application
consumption, gameplay, useful feedback, recovery efficacy, or live #59 gate is
established.

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v research.doom.cancel_key_release_intervals_59_4d74_20261004.audit_v2.test_audit
PYTHONDONTWRITEBYTECODE=1 python3 -B research/doom/cancel_key_release_intervals_59_4d74_20261004/audit_v2/audit.py
git diff --check
```

The first v2 test was run before `audit.py` existed and failed as expected
(the CLI was missing). After implementation, the regression passes 1/1 and
the independent v2 audit exits 0. The retained predecessor's original
`AUDIT.json` remains unchanged.
