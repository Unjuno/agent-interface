"""Compile explicit key repetition to the existing bounded native operation list."""
from copy import deepcopy


def expand_tail(tail, *, max_ops):
    if type(max_ops) is not int or not 0 <= max_ops <= 126:
        raise ValueError('native tail capacity must be 0..126')
    result = []
    for operation in tail:
        if not isinstance(operation, dict):
            raise ValueError('native tail operation must be an object')
        count = operation.get('repeat', 1)
        if 'repeat' in operation and operation.get('op') != 'key_chord':
            raise ValueError('repeat is supported only for key_chord')
        if type(count) is not int or not 1 <= count <= 126:
            raise ValueError('repeat must be an integer in 1..126')
        if len(result) + count > max_ops:
            raise ValueError('expanded tail exceeds native program capacity')
        item = {k: v for k, v in operation.items() if k != 'repeat'}
        result.extend(deepcopy(item) for _ in range(count))
    return result
