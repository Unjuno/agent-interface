"""Restore and verify the exact first-outcome Actions artifact; no experiment runs."""
from __future__ import annotations
import base64, hashlib, json, zipfile
from pathlib import Path

EXPECTED_ZIP_SHA256 = '1391709838769fe65da09c795470233fe27431f799141b165606669b76962cf5'
EXPECTED_MEMBERS = {
    'result.json': 'e6b99058f7d0424f51451cb7ebb0e418572c5f72a5c307e2fb6a0496b819c702',
    'summary.log': 'c830015b2d48b5beaa90f041b7f4d807b5feb1ed3775f0ce83c7ca2ac5f29d98',
    'audit.json': '88e2286f409d6ec79e97f5b392fc259cb8a0280d8eba0d4cfb79f9328bbfb22e',
}

def main() -> None:
    here = Path(__file__).resolve().parent
    encoded = ''.join(p.read_text().strip() for p in sorted(here.glob('evidence.zip.b64.part*')))
    data = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_ZIP_SHA256:
        raise SystemExit(f'zip sha mismatch: {digest}')
    out = here / 'restored-first-outcome.zip'
    out.write_bytes(data)
    with zipfile.ZipFile(out) as zf:
        if zf.testzip() is not None:
            raise SystemExit('zip CRC failure')
        actual = {}
        for name, expected in EXPECTED_MEMBERS.items():
            blob = zf.read(name)
            actual[name] = hashlib.sha256(blob).hexdigest()
            if actual[name] != expected:
                raise SystemExit(f'member sha mismatch: {name}')
        sums = zf.read('SHA256SUMS').decode()
        for name, expected in EXPECTED_MEMBERS.items():
            if f'{expected}  /tmp/occ443/{name}' not in sums:
                raise SystemExit(f'SHA256SUMS missing exact row for {name}')
    print(json.dumps({'status':'PASS_EVIDENCE_RESTORE','zip_sha256':digest,'members':actual}, indent=2))

if __name__ == '__main__':
    main()
