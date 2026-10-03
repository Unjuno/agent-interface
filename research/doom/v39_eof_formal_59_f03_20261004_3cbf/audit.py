"""Independent row semantics, not formal receipt/custody qualification yet."""
import json
PINS = {
    'candidate': '2b569e6697720bef1f9d0381af6bc4876770132f26e418f697f136c40fc8a1a1',
    'helper': '8359de6a8c714eabc08e88b6d22d51935be23fc3cfde5663fdc85bf44d1d1ae0',
    'archive': 'd1ad6dcb8720b27766702361b4898d13259d2efe0b173e7d0fbc970fe3d988db',
}


def require(value, message):
    if not value:
        raise ValueError(message)


def clock(value):
    return type(value) is int and value > 0


def check_directory(directory):
    cases = ['baseline_eof', 'candidate_eof', 'candidate_events_eof', 'candidate_json']
    files = list(directory.iterdir())
    require({path.name for path in files} == {'SUMMARY.json', *(case + '.json' for case in cases)},
            'exact output inventory')
    require(all(path.is_file() and not path.is_symlink() for path in files), 'regular files only')
    rows = [json.loads((directory / (case + '.json')).read_text()) for case in cases]
    check_rows(rows)
    require(all(row.get('gate') is True for row in rows), 'producer gates')
    summary = json.loads((directory / 'SUMMARY.json').read_text())
    require(summary == {'cases': cases, 'retries': 0, 'model_calls': 0,
                        'verdict': 'PASS_SCOPED_PIPE_NOTIFICATION'}, 'summary consistency')
    require(type(summary['retries']) is int and type(summary['model_calls']) is int, 'integer counters')
    return 'VERIFIED_SAVED_PIPE_RECORD'


def check_rows(rows, *, historical=False):
    cases = ['baseline_eof', 'candidate_eof', 'candidate_events_eof', 'candidate_json']
    require([row['case'] for row in rows] == cases, 'case cardinality/order')
    previous_cell_end = 0
    for index, row in enumerate(rows):
        require(row['pins'] == PINS, 'source pins')
        require(clock(row['start_ns']) and clock(row['end_ns']) and row['start_ns'] < row['end_ns'], 'cell clock')
        require(row['start_ns'] > previous_cell_end, 'sequential cells')
        previous_cell_end = row['end_ns']
        if not historical:
            require(row.get('cleanup_child_alive') is False
                    and row.get('cleanup_reader_alive') is False, 'cleanup liveness')
        require(clock(row['child_pid']) and row['reader_alive'] is False and row['child_alive'] is True, 'liveness')
        require(type(row['cleanup_exit']) is int and row['cleanup_exit'] == -15
                and row['fatal'] is None and row['cleanup_faults'] == [], 'cleanup')
        require(len(row['waits']) == 2, 'wait cardinality')
        previous = row['start_ns']
        for wait in row['waits']:
            require(clock(wait['start_ns']) and clock(wait['end_ns'])
                    and previous <= wait['start_ns'] < wait['end_ns'] <= row['end_ns'], 'wait clocks')
            previous = wait['end_ns']
            require(wait['outcome'] == ('TimeoutError' if index == 0 else '_SessionReaderFailure')
                    and wait['cause'] == (None if index == 0 else 'JSONDecodeError' if index == 3 else 'EOFError'), 'outcome')
        if index == 2:
            require(row['ready'] == {'event': 'ready'} and row['terminal'] == {'event': 'terminal'}
                    and row['reader_alive_after_ready'] is True, 'event handshake')
            require(row['events'] == [{'event': 'ready'}, {'event': 'terminal'}], 'event order')
        else:
            require(row['events'] == [], 'unexpected events')
    require(len({row['child_pid'] for row in rows}) == 4, 'fresh children')
    return 'VERIFIED_HISTORICAL_CONSTRUCTION_ROWS' if historical else 'VERIFIED_CONSTRUCTION_ROWS'
