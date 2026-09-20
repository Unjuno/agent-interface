import hashlib
import json
import os
from pathlib import Path
from unittest import mock

ROOT = Path('/work/source')
OUT = Path('/work/out')
COMMIT = '4d51fccac55433570bc714cfaf21c88531fe325d'
TREE = '7fae16c1766a36376d6c49f49a7fb0e68f93cb0d'
IMAGE = 'sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
FREEZE = 'd8cc8f36b1423c6a84bdcee4034c669d4e694b1e4c2a77c482e87a075f181861'
FILES = {
    'runtime/cli_v1/api.py': 'c402025700481d5cc0ba600f39bc83136be173f0',
    'runtime/cli_v1/review.py': '839ed09a749d675b18c317704a123e18e695c97f',
    'runtime/cli_v1/test_cli.py': 'b376bbd3878baa008b0301bdfe055cff81417e73',
    'runtime/core_v1/contract.py': '0206e6b170134dfdd05225cfbfb7b2a5bc26902c',
    'runtime/core_v1/backend.py': 'd00e5508f824bbb530fa67d2089b24572d5a9ef3',
    'runtime/core_v1/__init__.py': '659531954db218d4c04849fe937df80ad1fcf495',
    'runtime/core_v1/sequence.py': 'af7951e6b70193411b464e56c39c9c6dd7a4cd7e',
    'runtime/core_v1/platform_probe.py': '8fe6982c95fb385986114017bc0f9fcc8fd4dca9',
    'runtime/selector_v1/__init__.py': '1a09fab9f2f67777decfe2373b0108f3a2609678',
    'runtime/selector_v1/selector.py': '16c8994569172cd9498c18a0228016ef005ba44c',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data):
    import hashlib as h
    return h.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def main():
    assert os.environ.get('OBSTAC_SOURCE_COMMIT') == COMMIT
    assert os.environ.get('OBSTAC_SOURCE_TREE') == TREE
    assert os.environ.get('OBSTAC_IMAGE_ID') == IMAGE
    assert os.environ.get('OBSTAC_FREEZE_SHA256') == FREEZE
    assert os.environ.get('OBSTAC_DOCKER_CONTEXT') == 'orbstack'
    assert os.environ.get('OBSTAC_PLATFORM') == 'linux/arm64'
    source_manifest = {}
    for rel, expected in FILES.items():
        data = (ROOT / rel).read_bytes()
        assert git_blob_sha(data) == expected, rel
        source_manifest[rel] = {'git_blob_sha': expected, 'sha256': sha(data)}

    import sys
    sys.path.insert(0, str(ROOT))
    from runtime.cli_v1.api import dispatch

    base = {'schema': 'agent-interface/program-v1', 'program_id': 'obstac-3850',
            'source': {'observation_seq': 1, 'binding_revision': 0},
            'authority': {'lease_id': 'fixture-only', 'expires_at_ns': 100},
            'terminal': {'release_all_required': True}, 'ops': []}
    cases = [
        ('region_shape', {'op':'observe','frame':'window_client','region':[0,0,400,180]}, 'observe x must be int'),
        ('width_height_shape', {'op':'observe','frame':'window_client','x':0,'y':0,'width':400,'height':180}, 'observe w must be int'),
        ('valid_program_backend_refusal', {'op':'observe','frame':'window_client','x':0,'y':0,'w':400,'h':180}, None),
        ('unsupported_op_no_echo', {'op':'untrusted-' * 250}, 'unsupported operation'),
    ]
    rows = []
    for name, operation, expected_detail in cases:
        program = {**base, 'ops':[operation, {'op':'release_all'}]}
        before = json.loads(json.dumps(program))
        refusal = {'status':'refused','error':'INVALID_PROGRAM','backend_emissions':0}
        session = mock.Mock()
        session.dispatch.return_value = refusal.copy()
        with mock.patch('runtime.cli_v1.api.open_session', return_value=session) as opened:
            result = dispatch(program, {'fixture':1}, current_observation_seq=1,
                              current_binding_revision=0)
        opened.assert_called_once()
        session.dispatch.assert_called_once()
        session.backend.close.assert_called_once()
        assert program == before
        assert result['status'] == 'returned'
        actual = result['result']
        assert actual['status'] == 'refused' and actual['error'] == 'INVALID_PROGRAM'
        assert actual['backend_emissions'] == 0
        assert actual.get('detail') == expected_detail
        if expected_detail is None:
            assert 'detail_source' not in actual
        else:
            assert actual['detail_source'] == 'program_validation'
        serialized = json.dumps(result)
        assert 'untrusted-' not in serialized
        rows.append({'case':name, 'input_sha256':sha(json.dumps(program,sort_keys=True).encode()),
                     'returned':result, 'dispatch_count':1, 'close_count':1,
                     'backend_emissions':0, 'input_unchanged':True})
    kind = os.environ.get('OBSTAC_RUN_KIND')
    assert kind in ('construction', 'formal')
    raw = {'schema':'issue-3850-obstac-raw-v1','source_commit':COMMIT,
           'source_tree':TREE,'source_manifest':source_manifest,'rows':rows,
           'formal':kind == 'formal','kind':kind}
    data = (json.dumps(raw, sort_keys=True, separators=(',',':'))+'\n').encode()
    (OUT/('construction.json' if kind == 'construction' else 'raw.json')).write_bytes(data)
    print(json.dumps({'rows':len(rows),'raw_sha256':sha(data),'status':'ROWS_COMPLETE'}))


if __name__ == '__main__':
    main()
