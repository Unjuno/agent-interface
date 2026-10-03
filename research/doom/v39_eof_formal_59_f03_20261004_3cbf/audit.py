"""Independent row semantics, not formal receipt/custody qualification yet."""
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
    return 'VERIFIED_SAVED_PIPE_RECORD'


def check_rows(rows):
    cases = ['baseline_eof', 'candidate_eof', 'candidate_events_eof', 'candidate_json']
    require([row['case'] for row in rows] == cases, 'case cardinality/order')
    for index, row in enumerate(rows):
        require(row['pins'] == PINS, 'source pins')
        require(clock(row['start_ns']) and clock(row['end_ns']) and row['start_ns'] < row['end_ns'], 'cell clock')
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
    return 'VERIFIED_CONSTRUCTION_ROWS'
