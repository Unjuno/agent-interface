"""Research-only Submit-event semantics on the exact retained document store.

A submission is a private database record, not an external business effect.
This explicitly adds a contract; it does not change the historical sink.
"""
import hashlib
import json
from legacy_sink import Store as LegacyStore, FIELDS


class Store(LegacyStore):
    def __init__(self, path, session):
        super().__init__(path, session, 'REVISION_FENCE')
        self.db.execute('CREATE TABLE submissions (job_id TEXT PRIMARY KEY, revision INTEGER NOT NULL, value TEXT NOT NULL)')

    def apply(self, job):
        if (type(job) is not dict or set(job) != FIELDS or
                job['session'] != self.session or job['document'] != 'doc' or
                job['epoch'] != 'epoch-1' or type(job['revision']) is not int or
                not 1 <= job['revision'] < 2**63 or type(job['value']) is not str or
                len(job['value']) > 64 or type(job['job_id']) is not str or
                not 1 <= len(job['job_id']) <= 80 or job['kind'] not in ('AUTO', 'SUBMIT')):
            return {'status': 'INVALID', 'authority': False, 'state': self.state()}
        fingerprint = hashlib.sha256(json.dumps(job, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            before = self.state()
            previous = self.db.execute('SELECT fingerprint,status FROM seen WHERE job_id=?', (job['job_id'],)).fetchone()
            if previous is not None:
                status = 'REPLAY' if previous[0] == fingerprint else 'CONFLICT_ID'
            elif job['revision'] < before['revision']:
                status = 'STALE'
            elif job['revision'] == before['revision'] and job['value'] != before['value']:
                status = 'CONFLICT_REVISION'
            elif job['revision'] == before['revision']:
                status = 'SUBMITTED_CURRENT' if job['kind'] == 'SUBMIT' else 'DUPLICATE_REVISION'
            else:
                status = 'APPLIED'
            if status == 'APPLIED':
                self.db.execute('UPDATE document SET revision=?,value=? WHERE id=1', (job['revision'], job['value']))
                self.db.execute('INSERT INTO commits(job_id,revision,value,kind) VALUES(?,?,?,?)',
                                (job['job_id'], job['revision'], job['value'], job['kind']))
            if job['kind'] == 'SUBMIT' and status in ('APPLIED', 'SUBMITTED_CURRENT'):
                self.db.execute('INSERT INTO submissions VALUES(?,?,?)', (job['job_id'], job['revision'], job['value']))
            if previous is None:
                self.db.execute('INSERT INTO seen VALUES(?,?,?)', (job['job_id'], fingerprint, status))
            after = self.state()
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise
        return {'status': status, 'before': before, 'state': after, 'authority': False}
