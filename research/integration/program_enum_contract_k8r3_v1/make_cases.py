"""Deterministic JSON fixtures; imports no runtime or candidate."""
from copy import deepcopy
import json
from pathlib import Path


def cases():
    invalid = [None, False, 0, 1.5, '', 'sentinel-k8r3', [], {},
               ['sentinel-k8r3'], {'tag': 'sentinel-k8r3'}]
    tokens = {'observe': ['screen_physical_px', 'screen_logical', 'window_client'],
              'pointer_move': ['screen_physical_px', 'screen_logical', 'window_client'],
              'pointer_button': ['left', 'middle', 'right', 'x1', 'x2']}
    prefixes = {'plain': [], 'repeat': [{'op':'key_chord','keys':['Tab'],'repeat':2}],
                'gap': [{'op':'text','text':'abc','gap_ms':1}]}
    result = []
    for mode, prefix in prefixes.items():
        for kind, valid in tokens.items():
            for i, value in enumerate(invalid + valid):
                op = {'op':kind}
                if kind == 'pointer_button':
                    op.update(button=value, down=True)
                else:
                    op.update(frame=value, x=0, y=0)
                    if kind == 'observe':
                        op.update(w=1, h=1)
                p = {'schema':'agent-interface/program-v1','program_id':'enum-check',
                     'source':{'observation_seq':1,'binding_revision':1},
                     'authority':{'lease_id':'test-only','expires_at_ns':100},
                     'terminal':{'release_all_required':True},
                     'ops':deepcopy(prefix)+[op,{'op':'release_all'}]}
                result.append({'id':f'{mode}-{kind}-{i:02d}', 'mode':mode,
                               'input':json.dumps(p, sort_keys=True, separators=(',', ':'))+'\n'})
    return result


if __name__ == '__main__':
    Path(__file__).with_name('cases.json').write_text(json.dumps(cases(), indent=2)+'\n')
