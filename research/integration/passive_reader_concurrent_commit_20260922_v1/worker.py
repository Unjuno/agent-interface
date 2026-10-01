"""Experimental host-result commit worker. No action/ACK or production integration."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from upstream.reader import read_pending


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def state(db):
    revision, cursor = db.execute('SELECT revision,cursor FROM state WHERE id=1').fetchone()
    return {'revision': revision, 'cursor': json.loads(cursor)}


def commit(db, prepared, policy, worker):
    # All three arms publish response + cursor atomically. Only stale-read admission differs.
    db.execute('BEGIN IMMEDIATE')
    try:
        current = state(db)
        if policy == 'REVISION_CAS' and current != prepared['start']:
            db.rollback()
            return {'disposition': 'STALE_RESULT', 'request_id': prepared['request_id']}
        target = prepared['response']['next_cursor']
        if policy == 'OFFSET_MAX' and current['cursor']['offset'] > target['offset']:
            target = current['cursor']
        db.execute('INSERT INTO batches(worker,request_id,response) VALUES(?,?,?)',
                   (worker, prepared['request_id'], encoded(prepared['response'])))
        if policy == 'REVISION_CAS':
            changed = db.execute('UPDATE state SET revision=revision+1,cursor=? '
                                 'WHERE id=1 AND revision=? AND cursor=?',
                                 (encoded(target), prepared['start']['revision'],
                                  encoded(prepared['start']['cursor']))).rowcount
            if changed != 1:
                raise RuntimeError('CAS_UPDATE_MISMATCH')
        else:
            db.execute('UPDATE state SET revision=revision+1,cursor=? WHERE id=1',
                       (encoded(target),))
        db.commit()
        return {'disposition': 'COMMITTED', 'request_id': prepared['request_id']}
    except BaseException:
        db.rollback()
        raise


def main():
    root, worker, policy, stream_id = sys.argv[1:]
    if policy not in ('BLIND_REPLACE', 'OFFSET_MAX', 'REVISION_CAS'):
        raise ValueError('INVALID_POLICY')
    db = sqlite3.connect(str(Path(root) / 'host.sqlite'), isolation_level=None, timeout=3)
    db.execute('PRAGMA synchronous=FULL')
    prepared = None
    for line in sys.stdin:
        command = json.loads(line)
        start_ns = time.monotonic_ns()
        if command['op'] == 'prepare':
            before = state(db)
            response = read_pending(Path(root) / 'stream.jsonl', stream_id=stream_id,
                                    cursor=before['cursor'], max_records=command['limit'])
            prepared = {'request_id': command['request_id'], 'start': before, 'response': response}
            result = {'prepared': prepared}
        elif command['op'] == 'commit':
            if prepared is None:
                raise ValueError('NOT_PREPARED')
            result = commit(db, prepared, policy, worker)
        elif command['op'] == 'quit':
            result = {'disposition': 'EXIT'}
        else:
            raise ValueError('INVALID_OPERATION')
        print(encoded({'pid': os.getpid(), 'started_ns': start_ns,
                       'finished_ns': time.monotonic_ns(), **result}), flush=True)
        if command['op'] == 'quit':
            break
    db.close()


if __name__ == '__main__':
    main()
