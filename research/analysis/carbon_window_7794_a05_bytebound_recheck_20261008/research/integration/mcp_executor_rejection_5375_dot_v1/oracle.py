"""Independent raw-only diagnostic auditor; no runtime/runner imports."""
import hashlib
import json
from pathlib import Path


def metadata(result):
    if result.get('kind') != 'return':
        return None
    value = result['value']
    blocks = value['content']
    if type(value['isError']) is not bool or len(blocks) != 1 or blocks[0]['type'] != 'text':
        raise ValueError('unexpected MCP envelope')
    row = json.loads(blocks[0]['text'])
    if type(row) is not dict:
        raise ValueError('metadata is not an object')
    return row


def audit(raw, root=None):
    errors = []
    def require(condition, name):
        if not condition:
            errors.append(name)
    disposition = 'STOP_INTEGRITY'
    try:
        require(raw['schema'] == 'mcp-preworker-original-v1', 'schema')
        require(raw['source_unchanged'] is True, 'source_changed')
        require(raw['tripwire_calls'] == [], 'native_tripwire')
        for key, count in [('public_close_calls', 4), ('public_list_calls', 4), ('executor_probe_calls', 1)]:
            require(type(raw[key]) is int and raw[key] == count, key)
        require(raw['health_probe']['completed'] is True and
                raw['health_probe']['value'] == 'healthy-executor', 'replacement_executor_unproven')
        rows = raw['rows']
        labels = ['healthy_close', 'rejected_close', 'recovered_close', 'fresh_close']
        require([r['label'] for r in rows] == labels, 'row_schedule')
        if len(rows) != 4:
            return {'errors': errors, 'disposition': disposition}
        for row in rows:
            require(row['tool'] == 'interface_close' and row['arguments'] == {}, 'request_' + row['label'])
            require(type(row['invoke_entries']) is int and row['invoke_entries'] >= 0, 'entry_type')
            ledger = metadata(row['ledger'])
            require(row['ledger']['value']['isError'] is False and ledger['status'] == 'call_list'
                    and ledger['scope'] == 'current_server' and ledger['operation_invoked'] is False
                    and ledger['next_before_call_id'] is None, 'ledger_' + row['label'])
            require(type(ledger['total_calls']) is int and ledger['total_calls'] == len(ledger['calls']), 'ledger_count')
            require(all(c['operation'] == 'close' and c['state'] == 'finished' for c in ledger['calls']), 'ledger_rows')
            inventory = row['inventory']
            require(type(inventory) is dict and all(type(v['bytes']) is int and v['bytes'] >= 0
                and isinstance(v['sha256'], str) and len(v['sha256']) == 64 for v in inventory.values()), 'inventory_shape')
            if root is not None:
                location = row['server_directory']
                require(location in ('healthy', 'rejection', 'fresh'), 'server_directory')
                # Rejection before/after inventories must both be empty in the observed-failure branch.
                folder = Path(root) / location
                actual = {str(p.relative_to(folder)): {'bytes': p.stat().st_size,
                    'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                    for p in sorted(folder.rglob('*')) if p.is_file()}
                if row['label'] != 'rejected_close':
                    require(actual == inventory, 'disk_' + row['label'])
        def closed(row):
            value = metadata(row['result'])
            return value is not None and row['result']['value']['isError'] is False and all((
                value.get('status') == 'closed', value.get('authority_granted') is False,
                value.get('restart_allowed') is False, value.get('release_attempted') is False,
                value.get('connection_close_attempted') is False,
                value.get('session', {}).get('state') == 'closed'))
        for index in (0, 3):
            row = rows[index]
            require(closed(row) and row['invoke_entries'] == 1 and len(row['inventory']) == 3
                    and metadata(row['ledger'])['total_calls'] == 1, 'healthy_control_' + row['label'])
        rejected = rows[1]
        reason = rejected['result']
        rejection_text = reason.get('message', '') if reason.get('kind') == 'exception' else json.dumps(reason)
        require('cannot schedule new futures after shutdown' in rejection_text, 'executor_rejection_not_exposed')
        require(rejected['invoke_entries'] == 0 and rejected['inventory'] == {}
                and metadata(rejected['ledger'])['total_calls'] == 0, 'rejection_started_operation')
        recovered = rows[2]
        row = metadata(recovered['result'])
        if row and row.get('status') == 'busy':
            require(recovered['result']['value']['isError'] is True and row.get('operation_invoked') is False
                and recovered['invoke_entries'] == 0 and recovered['inventory'] == {}
                and metadata(recovered['ledger'])['total_calls'] == 0, 'busy_evidence')
            disposition = 'FAIL_PREWORKER_CAPACITY_RELEASE'
        elif closed(recovered):
            require(recovered['invoke_entries'] == 1 and len(recovered['inventory']) == 3
                and metadata(recovered['ledger'])['total_calls'] == 1, 'recovery_evidence')
            disposition = 'PASS_PREWORKER_CAPACITY_RELEASE_SCOPED'
        else:
            errors.append('unexpected_recovery_result')
        if 'profile_events' in raw:
            events = raw['profile_events']
            for row in rows:
                count = sum(e['label'] == row['label'] and e['function'] == 'invoke'
                            and e['operation'] == 'close' for e in events)
                require(count == row['invoke_entries'], 'profile_count_' + row['label'])
            require(len(events) == sum(r['invoke_entries'] for r in rows), 'profile_total')
        else:
            errors.append('missing_profile')
        if root is not None:
            journal = [json.loads(line) for line in (Path(root) / 'EVENTS.jsonl').read_text().splitlines()]
            starts = [x for x in journal if x['kind'] == 'public_call_started']
            ends = [x for x in journal if x['kind'] == 'public_call_completed']
            expected_labels = [label for main in labels for label in (main, main + '_list')]
            require([x['label'] for x in starts] == expected_labels, 'journal_start_schedule')
            require([x['label'] for x in ends] == expected_labels, 'journal_end_schedule')
            require(sum(x['tool'] == 'interface_close' for x in starts) == raw['public_close_calls'], 'journal_close_count')
            require(sum(x['tool'] == 'interface_results' for x in starts) == raw['public_list_calls'], 'journal_list_count')
            require(sum(x['kind'] == 'executor_health_probe_completed' for x in journal) == raw['executor_probe_calls'], 'journal_probe_count')
            by_label = {x['label']: x['result'] for x in ends}
            for row in rows:
                require(by_label.get(row['label']) == row['result'] and
                        by_label.get(row['label'] + '_list') == row['ledger'], 'journal_response_' + row['label'])
    except (KeyError, TypeError, ValueError, OSError) as error:
        errors.append('malformed:' + type(error).__name__ + ':' + str(error))
    return {'errors': errors, 'disposition': 'STOP_INTEGRITY' if errors else disposition}
