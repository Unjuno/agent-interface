# #3217 reconciliation result

## Decision

`PASS_CURRENT_MAIN_ARTIFACT_RECONCILED_SCOPED`

The prior `HOLD_CURRENT_MAIN_ARTIFACT_UNCONFIRMED` remains historically correct for the earlier repository state. The previously missing executable source and workflow artifact are now directly retrievable and have been independently reconciled.

## Source and artifact identity

Historical successful run: `35466506122`, head `6960809cdf9ccc2c2cda24ad84cab94c3cd2b4b6`.

Publication-base main: `2df540489fb3f810a1cbd220d0761ca7ec1b23d0`.

The following Git blobs are identical between the historical workflow head and publication-base main:

| Path | Git blob |
|---|---|
| `research/verification/known_postcondition_boundary_v1/experiment.py` | `0cd6b755cf54d8c01b254b2f8ee52610a29410f2` |
| `research/verification/known_postcondition_boundary_v1/audit.py` | `a234184fbb583911cea3a66d0eb01e4fe4ce894f` |
| `research/verification/known_postcondition_boundary_v1/Dockerfile` | `263520dc3ce3f10fbc4905b8893dad1946e5a9cf` |
| `.github/workflows/known-postcondition-boundary-3048.yml` | `32418aa8b5af29851d2a9f7ac0652bf5df07885b` |

Retained artifact 10590764445 is unexpired at reconciliation time. Its downloaded ZIP SHA-256 is exactly GitHub's recorded digest:

`863177586ae3d686c05b2c150967a9c426ef8d460b86ae5b8fc9a0243954b728`.

Members:

- `artifact/raw.json`: SHA-256 `ce1e0372f1f5c8387c0630436e5d1208f4e810c42711e544e3c4073f790534e0`, 90 rows.
- `artifact/audit.json`: SHA-256 `cb0d8ff3aa419bc15c423bd0331763be30f39eb80ad2423c913a9f981b242446`.

## Fresh source reconstruction check

The exact current-main `experiment.py` and retained `audit.py` source bytes were materialized and their Git blob IDs independently recomputed. In the provided Linux execution container (CPython 3.13.5), one fresh construction/provenance execution regenerated `raw.json` and `audit.json` byte-for-byte identical to the historical workflow artifact.

This is not claimed as Docker/Python-3.12 or Xvfb replication. It establishes deterministic source-to-artifact reconstruction for these files.

## Independent formal audit

The independent auditor SHA-256 is `08c93866d4d4b7b164527cf0f913dc385b9fc675581e1fc8134e4f2823b78752`. It imports neither candidate `experiment.py` nor historical `audit.py`.

One formal invocation returned exit 0 with:

- rows: 90;
- unique `{kind, scenario, policy}` identities: 90;
- independent errors: `[]`;
- rich-agent shadow calls: `RICH_AGENT_FIRST=30`, `DETERMINISTIC_FIRST=18`, `DETERMINISTIC_ONLY_FOR_KNOWN=12`;
- every candidate verdict and reason equal to the independent recomputation;
- no non-valid scenario classified `PASS_POSTCONDITION`;
- six corruption controls rejected 6/6.

Independent result SHA-256:

`f04db54fd37a0e84d88003365de6387385d9ba0fc236250345c0173224ab98f7`.

## H/T/D/C/U interpretation

The specific current-main source/artifact/reconciliation gap in #3217 is now resolved at this scoped synthetic-contract boundary. This does not turn the later GTK/X11 result into the same experiment, does not validate model behavior, and does not establish production efficiency or broad GUI correctness.

No historical row was rerun, replaced, pooled, or relabeled. The exact retained raw and audit members are included in this additive evidence directory so the reconciliation survives Actions artifact expiry.
