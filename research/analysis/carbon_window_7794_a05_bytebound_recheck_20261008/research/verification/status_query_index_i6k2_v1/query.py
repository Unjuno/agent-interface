"""Read-only first-outcome projection for the archived cooperative sink.

This is an opt-in research adapter. It never calls Store.apply, dispatches input,
repairs state, or interprets an absent row as proof of non-execution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys

SCHEMA = 'research/replay-first-outcome-v1'
FIELDS = {'session', 'document', 'epoch', 'job_id', 'revision', 'value', 'kind'}
REJECTS = {'STALE': 'REJECTED_STALE',
           'CONFLICT_REVISION': 'REJECTED_REVISION_CONFLICT',
           'DUPLICATE_REVISION': 'NO_NEW_COMMIT_SAME_VALUE'}

def base() -> dict:
    return dict(schema=SCHEMA, outcome='UNKNOWN_INCONSISTENT',
                request_sha256=None, stored_status=None,
                request_commit_count=None, current_state=None,
                current_value_matches=None, authority=False,
                replay_authority=False, task_success=None)

def valid_request(j: object, session: str) -> bool:
    return (type(j) is dict and set(j) == FIELDS and
            type(session) is str and bool(session) and
            type(j['session']) is str and j['session'] == session and
            j['document'] == 'doc' and j['epoch'] == 'epoch-1' and
            type(j['revision']) is int and 1 <= j['revision'] < 2**63 and
            type(j['value']) is str and len(j['value']) <= 64 and
            type(j['job_id']) is str and 1 <= len(j['job_id']) <= 80 and
            type(j['kind']) is str and j['kind'] in ('AUTO', 'SUBMIT'))

def query(path: Path, request: object, session: str, trace: list | None = None) -> dict:
    """Join retained receipt and commit rows in one read-only snapshot.

    Database identity, owner honesty and complete retained tables are assumptions;
    hashes bind content, not origin. Current value is sampled, not future authority.
    """
    out = base()
    if not valid_request(request, session):
        out['outcome'] = 'INVALID_QUERY'
        return out
    digest = hashlib.sha256(json.dumps(request, sort_keys=True,
                                      separators=(',', ':')).encode()).hexdigest()
    out['request_sha256'] = digest
    con = None
    try:
        con = sqlite3.connect(path.resolve(strict=True).as_uri() + '?mode=ro',
                              uri=True, isolation_level=None, timeout=2)
        if trace is not None:
            con.set_trace_callback(trace.append)
        con.execute('PRAGMA query_only=ON')
        con.execute('BEGIN')
        doc = con.execute('SELECT revision,value FROM document WHERE id=1').fetchall()
        seen = con.execute('SELECT fingerprint,status FROM seen WHERE job_id=?',
                           (request['job_id'],)).fetchall()
        commits = con.execute('SELECT ordinal,job_id,revision,value,kind FROM commits '
                              'WHERE job_id=? ORDER BY ordinal',
                              (request['job_id'],)).fetchall()
        con.execute('COMMIT')
        if (len(doc) != 1 or type(doc[0][0]) is not int or
            not 0 <= doc[0][0] < 2**63 or type(doc[0][1]) is not str):
            return out
        out['current_state'] = dict(revision=doc[0][0], value=doc[0][1])
        out['current_value_matches'] = doc[0][1] == request['value']
        if not seen:
            if not commits:
                out['outcome'] = 'NOT_RECORDED'
            return out
        if len(seen) != 1:
            return out
        if seen[0][0] != digest:
            out['outcome'] = 'CONFLICT_ID'
            return out
        first = seen[0][1]
        if first == 'APPLIED':
            if (len(commits) != 1 or type(commits[0][0]) is not int or
                commits[0][0] < 1 or type(commits[0][2]) is not int or
                tuple(commits[0][1:]) != (request['job_id'], request['revision'],
                                         request['value'], request['kind'])):
                return out
            out.update(outcome='APPLIED_ONCE', stored_status=first,
                       request_commit_count=1)
        elif first in REJECTS and not commits:
            out.update(outcome=REJECTS[first], stored_status=first,
                       request_commit_count=0)
        return out
    except (sqlite3.Error, OSError, ValueError):
        return out
    finally:
        if con is not None:
            con.close()

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--db', type=Path, required=True)
    p.add_argument('--session', required=True)
    a = p.parse_args()
    trace: list[str] = []
    req = json.loads(sys.stdin.read())
    print(json.dumps(dict(result=query(a.db, req, a.session, trace),
                          sql_trace=trace, pid=os.getpid()), sort_keys=True))

if __name__ == '__main__':
    main()
