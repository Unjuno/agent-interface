def choose(records, fields):
    if (type(records) is not list or len(records) != 2 or not fields or
            len(set(fields)) != len(fields) or any(f not in ('title', 'parent', 'anchor') for f in fields)):
        return None
    if any(type(r) is not dict or type(r.get('id')) is not int or r['id'] <= 1 for r in records):
        return None
    if len({r['id'] for r in records}) != len(records):
        return None
    if any(f not in r or type(r[f]) is not str for r in records for f in fields):
        return None
    matches = {r['id'] for r in records if any(r[f] == 'Target' for f in fields)}
    return next(iter(matches)) if len(matches) == 1 else None
