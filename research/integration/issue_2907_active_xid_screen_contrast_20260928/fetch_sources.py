"""Fetch and verify only the pinned public-X11 source closure into /src."""
import hashlib
import json
from pathlib import Path

import httpx


COMMIT = '2dadbde96a3774614f0dff8b51f95dbef9d05716'
ROOT = Path('/src')
EXPECTED = {
    'research/live_control/coordinate_frame_transform_v1.py': 'cb6aefeaa4e9a41b4f4b9ca532e24106025247e39e7c7ee026ddc242a7cbb05b',
    'research/live_control/native_handle_bridge_v1.py': '451678e42ed8262d61abf6dda834a946bd87c6e06f5b3cf1ca5c68353ed67456',
    'research/live_control/native_tail_v1.py': '95a9da71623e896e4a623bd2a246e5dcb73aa4c0e65e87ce86edcb74fb6dc9b5',
    'research/live_control/scoped_target_handle_v1.py': '550d377f145abbb16f8466dc91b5bb84ca25fccadf71e4d24b2f426550f5a19f',
    'research/live_control/scoped_target_handle_v2.py': '11fa315eb333a022ed09f56059c0d91963586184ba89534a177453048fb40e67',
    'research/live_control/scoped_target_handle_v3.py': '05da09752a051713dc9c344cd8b40a97718e2c07378dd28b258fc986b07f0dcb',
    'runtime/backends/quartz_v1/backend.py': 'a265b6501f5de3cc3e9fce7c037e36db39716f7dbaac5f5bdc69289081d85866',
    'runtime/backends/quartz_v1/session.py': 'bd8fee0f5d36fce746d97a998ffd77f6b9b16f83d067a0009799614f3c2a35bd',
    'runtime/backends/win32_v1/backend.py': '4cf87d6cecab9a84c4e9cdce83adbe8b58f93227eb64526740c029342bbdd6dd',
    'runtime/backends/win32_v1/session.py': '7e81a5b5cec01dc43da7a0ff4acebd0dd33bd67b9dd7c600ced431f61166af77',
    'runtime/backends/x11_v1/backend.py': 'bbdf1a6c474ad488dce9110a8deb025498b5bc820ad53261de6eb3110245a118',
    'runtime/backends/x11_v1/capture_artifacts.py': '03aa32ad615595ece5b45b147cf550bb6a39e34e7e4db151e3cca4fd23266688',
    'runtime/backends/x11_v1/session.py': '70ffb0167a70efcf629221c8236dd19ba9fbc2ff3ffc18454f13a0f656b86a93',
    'runtime/cli_v1/api.py': '9ff9c5c1d7050d4769416380f8bbb0618b67220570e96c6f00372e368e94be50',
    'runtime/cli_v1/observe.py': '853c25aa1f2125810e7e19e416165c8c3f5efe65786e9287df99c1da3ad05f46',
    'runtime/core_v1/contract.py': 'f053f73ccdeb67175068bf4d663bd484d886beb83305ed679510292809afd536',
    'runtime/core_v1/sequence.py': '20fd121ec7d54c0c0318fa1415bff49ff18808808b35cd902cd4435fb671b391',
    'runtime/selector_v1/__init__.py': '66bc2fcb2797b108cd739b1c000352932dbdd7a16c186c1104cd8d26d0645881',
    'runtime/selector_v1/selector.py': '7f3db522b2250fcd3d8960c87b1d87ad078bf1b2b565900b4210836f6b7ca764',
}


def main():
    existing = []
    missing = []
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        if path.exists():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != expected:
                raise SystemExit(f'pre-existing source differs; refusing overwrite: {relative}')
            existing.append(relative)
        else:
            missing.append(relative)

    fetched = {}
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for relative in missing:
            url = f'https://raw.githubusercontent.com/Unjuno/agent-interface/{COMMIT}/{relative}'
            response = client.get(url)
            response.raise_for_status()
            data = response.content
            digest = hashlib.sha256(data).hexdigest()
            if digest != EXPECTED[relative]:
                raise SystemExit(f'pinned source digest mismatch: {relative}: {digest}')
            fetched[relative] = data

    # Write only after every response has passed its frozen digest check.
    for relative, data in fetched.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_bytes(data)
        temporary.replace(path)

    rows = []
    for relative, expected in sorted(EXPECTED.items()):
        data = (ROOT / relative).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise SystemExit(f'post-write source mismatch: {relative}')
        rows.append({'path': relative, 'bytes': len(data), 'sha256': actual})
    manifest = {'source_commit': COMMIT, 'files': rows,
                'existing_verified': sorted(existing),
                'downloaded_now': sorted(fetched)}
    (ROOT / 'source_manifest.json').write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'verified_files': len(rows),
                      'downloaded': len(fetched), 'existing_verified': len(existing),
                      'source_commit': COMMIT}, sort_keys=True))


if __name__ == '__main__':
    main()
