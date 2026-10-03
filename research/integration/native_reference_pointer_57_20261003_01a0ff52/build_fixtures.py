"""Finite engineering inputs, fixed before the first matrix invocation."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OBS = {'sequence': 7, 'native': {'payload': 'retained observation'}}
MARKER = {'observation_ref': '/native_result/observation'}
TOKENS = ['0','1','2','3','-1','-2','-0','00','01','+0','+1',' 0','0 ','٠','１','1.0','1e0','-','', 'a~2b','a~','~01','a~1b~0c']


def build():
    cases = []
    def add(kind, rows, token, schema):
        path = '/native_result/rows/' + token
        view = {'schema': schema, 'reference_scope': 'synthetic exact-location test',
                'observation_references': [path] if '-v1-' in schema else {path: '/native_result/observation'},
                'native_result': {'observation': OBS, 'rows': copy.deepcopy(rows)}}
        cases.append({'id': str(len(cases)), 'kind': kind, 'view': view})
    for schema in ('agent-interface/native-receipt-v1-observation-refs',
                   'agent-interface/native-receipt-v2-observation-refs'):
        for length in (0, 1, 3):
            for token in TOKENS:
                add('array-' + str(length), [MARKER] * length, token, schema)
        for token in TOKENS:
            # Dictionary keys are strings: '-1' and '00' are valid keys here.
            key = token.replace('~1', '/').replace('~0', '~')
            add('dictionary', {key: MARKER}, token, schema)
        for scalar in (None, 3, 'literal', True):
            add('scalar-traversal', [scalar], '0/field', schema)
        add('missing-dictionary-key', {}, 'missing', schema)
    return cases


if __name__ == '__main__':
    with (ROOT / 'fixtures.json').open('x', encoding='utf-8') as stream:
        json.dump(build(), stream, ensure_ascii=False, indent=2)
        stream.write('\n')
