"""Read-only, explicit-window accounting of Codex per-response usage records.

Tool association is chronological, not provider-attested attribution. Costs and
isolated tool/image charges cannot be inferred from whole-context token usage.
"""
import argparse
import hashlib
import json

FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
          'output_tokens', 'reasoning_output_tokens', 'total_tokens')


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def validate_usage(value):
    if any(type(value.get(k)) is not int or value[k] < 0 for k in FIELDS):
        raise ValueError('Missing or invalid usage counter')
    if (value['cached_input_tokens'] > value['input_tokens'] or
            value['reasoning_output_tokens'] > value['output_tokens'] or
            value['total_tokens'] != value['input_tokens'] + value['output_tokens']):
        raise ValueError('Inconsistent usage counters')
    return {k: value[k] for k in FIELDS}


def project(lines, selection):
    if not selection or len({s['name'] for s in selection}) != len(selection):
        raise ValueError('Unique named windows required')
    begins = {s['begin_call_id']: s for s in selection}
    if len(begins) != len(selection):
        raise ValueError('Overlapping begin boundaries')
    windows, active, context, pending, seen = [], None, None, {}, {}
    response_windows = {}
    for index, line in enumerate(lines, 1):
        record = json.loads(line)
        payload = record.get('payload', {})
        kind = record.get('type')
        stamp = dict(source_line=index, timestamp=record.get('timestamp'),
                     source_sha256=digest(line))
        if kind == 'turn_context':
            context = {k: payload.get(k) for k in ('turn_id', 'model', 'effort')}
        if kind == 'response_item' and payload.get('type') == 'custom_tool_call':
            cid = payload['call_id']
            if cid in begins:
                if active is not None or any(w['name'] == begins[cid]['name'] for w in windows):
                    raise ValueError('Overlapping or repeated boundary')
                active = dict(begins[cid], begin=stamp, calls=[], usage_records=[],
                              duplicate_usage_records=0, cost_usd=None)
                windows.append(active)
                pending, seen = {}, {}
            if active is not None:
                if cid in pending or any(c['call_id'] == cid for c in active['calls']):
                    raise ValueError('Repeated tool call ID')
                entry = dict(stamp, call_id=cid, name=payload.get('name'),
                             input_sha256=digest(payload.get('input', '')),
                             context=context, response_ids=[])
                active['calls'].append(entry)
                pending[cid] = entry
        elif active is not None and kind == 'token_usage_record':
            rid = payload.get('response_id')
            if not isinstance(rid, str) or not rid:
                raise ValueError('Missing response identity')
            usage = validate_usage(payload.get('usage', {}))
            if rid in response_windows and response_windows[rid] != active['name']:
                raise ValueError('Response identity repeated across selected windows')
            response_windows[rid] = active['name']
            identity = (payload.get('turn_id'), usage)
            if rid in seen:
                if seen[rid] != identity:
                    raise ValueError('Conflicting response usage')
                active['duplicate_usage_records'] += 1
            else:
                seen[rid] = identity
            active['usage_records'].append(dict(stamp, response_id=rid,
                turn_id=payload.get('turn_id'), usage=usage, context=context))
            for entry in pending.values():
                if rid not in entry['response_ids']:
                    entry['response_ids'].append(rid)
        elif (active is not None and kind == 'response_item' and
              payload.get('type') == 'custom_tool_call_output'):
            cid = payload['call_id']
            if cid not in pending:
                raise ValueError('Unmatched tool output in selected window')
            pending.pop(cid)['output'] = dict(stamp,
                output_sha256=digest(json.dumps(payload.get('output'), ensure_ascii=False)))
            if cid == active['end_call_id']:
                if pending:
                    raise ValueError('Selected end leaves unfinished calls')
                active['end'] = stamp
                missing = [c['call_id'] for c in active['calls'] if not c['response_ids']]
                active['calls_without_usage'] = missing
                active['status'] = 'partial_usage' if missing else 'recorded_usage'
                totals = {k: sum(u[k] for _, u in seen.values()) for k in FIELDS}
                totals['uncached_input_tokens'] = totals['input_tokens'] - totals['cached_input_tokens']
                active['totals'] = totals if seen else None
                active = None
                if len(windows) == len(selection):
                    break
    if active is not None or len(windows) != len(selection):
        raise ValueError('Missing requested boundary')
    return dict(schema='primary-usage-projection-v2', windows=windows,
                scope='whole-context responses inside explicit execution windows',
                association='chronological; not provider-attested per-tool attribution',
                billing='unavailable; no price or isolated receipt/image charge inferred')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', required=True)
    parser.add_argument('--selection', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    with open(args.selection, encoding='utf-8') as source:
        selection = json.load(source)
    with open(args.session, encoding='utf-8') as source:
        result = project(source, selection)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    with open(args.output, 'x', encoding='utf-8') as target:
        target.write(encoded)


if __name__ == '__main__':
    main()
