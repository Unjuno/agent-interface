"""Versioned retained-byte/process-metadata audit; imports no candidate/writer/v1."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
MANDATORY = ['identity', 'freshness', 'effect']
# Literal finite oracle: disposition, reason, current completed-prefix length.
EXPECTED = {
    'c01': ('PARTIAL_UNKNOWN', 'MISSING_OR_UNPROVEN_MANDATORY', 1),
    'c02': ('PARTIAL_UNKNOWN', 'MISSING_OR_UNPROVEN_MANDATORY', 2),
    'c03': ('COMPLETE_VERDICT', 'MANDATORY_COMPLETE', 3),
    'c04': ('COMPLETE_VERDICT', 'MANDATORY_COMPLETE', 3),
    'c05': ('COMPLETE_VERDICT', 'MANDATORY_COMPLETE', 3),
    'c06': ('PARTIAL_UNKNOWN', 'MISSING_OR_UNPROVEN_MANDATORY', 2),
    'c07': ('COUNTEREXAMPLE', 'SOURCE_CURRENT_NEGATIVE', 1),
    'c08': ('PARTIAL_UNKNOWN', 'GENERATION_OR_SCOPE', 0),
    'c09': ('PARTIAL_UNKNOWN', 'ORDER_OR_DUPLICATE', 0),
}

def require(value, message):
    if not value:
        raise ValueError(message)

def sha(value):
    return hashlib.sha256(value).hexdigest()

def object_keys(value, keys, name):
    require(type(value) is dict and set(value) == set(keys.split()), name + ' schema')

def utc(value):
    require(type(value) is str and value.endswith('+00:00'), 'UTC representation')
    try:
        result = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError('UTC parse') from error
    require(result.tzinfo == timezone.utc, 'UTC timezone')
    return result

def audit(raw, folder):
    folder = Path(folder)
    frozen = json.loads((HERE / 'FREEZE.json').read_bytes())
    specs = json.loads((HERE / 'cases.json').read_bytes())
    run = json.loads((HERE / 'RUN.json').read_bytes())
    object_keys(raw, 'schema sources started_utc ended_utc environment rows', 'raw')
    require(raw['schema'] == 'disk-prefix-process-boundary-v1', 'schema')
    actual = {name: sha((HERE / name).read_bytes()) for name in frozen['sources']}
    require(raw['sources'] == actual == frozen['sources'], 'original source freeze')
    object_keys(raw['environment'], 'python platform executable_sha256', 'environment')
    env = frozen['environment']
    require(raw['environment'] == {'python':env['python'], 'platform':env['platform'],
        'executable_sha256':env['python_executable_sha256']}, 'frozen environment')
    require(type(run) is list and len(run) == 2 and [r['name'] for r in run] == ['boundary', 'audit'], 'RUN identities')
    for r in run:
        object_keys(r, 'name argv cwd started_utc ended_utc exit_code output_sha256', 'RUN')
        require(type(r['exit_code']) is int and r['exit_code'] == 0, 'RUN exit')
        require(r['cwd'] == '<workspace>', 'RUN cwd')
        log = HERE / 'results' / ('boundary.log' if r['name'] == 'boundary' else 'audit.log')
        require(sha(log.read_bytes()) == r['output_sha256'], 'RUN log hash')
    require(run[0]['argv'] == ['python', '<package>\\run_boundary.py', '<package>\\results\\boundary-01'], 'boundary argv')
    require(run[1]['argv'] == ['python', '<package>\\audit.py', '<package>\\results\\boundary-01', '<package>\\results\\audit-01.json'], 'audit argv')
    start, end = utc(raw['started_utc']), utc(raw['ended_utc'])
    require(utc(frozen['utc']) <= utc(run[0]['started_utc']) <= start <= end <= utc(run[0]['ended_utc'])
        <= utc(run[1]['started_utc']) <= utc(run[1]['ended_utc']), 'freeze/RUN/raw chronology')
    require(type(raw['rows']) is list and len(raw['rows']) == len(specs) == 9, 'row denominator')
    previous = start
    completed_total = 0
    for index, (row, case) in enumerate(zip(raw['rows'], specs)):
        object_keys(row, 'case processes recovery second_recovery journal_sha256 always_unknown trust_cached', 'row')
        object_keys(row['case'], 'id cut negative generation duplicate', 'case')
        require(row['case'] == case and type(row['case']['generation']) is int
            and all(type(row['case'][k]) is bool for k in ('negative', 'duplicate')), 'case identity/types/order')
        name = case['id']
        count = {'c01':1, 'c02':2, 'c03':3, 'c04':3, 'c05':3, 'c06':2, 'c07':1, 'c08':3, 'c09':4}[name]
        records = [dict(sequence=i+1, check=(MANDATORY+['effect'])[i], value=not(name=='c07' and i==0),
            generation=1, scope='synthetic-claim') for i in range(count)]
        wanted_journal = ''.join(json.dumps(r, sort_keys=True)+'\n' for r in records).encode()
        if name == 'c06':
            wanted_journal += b'{"sequence":3'
        journal = (folder / name / 'receipts.jsonl').read_bytes()
        require(journal == wanted_journal and row['journal_sha256'] == sha(journal), 'retained journal bytes/hash')
        disposition, reason, prefix = EXPECTED[name]
        wanted_result = dict(disposition=disposition, reason=reason, completed=MANDATORY[:prefix], missing=MANDATORY[prefix:],
            journal_sha256=sha(journal), consumer_authority=False)
        for key in ('recovery', 'second_recovery'):
            object_keys(row[key], 'disposition reason completed missing journal_sha256 consumer_authority', 'result')
            require(row[key] == wanted_result and row[key]['consumer_authority'] is False, 'complete result oracle')
        require(type(row['processes']) is list and len(row['processes']) == 3, 'process denominator')
        for position, process in enumerate(row['processes']):
            object_keys(process, 'mode argv started_utc ended_utc exit_code stdout stderr', 'process')
            mode = 'write' if position == 0 else 'read'
            require(process['mode'] == mode and process['argv'] == ['python.exe', 'child.py', mode, name,
                json.dumps(case, sort_keys=True)], 'child argv/mode/case')
            require(type(process['exit_code']) is int and process['exit_code'] == (73 if position == 0 else 0), 'child exit')
            require(type(process['stdout']) is str and process['stderr'] == '', 'child output types')
            begin, finish = utc(process['started_utc']), utc(process['ended_utc'])
            require(previous <= begin <= finish <= end, 'serial child chronology')
            if index == 0 and position == 0:
                require(begin == start, 'first child/raw start')
            previous = finish
            if position == 0:
                require(process['stdout'] == '', 'writer stdout')
            else:
                try:
                    emitted = json.loads(process['stdout'])
                except (ValueError, TypeError) as error:
                    raise ValueError('reader stdout JSON') from error
                object_keys(emitted, 'disposition reason completed missing journal_sha256 consumer_authority', 'stdout result')
                require(emitted == wanted_result and emitted['consumer_authority'] is False, 'full reader stdout')
        marker = folder / name / 'cached-verdict.json'
        cached = name in ('c05', 'c08', 'c09')
        require(marker.exists() is cached, 'marker presence')
        if cached:
            require(marker.read_bytes() == b'{"disposition": "COMPLETE_VERDICT"}\n', 'exact marker bytes')
        require(row['always_unknown'] == 'PARTIAL_UNKNOWN' and row['trust_cached'] ==
            ('COMPLETE_VERDICT' if cached else 'PARTIAL_UNKNOWN'), 'comparators')
        completed_total += prefix
    return dict(status='PASS_AUDIT_V2_RETAINED_BOUNDARY_SCOPED', cases=9, child_invocations=27,
        complete=3, counterexamples=1, partial_unknown=5, reusable_current_checks=completed_total,
        cached_false_completions=2, consumer_authority=False, candidate_reexecuted=False)

def main():
    folder, output = map(Path, sys.argv[1:])
    freeze = json.loads((HERE / 'FREEZE-v2.json').read_bytes())
    for name, digest in freeze['files'].items():
        require(sha((HERE / name).read_bytes()) == digest, 'v2 source/input freeze: ' + name)
    raw = json.loads((folder / 'raw.json').read_bytes())
    result = audit(raw, folder)
    result['raw_sha256'] = sha((folder / 'raw.json').read_bytes())
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
