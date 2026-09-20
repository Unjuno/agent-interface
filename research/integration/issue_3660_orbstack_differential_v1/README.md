# Issue #3660: independent reconstruction of #3652 transition evidence

Audit-only successor to #3652/#3656. It consumes the exact retained formal raw; it never launches a GUI or repeats the formal allocation. Predecessor artifacts are preserved byte-for-byte under `evidence/`.

## Reproduce in OrbStack

Build/run against the already frozen image (build is unnecessary):

```sh
mkdir -p /tmp/issue3660-output
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=16m \
  -v "$PWD:/work:ro" -v /tmp/issue3660-output:/output:rw \
  -e PYTHONDONTWRITEBYTECODE=1 -e MUTATION_OUTPUT=/output/mutants \
  -e PREDECESSOR_AUDIT=/work/evidence/predecessor_audit_readback.py \
  --entrypoint /bin/sh sha256:f8ae93cfedd412cfe39ca575a97abc32c4d6e99ee7b5cc7848e79e0ce08bdc9f \
  -lc 'cd /work && /usr/bin/python3 validate_bundle.py && /usr/bin/python3 audit_raw.py evidence/frozen_3652_formal01_raw.json > /output/reconstruction.json && /usr/bin/python3 test_audit_raw.py evidence/frozen_3652_formal01_raw.json > /output/mutation-tests.stdout.json'
```

The committed `evidence/reconstruction.json`, mutation receipt and individual mutant JSON files are the actual OrbStack outputs from this invocation. The historical result hash is over the exact downloaded file bytes, not parsed/re-serialized JSON.

## Result

`HOLD_AUDIT_EVIDENCE_INCOMPLETE` for reconstruction of all five predecessor claims; `PASS_MUTATION_CONTROLS` for the independent auditor's eight integrity mutations. The unmodified input passes structural checks, but three claim-level receipts are absent: modal owner and disappearance, an actually exercised/receipted Chromium stale-generation admission, and active-window plus fresh Calc role resolution on return. The experiment therefore does not turn #3652's reported 5/5 into an independently supported PASS. It also does not invalidate the historical formal result; it narrows what the retained raw independently proves.

The unchanged predecessor readback audit was separately replayed in the same pinned container and again emitted `PASS_POSTHOC_EVENT_RECOMPUTATION`; see `evidence/predecessor-audit-replay.json`. The stricter reconstruction and mutation controls explain why that receipt does not close the evidence gaps.

See `PREREGISTRATION.md` for H/T/D/C/U and `evidence/RESULT.md` for provenance, container gates, scope, and exact digests.
