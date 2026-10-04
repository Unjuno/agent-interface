"""Explicit stdlib data reader; never import or rerun an MCP/experiment producer."""
import ast
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parent
STAGES = {
    'red-shutdown': (1, 4, 4, 0),
    'green-shutdown': (0, 4, 0, 0),
    'green-affected-mcp': (1, 103, 0, 1),
    'red-unshielded-teardown312': (1, 1, 1, 0),
    'red-shutdown312': (1, 4, 4, 0),
    'green-affected-mcp312': (0, 104, 0, 0),
    'red-preentry-cancellation312': (1, 2, 1, 0),
    'green-final-mcp312': (0, 106, 0, 0),
}

def require(value, message):
    if not value:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def pairs(rows):
    result = {}
    for key, value in rows:
        require(key not in result, 'duplicate JSON member')
        result[key] = value
    return result

def decode(data):
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

def case_rows(text):
    rows, pending = {}, None
    for line in text.splitlines():
        match = re.match(r'^(test_\w+) \(([\w.]+)\) \.\.\. (.*)$', line)
        if match:
            require(pending is None, 'unfinished prior test output')
            name, pending, tail = match.groups()
            require(pending.endswith('.'+name) and pending not in rows, 'duplicate/mismatched test identity')
            line = tail
        status = line.strip()
        if pending is not None and status in ('ok', 'FAIL', 'ERROR'):
            rows[pending], pending = status, None
    require(pending is None, 'unfinished last test output')
    return rows

def data_check(read):
    publication = decode(read('PUBLICATION.json'))
    mapped = {row['path']: row for row in publication['records']}
    results = {}
    for name, (code, count, failures, errors) in STAGES.items():
        receipt = decode(read(name+'.receipt.json'))
        require(type(receipt['exit_code']) is int and receipt['exit_code'] == code, name+' exit')
        require(type(receipt['expected_exit']) is int, name+' expected exit type')
        require(receipt['timed_out'] is False, name+' timeout')
        start, end = (datetime.fromisoformat(receipt[key]) for key in ('started_utc', 'ended_utc'))
        require(start.utcoffset() == end.utcoffset() == timedelta(0) and start <= end, name+' UTC order')
        for stream in ('stdout', 'stderr'):
            path = name+'.'+stream+'.txt'
            require(receipt[stream+'_sha256'] == mapped[path]['original_sha256'], name+' original stream join')
        text = read(name+'.stderr.txt').decode('utf-8')
        rows = case_rows(text)
        require(len(rows) == count, name+' complete test identities')
        require(sum(value == 'FAIL' for value in rows.values()) == failures, name+' failure count')
        require(sum(value == 'ERROR' for value in rows.values()) == errors, name+' error count')
        require(re.search(r'\bRan '+str(count)+r' tests? in ', text) is not None, name+' reported count')
        require(('\nOK\n' in text.replace('\r', '')) == (code == 0), name+' verdict')
        results[name] = dict(exit_code=code, methods=len(rows), failures=failures, errors=errors)
    identities = decode(read('TEST_IDENTITIES.json'))
    final = case_rows(read('green-final-mcp312.stderr.txt').decode('utf-8'))
    require(len(identities) == len(set(identities)) == 106 and set(identities) == set(final), 'final identity set')
    environment = decode(read('environment312.json'))
    packages = {item['name'].lower(): item['version'] for item in environment['packages']}
    require(environment['python'].startswith('3.12.14 ') and environment['platform'].startswith('Windows'), 'actual supported native runtime')
    for package, version in (('mcp', '1.30.0'), ('anyio', '4.14.2'), ('pydantic', '2.13.4')):
        require(packages[package] == version, 'actual SDK/dependency '+package)
    receipt = decode(read('green-final-mcp312.receipt.json'))
    normalization = decode(read('SOURCE_NORMALIZATION.json'))
    for row in normalization:
        path = row['path']
        snapshot = read('source-final/'+Path(path).name+'.txt')
        require(receipt['source_sha256'][path] == sha(snapshot) == row['executed_working_sha256'], 'executed final source join')
        normalized = snapshot.replace(b'\r\n', b'\n')
        require(ast.dump(ast.parse(snapshot), include_attributes=True) == ast.dump(ast.parse(normalized), include_attributes=True), 'source AST normalization')
        blob = hashlib.sha1(b'blob '+str(len(normalized)).encode()+b'\0'+normalized).hexdigest()
        require(sha(normalized) == row['committed_lf_sha256'] and blob == row['git_blob'], 'committed source identity')
    baseline = read('source-red/mcp_server.py.txt').replace(b'\r\n', b'\n')
    require(hashlib.sha1(b'blob '+str(len(baseline)).encode()+b'\0'+baseline).hexdigest() ==
            '05f952d26c90d66ccc2af3b24dd4704e0ffd596e', 'preserved original server blob')
    dependencies = decode(read('DEPENDENCIES.json'))['files']
    require(len(dependencies) == 133 and sum(row['changed'] is True for row in dependencies) == 2,
            'bounded dependency/change set')
    require({row['path'] for row in dependencies if row['changed']} ==
            {'runtime/cli_v1/mcp_server.py', 'runtime/cli_v1/test_mcp_session.py'}, 'exact code delta')
    return dict(stages=results, final_methods=106, dependency_files=133,
                formal_allocations=0, qualification='data/source/receipt consistency only; no authentication or runtime rerun')

def verify(root=ROOT):
    manifest = decode((root/'MANIFEST.json').read_bytes())
    expected = set()
    for row in manifest['files']:
        path = row['path']
        parts = PurePosixPath(path)
        require(not parts.is_absolute() and '..' not in parts.parts and path not in expected, 'manifest path')
        expected.add(path)
        data = (root/path).read_bytes()
        require(type(row['bytes']) is int and row['bytes'] == len(data) and row['sha256'] == sha(data), 'manifest bytes '+path)
    actual = {path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()}
    require(actual == expected | {'MANIFEST.json'}, 'manifest completeness')
    publication = decode((root/'PUBLICATION.json').read_bytes())
    for row in publication['records']:
        require(sha((root/row['path']).read_bytes()) == row['public_sha256'], 'public mapping '+row['path'])
        require(type(row['redacted']) is bool and row['redacted'] ==
                (row['original_sha256'] != row['public_sha256']), 'redaction qualification')
    return data_check(lambda path: (root/path).read_bytes())

if __name__ == '__main__':
    try:
        print(json.dumps(verify(), indent=2))
    except Exception as error:
        print(json.dumps(dict(status='HOLD_DATA_INCONSISTENCY', error=str(error))))
        raise SystemExit(1)
