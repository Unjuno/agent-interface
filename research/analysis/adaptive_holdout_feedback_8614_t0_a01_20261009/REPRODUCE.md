# Reproduce the retained audit

The frozen candidate was invoked once using the command in `FREEZE.json`; its exact JSON output was then losslessly compressed for repository storage. Verify the compressed artifact and recover the exact candidate bytes with:

```sh
gzip -t raw/candidate.json.gz
gzip -cd raw/candidate.json.gz > /tmp/8614-candidate.json
shasum -a 256 /tmp/8614-candidate.json
```

The decompressed digest must match `SHA256SUMS`. To independently rerun the read-only audit from the retained data:

```sh
python3 src/auditor.py input/fixture.json /tmp/8614-candidate.json /tmp/8614-audit.json
cmp audit/audit.json /tmp/8614-audit.json
```

This reproduces the audit only; it does not rerun the candidate. Do not use the formal seeds for another candidate invocation.
