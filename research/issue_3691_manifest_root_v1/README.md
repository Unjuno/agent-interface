# Issue #3691 manifest trust-root reproduction

## H/T/D/C/U

- **H:** The Issue #3691 auditor compares raw and predecessor-freeze bytes to digests supplied by a caller-controlled study manifest. Replacing raw, freeze, and that manifest together can recover PASS even though all internal mutation checks reject their own challenges.
- **T:** Freeze and run the exact audit source, test source, predecessor raw, and predecessor FREEZE from current Issue #3691 branch HEAD `71ab9b6a0149695184282bc200cc544290fa42bb`. Compare canonical artifacts with coordinated replacements in a local temporary directory. Never edit predecessor evidence or the active PR branch.
- **D:** PASS_REPRODUCTION only if canonical input passes and the coordinated raw+freeze+manifest replacement also passes with unchanged exact source-file hashes. Reproduction is a scoped trust-root result, not Docker validation or a new XRes experiment.
- **C:** No Docker/container invocation, network, X11, GUI/input, model, formal allocation rerun, or mutation of Issue #3675/#3676/#3691 evidence and PR #3697 branch.
- **U:** Shows one concrete artifact-authentication gap; not arbitrary auditor unsoundness, runtime safety, or product reliability.

## Reproduce

Run from a clean checkout with Python 3.10+:

```bash
python research/issue_3691_manifest_root_v1/reproduce.py
```

The script verifies frozen SHA-256 values, runs the exact copied auditor against canonical inputs, then replaces both pixel digests, appends a space to the predecessor freeze, updates raw.freeze_sha256, and rewrites only the study manifest hashes. It prints both CLI results and all relevant digests. Fixed inputs are under `inputs/`; the captured outcome is `reproduction_output.json`.

## Frozen inputs and result

Source branch: `research/issue-3691-audit-integrity-v1`, HEAD `71ab9b6a0149695184282bc200cc544290fa42bb`. Each exact input is copied byte-for-byte under `inputs/` and pinned in `reproduce.py`:

- audit.py SHA-256 `0956b13a9e98c504c870096507b9428acae0510a27903d0eccb0f730af35c579`.
- test_integrity.py SHA-256 `15dbc3167b3d39dc622944bdf770c2c3d12036d23d9079c8cb80fbb628a98105`.
- raw.json SHA-256 `ccb9a75eefb7df73cb13dbc9191d33334fb672c2fd58fcc5fa32be998e182807`.
- predecessor_FREEZE.json SHA-256 `f40494b1be99fb1e68d7b09c498297df35a72c043740b5f09d3faec7e059acfe`.

Verified locally with Python 3.12. Both canonical and coordinated-replacement CLI invocations exited 0 with `PASS_OFFLINE_STRUCTURAL_AUDIT`, `errors=[]`, and all 11 built-in corruption controls true.

Replacement raw SHA-256 `32eea2e057b34ee0df624dbf5a07e76f3f57807ed55f0d957766a67693dc1377`; replacement freeze SHA-256 `529dbd8f6fbf1181606bb0eed7e1da3dcfe4267dcc8afb6eb023ec593fd9d640`; replacement manifest SHA-256 `c14c0fe1d573a94d2973a7228abd0c9ea6f00ff2de56b2a1a7645589331c76f2`. The replacement manifest retains the verified original auditor and test source hashes above. The earlier provisional manifest hash `d658774e…` is superseded and must not be used; it came from a discarded harness that used a placeholder test file.

## Decision and limitations

**PASS_REPRODUCTION_MANIFEST_TRUST_ROOT_GAP.** The manifest is used as authority for artifact and source digests but is never itself authenticated independently. A digest checked against a value stored only inside that same replaceable manifest is not a trust root. The repair needs a pinned expected study-manifest digest (or equivalent immutable manifest identity) outside the supplied file and a three-artifact substitution regression.

This remains native static audit evidence only. Docker Desktop on this host is still unresponsive; Issue #3691's isolated local Docker gate remains STOP. No Actions substitute, image pull, storage repair, GUI/input execution, or formal XRes allocation was run.