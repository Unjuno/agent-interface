"""Read-only verification; never extracts or executes archived source."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import tarfile

HERE = Path(__file__).resolve().parent


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    manifest = json.loads((HERE / 'manifest.json').read_text())
    archive = HERE / 'evidence.tar.xz'
    require(archive.stat().st_size == manifest['archive']['bytes'] < 10_000_000, 'archive size')
    require(sha(archive.read_bytes()) == manifest['archive']['sha256'], 'archive digest')
    payload = {}
    with tarfile.open(archive, 'r:xz') as tf:
        total = 0
        for member in tf:
            path = PurePosixPath(member.name)
            require(member.isfile() and not path.is_absolute() and '..' not in path.parts, 'regular relative member')
            require(member.name not in payload and member.name in manifest['members'], 'unique expected member')
            expected = manifest['members'][member.name]
            total += member.size
            require(member.size == expected['bytes'] and total <= 50_000_000, 'bounded member size')
            data = tf.extractfile(member).read()
            require(sha(data) == expected['sha256'], 'member digest: ' + member.name)
            payload[member.name] = data
    require(set(payload) == set(manifest['members']), 'complete inventory')

    def read(name):
        return json.loads(payload[name])

    pins = read('PLAN-v1.json')['source_hashes']
    for name, digest in pins.items():
        require(sha(payload[name]) == digest, 'prospective source pin: ' + name)
    require(payload['candidate-v1.py'] == payload['final-sources/research/live_control/codex_app_server_client_v2.py'], 'executed/final client identity')
    require(all(read('source-checks.json')['checks'].values()), 'recorded source checks')
    for name, expected in read('source-checks.json')['paths'].items():
        require(sha(payload['final-sources/' + name]) == expected, 'final source bytes: ' + name)

    cells = {}
    for arm, source in [('admission', 'admission.py'), ('candidate-v1', 'candidate-v1.py')]:
        for case in ['healthy', 'blocked', 'partial_close']:
            name = arm + '-' + case
            raw = read('actual-v1/' + name + '/raw.json')
            receipt = read('actual-v1/' + name + '.receipt.json')
            journal_bytes = payload['actual-v1/' + name + '/client-journal.jsonl']
            journal = [json.loads(line) for line in journal_bytes.splitlines()]
            require(raw['case'] == case and raw['source_sha256'] == pins[source], 'cell source identity')
            require(receipt['exit'] == 0 and receipt['argv'][-2:] == ['--case', case], 'wrapper exit and case')
            require(receipt['argv'][receipt['argv'].index('--source') + 1] == raw['source_path'], 'receipt/raw source path')
            require(sha(journal_bytes) == raw['journal_sha256'] and len(journal_bytes) == raw['journal_bytes'], 'journal identity')
            require(journal == raw['journal_rows'] and raw['errors'] == [], 'raw/journal agreement')
            require(raw['pending_ids'] == [] and raw['responses'] == {}, 'request state retired')
            require(raw['reader_alive'] is False and raw['process_poll'] is not None, 'actors retired')
            require(all(s['closed'] for s in raw['stream_state'].values()), 'streams retired')
            cells[name] = raw
            if case == 'healthy':
                sent = next(r['message'] for r in journal if r['direction'] == 'sent')
                reply = next(r['message'] for r in journal if r['direction'] == 'received' and type(r['message'].get('id')) is float)
                require(reply['id'] == sent['id'] and raw['result_text_matches'] and raw['result_digest_matches'], 'healthy Unicode/float-ID')
            if case == 'partial_close':
                require(raw['writer_lock_observed_locked'] and raw['pre_close_writer_alive'], 'active writer at close')
                require(raw['close_thread_result'] == 'returned' and raw['close_thread_alive_final'] is False and raw['request_thread_alive_final'] is False, 'concurrent threads retired')
                require(raw['safety_rescue'] == 'not-needed', 'concurrent close no rescue')
    base = cells['admission-blocked']
    fixed = cells['candidate-v1-blocked']
    require(base['caller_finished_before_0_6s'] is False and base['safety_rescue'].startswith('kill owned Popen child'), 'baseline discrimination')
    require(fixed['caller_finished_before_0_6s'] is True and fixed['safety_rescue'] == 'not-needed', 'candidate deadline return')
    error = fixed['request_error']
    require((error['type'], error['sent'], error['total'], error['reason']) == ('AppServerWriteUncertain', 65536, 524345, 'TimeoutError'), 'typed partial send')
    followup = fixed['followup_error']
    require(followup['type'] == 'AppServerWriteUncertain' and followup['reason'] == 'previous send failure' and fixed['followup_journal_unchanged'], 'follow-up refused')
    require(sum(r['direction'] == 'sent' for r in fixed['journal_rows']) == 1, 'no additional sent journal')
    require(abs(fixed['request_elapsed_ms'] - (fixed['request_finished_ns'] - fixed['request_started_ns']) / 1e6) < 1e-9, 'monotonic timing derivation')
    for directory, count in [('focused-normal-v2', 78), ('focused-optimized-v2', 78), ('workspace-v2', 22)]:
        require(read(directory + '/receipt.json')['exit_code'] == 0, 'test exit: ' + directory)
        require(('Ran %d tests' % count).encode() in payload[directory + '/stderr'] and payload[directory + '/stderr'].endswith(b'OK\n'), 'test log: ' + directory)
    require(read('index/receipt.json')['exit_code'] == 0, 'index exit')
    require(read('close-custody-red/receipt.json')['exit'] != 0 and read('borrowed-red/receipt.json')['exit'] != 0, 'retained negative tests')
    print(json.dumps({'status': 'PASS', 'archive_members': len(payload), 'real_popen_cells_read': len(cells), 'producer_rerun': False, 'scope': 'saved evidence integrity and result readback; no live effect or merge approval'}))


if __name__ == '__main__':
    main()
