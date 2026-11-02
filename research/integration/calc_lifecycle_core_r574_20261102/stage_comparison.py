"""Stage archived three-arm inputs for inspection; this is not a live launcher."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import unicodedata
import zipfile

ARCHIVE_PATH = 'research/integration/wslc_calc_three_arm_obstruction_20261101/raw.zip'
ROUTES = ('direct', 'compiled', 'fresh')
LIMIT = 8 * 1024 * 1024


def _safe_name(name):
    if not isinstance(name, str) or '\\' in name or ':' in name:
        raise ValueError('unsafe archive path')
    p = PurePosixPath(name)
    if p.is_absolute() or any(x in ('', '.', '..') for x in p.parts) or str(p) != name:
        raise ValueError('unsafe archive path')
    return name


def _validate_names(names):
    canonical = []
    for name in names:
        _safe_name(name)
        parts = PurePosixPath(name).parts
        for part in parts:
            if (part.endswith((' ', '.')) or any(ord(c) < 32 or c in '<>"|?*' for c in part)
                    or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])', part.split('.')[0])):
                raise ValueError('unsafe Windows filename')
        key = tuple(unicodedata.normalize('NFC', part).casefold() for part in parts)
        for other in canonical:
            if key[:len(other)] == other or other[:len(key)] == key:
                raise ValueError('colliding archive paths')
        canonical.append(key)


def stage_archive(blob, destination, *, commit):
    if not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('full git commit required')
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    route_hashes, source_files, conditions = {}, {}, {}
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate archive member')
        def read(name):
            try: info = z.getinfo(name)
            except KeyError as exc: raise ValueError('missing archive member') from exc
            if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16) or info.file_size > LIMIT:
                raise ValueError('invalid archive member')
            return z.read(info)
        for index, route in enumerate(ROUTES, 1):
            base = f'eq{index:02d}'
            condition = json.loads(read(base + '/conditions.json'))
            if condition.get('allocation') != base or condition.get('route') != route or condition.get('values') != ['472','615']:
                raise ValueError('unexpected comparison conditions')
            entries = condition.get('input_sha256')
            if not isinstance(entries, dict) or not entries or len(entries) > 100:
                raise ValueError('invalid input manifest')
            _validate_names(entries)
            verified = {}
            for name, expected in entries.items():
                _safe_name(name)
                if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):
                    raise ValueError('invalid input digest')
                content = read(base + '/' + name)
                actual = hashlib.sha256(content).hexdigest()
                if actual != expected:
                    raise ValueError('input digest mismatch: ' + name)
                verified[name] = actual
                if index == 1: source_files[name] = content
            route_hashes[route] = verified
            conditions[route] = condition
    if any(set(route_hashes[x]) != set(route_hashes['direct']) for x in ROUTES):
        raise ValueError('route input sets differ')
    receipt = {'source_commit':commit,'archive_path':ARCHIVE_PATH,
               'archive_sha256':hashlib.sha256(blob).hexdigest(),
               'staged_route':'direct','route_input_hashes':route_hashes,
               'conditions':conditions,'live_ready':False}
    destination.mkdir(parents=False,exist_ok=False)
    for name, content in source_files.items():
        target = destination / 'inputs' / name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    (destination/'manifest.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    return receipt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--commit',required=True)
    parser.add_argument('--destination',required=True)
    args=parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.commit):parser.error('commit must be a full lowercase SHA-1')
    blob=subprocess.run(['git','show',args.commit+':'+ARCHIVE_PATH],capture_output=True,check=True).stdout
    result=stage_archive(blob,args.destination,commit=args.commit)
    print(json.dumps({'archive_sha256':result['archive_sha256'],'input_count':len(result['route_input_hashes']['direct']),'live_ready':False}))

if __name__ == '__main__':main()
