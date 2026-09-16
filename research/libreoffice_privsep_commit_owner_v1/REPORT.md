# LibreOffice privilege-separated pathname commit owner v1

Status: **RETAIN at a capability-separated local-file boundary; HOLD general GUI/production promotion.**

Immutable experiment BASE: `3c6f07f0660aee854d6b2d2d0f525fd9f451de68`.
Branch: `research/libreoffice-privsep-commit-owner-3c6f07f`.
Issue: #318.

## Question

Prior retained real-Calc work showed that native conflict prompting is both over-broad and bypassable when mtime is restored, advisory `flock` stays on an old inode, and Linux file leases do not protect an adversarial pathname `os.replace`. This rung asks one smaller question: if the GUI domain has **no OS write capability to the authoritative pathname**, can the controller become the only pathname publisher while Calc edits only a private staging file?

## Frozen mechanism

- real LibreOffice Calc 25.2.3.2 on private Xvfb/Openbox;
- exact retained Office/X11 policy blobs:
  - `backend_x11.py` Git blob `b4f8e043ce4f8929d446e038418ea0fd3655bab0`;
  - `office_backend.py` Git blob `3aeca10f62fb1366bcdd5fad561509cfcc0d91ab`;
- LibreOffice and adversarial writer run as unprivileged GUI UID 1001;
- staging/profile directory is GUI-owned and writable;
- authoritative target directory is UID 0, mode `0755`; target source is UID 0, mode `0644`;
- controller is UID 0 and alone performs final same-filesystem temp+fsync+`os.replace` publication.

The adversarial arm attempts `os.replace(external.xlsx, target.xlsx)` after the controller's plan-bound final target check and before publication. The frozen issue also requires a final recheck before publish. This is explicit OS capability separation, not a hidden application endpoint.

## First-outcome discipline

1. construction-01: setup-only Xauthority failure before Calc discovery; no scored row;
2. construction-02: stable construction passed after adding only an explicit controller Xauthority;
3. `c318-privsep-01`: **HARNESS FAIL / 0 scored arms** because the process-identity proof included the root `runuser` wrapper in the LibreOffice UID assertion;
4. `c318-privsep-02`: **INCOMPLETE**. Stable completed, adversarial writer returned EACCES, but parent JSON parsing failed on a literal `\\n` suffix before controller publication;
5. `c318-privsep-03`: source-frozen successor changed only that serialization detail and completed both arms once.

No rows from failed/incomplete IDs are pooled into the final pair.

## c318-privsep-03 result

| arm | Calc/staging | GUI-domain target replace | controller publish | final target | release |
|---|---|---|---|---|---|
| stable | `office / preview` | n/a | yes | `office / preview` | empty/verified |
| path_replace_attempt | `office / preview` | **EACCES (13)** | yes | `office / preview` | empty/verified |

Adversarial writer evidence:

- writer EUID: `1001`;
- `os.replace` result: `PermissionError(13, 'Permission denied')`;
- target inode/SHA after the failed writer attempt exactly match the plan-bound source;
- external source workbook remains present;
- actual `soffice.bin` process bound to the private profile has EUID 1001;
- controller publishes a new UID-0 target inode only after the target remains plan-valid.

The exact XLSX bytes differ between the two fresh arms because Office regenerated files independently; semantic scoring is `A1=office`, `A2=preview` in both.

## Audit

Independent `audit_v3.py` does not drive the GUI. It checks:

- exact retained backend Git blob identities;
- allocation/row structure;
- actual soffice EUID binding;
- root-owned non-group/world-writable authority directory;
- EACCES/EPERM writer refusal and unchanged target after the attempt;
- correct staging/final workbook cells;
- publication gates;
- verified empty X-server release.

Result: **2/2 rows pass, errors `[]`**. Four deliberate summary corruptions (writer errno, GUI UID, authority-dir mode, final cells) were independently rejected.

## H / T / D / C / U

**H.** Explicit OS write-capability separation can create the pathname ownership that old-inode guards could not: a GUI-domain writer cannot replace the authoritative target, while the controller can publish a valid staging result.

**T.** One frozen stable/adversarial pair with real Calc/XTEST, one unprivileged GUI principal, one root/controller publisher, independent XLSX scoring and release verification. No model call or user file.

**D.** PASS at this narrow capability boundary. The adversarial same-principal pathname replace is denied before target mutation, and both arms finish with the intended durable workbook. RETAIN as a mechanism candidate; do not promote to general GUI semantics.

**C.** The result may be largely ordinary Unix discretionary-access-control enforcement, not an application-specific property. That is the point of the boundary: protection comes from making the GUI domain unable to write the authoritative pathname. A privileged/same-controller-domain writer would escape this experiment.

**U.** One container/filesystem/LibreOffice version, controller runs as root, no real multi-user desktop policy, no network filesystem, no sandbox escape test, no same-UID deployment, no post-publication revocation, no crash/power-loss factor, no speed/rate claim. The frozen adversary is pathname replacement only; direct in-place writes are a separate one-factor successor if needed.

## Decision

**RETAIN** staging + explicit OS capability separation as one concrete way to instantiate an authoritative pathname commit owner in this local Linux fixture.

This does not make ordinary GUI Save atomic. It changes the architecture so the GUI never owns the authoritative target write capability; controller publication is the consequential commit.

## Successor rung — direct existing-inode write

The pathname-replacement result was not generalized by assumption. A separate frozen allocation tested a different GUI-domain write class: `open(target,'r+b')` followed by write/truncate/flush/fsync.

First outcomes before completion remain separate:

- `c318-privsep-04`: HARNESS FAIL / 0 scored arms because a relative output path created a relative GUI HOME and Openbox/Calc never became ready;
- `c318-privsep-05`: INCOMPLETE. Stable completed; the adversarial arm produced an incorrect staging edit (`A1=oldffice`) and fail-closed before the direct writer ran;
- `c318-privsep-06`: changed only post-window setup settle (0.6 s -> 1.5 s) plus fresh allocation/display identities and completed both arms once.

`c318-privsep-06` result:

- stable staging/final: `office / preview`, release empty/verified;
- direct-write arm: UID 1001 writer operation `inplace_r+b` failed with `EACCES (13)` before target mutation;
- target remained plan-valid through the writer attempt and controller recheck;
- controller publication succeeded; final target independently scored `office / preview`;
- independent audit: 2/2 rows, errors `[]`.

The executed v6 source is reconstructible from the exact retained v3 source plus `runner_v6_direct.patch`; the reconstruction was byte-compared to the executed local source and matches SHA-256 `f7e54e9d9f4495ea8d13968cffe182accc84015573213bd77ae965b0b95c78fe`.

**Refined decision:** under this UID/mode split, the tested GUI principal cannot mutate the authoritative target either by pathname replacement or by opening the existing inode for write. This strengthens the narrow capability-ownership interpretation. It still does not protect against a privileged/same-controller-domain writer or establish a deployable desktop sandbox.
