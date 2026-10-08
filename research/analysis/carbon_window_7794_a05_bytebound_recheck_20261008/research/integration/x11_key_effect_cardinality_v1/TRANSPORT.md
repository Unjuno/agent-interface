# Evidence storage and read-only replay

The complete lossless archive is stored as six ordered **binary** Git blobs,
`evidence.tar.xz.part00` through `part05`. This partition is only publication
transport, not an experimental split or another allocation. All eight frozen
source/plan/environment files are also readable directly in this directory.
The full report is [README.md](README.md); all raw rows, earlier construction
versions/failures and process exits are inside the assembled archive.

From a checkout of this directory, first assemble the archive with Python 3:

```sh
python - <<'PY'
import hashlib
import json
from pathlib import Path

manifest = json.loads(Path('ARTIFACTS.json').read_text())
expected_names = [f'evidence.tar.xz.part{i:02}' for i in range(6)]
assert [part['path'] for part in manifest['parts']] == expected_names
parts = []
for part in manifest['parts']:
    data = Path(part['path']).read_bytes()
    assert len(data) == part['bytes'], part['path']
    assert hashlib.sha256(data).hexdigest() == part['sha256'], part['path']
    parts.append(data)
archive = b''.join(parts)
assert len(archive) == manifest['archive_bytes']
assert hashlib.sha256(archive).hexdigest() == manifest['archive_sha256']
with Path('evidence.tar.xz').open('xb') as output:
    output.write(archive)
print('Verified archive:', len(archive), 'bytes')
PY
```

No Base64 decoding is needed after Git checkout: the parts are already binary.
An existing archive is not overwritten. The assembled SHA-256 must be
`ad0be00c312d5cca1714ab4b0f6d2d54b59e8619b2ea9088dc0a01cf6b8b636e`.
The manifest's `archive_git_blob` is the calculated Git object identity of the
assembled bytes, not a claim that a separate whole-archive Git blob is stored.

Continue with the **Read-only reproduction** commands in README.md. They verify
115 member hashes, replay the unchanged auditor, run four unittest methods and
twelve semantic corruption controls. `REPLAY_CHECK.json` records a successful
fresh-directory replay in the same provided container; the audit output was
byte-identical to the retained result. This is not independent human review,
external-environment replication or another live experiment. No X11 input is
needed for replay. Do not run the consumed live allocation again.

All formal source bytes remain those of commit
`f3c2c0a042db53394cd9d529c0c199ba235f60f3`. This transport guide and outer archive
manifest were added after the outcome; neither alters the frozen gates or raw
evidence. The archived README is byte-identical to the public result README.

Publication-only note: two local guide-writing commands failed on shell
here-document delimiters (first a parse error before writing; then a stray
trailing delimiter after writing and verification). A direct Python invocation
removed the shell-wrapper issue and tested the exact assembly snippet in a
fresh temporary directory. No experiment, archive, frozen source or scientific
gate was changed or rerun.
