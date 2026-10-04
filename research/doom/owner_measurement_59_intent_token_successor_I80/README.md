# MAP01 per-key identity binding successor (I80)

This additive construction repairs one concrete identity mismatch in the retained owner measurement builder. The builder copied from current main `a5f2bf291787000627abbc12c123af4bd2873d5c`; the PR branch was rebased onto `853a867fb554c04d8f1223f9525f9eaf7d2792b6`, and the builder plus lease source paths were verified unchanged across that advance looked up `lease.token`, while the selected runtime path provides `lease.intent_token`. The previous native A01 fixture added a test-only `token` alias, so its scoped native result remains valid for the fixture it exercised but does not prove production-path identity linkage.

The successor routes both explicit key-up and bulk-cleanup telemetry through `_measurement_intent`, which accepts only the actual nonempty string `intent_token`. The regression imports the actual repository `lease_cause_v1.Lease` implementation with its checked-in base `lease.py`, verifies that it has `intent_token` and no `token`, and checks that generated explicit-up and bulk-release telemetry use that value. A decoy legacy `token` value is also rejected in favor of `intent_token`.

## H/T/D/C/U

- **H:** Measurement events can bind to the runtime's actual accepted intent identity without changing input admission, explicit release order, cleanup behavior, or the owner result.
- **T:** Run the copied original construction suite plus the new actual-Lease regression on the frozen input owner and lease sources. Perform a separate AST/source audit of generated telemetry helpers.
- **D:** The construction suite and source audit pass; retain this as a scoped identity-binding correction only.
- **C:** A correct source field does not attest to the loaded production bytes, event sink/clock behavior in every live branch, physical release, independently useful feedback, recovery, or task value.
- **U:** Existing formal X11 A01 is consumed and was not rerun. Fresh native validation remains subject to resource assignment, a new freeze and independent review.

## First outcomes and validation

1. The first 14-test run passed the focused actual-Lease test and 12 builder controls; one inherited command-construction assertion failed because its expected `/out` and `/fixtures/...` literals were POSIX-only. The runtime command had host-native paths. This was a test portability issue; it is retained in `ATTEMPTS.md`.
2. After adding the original import-probe tests, the next run had 3 failures: the same fixture-path expectation plus two missing `probe_imports.py` package-data errors. No candidate runtime test failed.
3. The expected fixture paths were normalized using `Path.resolve()`, and the exact retained import probe was added. The final local command below passed all 16 tests.

```powershell
python -B -m unittest discover -s research/doom/owner_measurement_59_intent_token_successor_I80 -v
```

The full test stdout/stderr is in `CONSTRUCTION_CI.txt`. `audit_source.py` is a distinct same-worker audit of the frozen source pin and the generated AST; its result is in `SOURCE_AUDIT.txt`. No game, GUI, X11, model, GPU, live input, or formal allocation ran.
