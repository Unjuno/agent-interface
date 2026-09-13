"""Remove only verified duplicates at known result locations; retain unknown data."""
import copy
import hashlib
import json
from shared_result_v1 import canonical, unique_pairs
from input_state_table_v1 import decode as states

ALIASES = {
    'image': (('image',), ('receipt', 'image')),
    'terminal': (('lifecycle', 'terminal'), ('receipt', 'terminals', 0, 'record')),
    'binding_terminal': (('receipt', 'program_binding', 'terminal'),
                         ('receipt', 'terminals', 0, 'record')),
}


def at(value, path):
    for key in path:
        value = value[key]
    return value


def build(data):
    value = json.loads(data, object_pairs_hook=unique_pairs)
    normalized = canonical(value).encode('utf-8')
    doc = copy.deepcopy(value)
    omitted = []
    for name, (target, source) in ALIASES.items():
        try:
            if canonical(at(doc, target)) != canonical(at(doc, source)):
                continue
            del at(doc, target[:-1])[target[-1]]
            omitted.append(name)
        except (KeyError, IndexError, TypeError):
            continue
    state_row = None
    try:
        observation = doc['lifecycle']['observation']
        rows = states(doc['state_table']['table'])
        matches = [(i, row) for i, row in enumerate(rows)
                   if canonical(row['sequence']) == canonical(observation['sequence'])]
        if len(matches) == 1:
            index, row = matches[0]
            fields = row['fields']
            if fields and set(fields) <= {'input_state_before', 'input_state_after',
                    'input_state_scope', 'owner_revision_unchanged'} and all(k in observation and canonical(observation[k]) == canonical(v)
                              for k, v in fields.items()):
                for key in fields:
                    del observation[key]
                state_row = index
    except (KeyError, IndexError, TypeError, ValueError):
        pass
    return dict(format='composed-result-v1', document=doc, omitted=omitted,
                observation_state_row=state_row,
                restored_sha256=hashlib.sha256(normalized).hexdigest(),
                scope='Known exact duplicates only; no authority or task-success inference.')


def decode(envelope):
    if envelope['format'] != 'composed-result-v1':
        raise ValueError('unsupported format')
    doc = copy.deepcopy(envelope['document'])
    names = envelope['omitted']
    if len(names) != len(set(names)) or any(n not in ALIASES for n in names):
        raise ValueError('invalid omission list')
    for name in names:
        target, source = ALIASES[name]
        parent = at(doc, target[:-1])
        if target[-1] in parent:
            raise ValueError('refusing to overwrite retained data')
        parent[target[-1]] = copy.deepcopy(at(doc, source))
    index = envelope['observation_state_row']
    if index is not None:
        if type(index) is not int or index < 0:
            raise ValueError('invalid state index')
        rows = states(doc['state_table']['table'])
        row = rows[index]
        observation = doc['lifecycle']['observation']
        if canonical(row['sequence']) != canonical(observation['sequence']):
            raise ValueError('state sequence mismatch')
        for key, value in row['fields'].items():
            if key in observation:
                raise ValueError('refusing to overwrite retained state')
            observation[key] = copy.deepcopy(value)
    digest = hashlib.sha256(canonical(doc).encode('utf-8')).hexdigest()
    if digest != envelope['restored_sha256']:
        raise ValueError('reconstruction mismatch')
    return doc
