# Source-first freeze: Issue #706

Task: XI2-RELEASE-VS-ABORT-TK-20260917-001.
Immutable publication base: d84027ebd94a786b2143e25e52fe1504deb85ee7.
No formal case has executed at this commit.

The seven binary parts concatenate, in numeric order, to an exact 9,323-byte gzip tar archive, SHA-256 e8b54c80b36ed2338eb0103bffe5fdbc7202eb4a44d1eb1abad4e55c0c3ab1d3. They contain source/fixture.py, source/retained_transport.py, source/run_case.py, source/audit.py, source/plan.json, source/environment.json and source/FREEZE.json. FREEZE.json SHA-256 is 824bcfb57369454daaecd0d6fd5ca2f569efb29a5cbeb339d08f9c86004a807d.

```sh
cat source-freeze.part??.bin > source-freeze.tar.gz
printf '%s  %s\n' e8b54c80b36ed2338eb0103bffe5fdbc7202eb4a44d1eb1abad4e55c0c3ab1d3 source-freeze.tar.gz | sha256sum -c -
tar -xzf source-freeze.tar.gz
```

All seven returned Git blob identities match locally computed blob hashes before formal execution. A preceding truncated single-blob transfer was detected by a blob mismatch and was not referenced by this tree. No source or scientific condition was changed to repair publication.

The experiment distinguishes physical/server input neutrality from application effect. The ordinary Tk Button class binding is not replaced, and only its command callback changes the visible effect marker. Retained #655 Authority/TouchAdapter class bodies are unchanged. One private Xorg and one Tk process per first case; no shared runtime, workflow, release or user-data mutation. Twelve cases total, three per scenario, one outer invocation each, no same-ID reruns. Exact order and decision are in source/plan.json.
