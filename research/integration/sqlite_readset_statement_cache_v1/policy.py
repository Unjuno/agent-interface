"""Dependency instrumentation experiment; NOT an access-control policy.

Every authorizer callback returns SQLITE_OK. Only fixed, local fixture SELECTs
are accepted by this wrapper. Prepared SQL metadata and current value revisions
are intentionally distinct objects. No GUI, network, or model is involved.
"""
from __future__ import annotations
import json
import sqlite3

QUERIES = {
    'SELECT value FROM a': 'a',
    'SELECT value FROM b': 'b',
    'SELECT value FROM current_view': 'current_view',
}
MODES = ('EVENT_ONLY', 'NO_STATEMENT_CACHE', 'METADATA_REUSE')
BASE_TABLES = frozenset(('a', 'b', 'u'))

class Reader:
    def __init__(self, path: str, mode: str):
        if mode not in MODES:
            raise ValueError('UNKNOWN_MODE')
        self.mode = mode
        self.cache_size = 0 if mode == 'NO_STATEMENT_CACHE' else 128
        self.db = sqlite3.connect(path, isolation_level=None,
                                  cached_statements=self.cache_size, timeout=2)
        self.events: list[dict] = []
        self.trace: list[str] = []
        self.active = False
        # Lifetime is this connection, not a process-global SQL dictionary.
        self.metadata: dict[tuple[int, str], tuple[str, ...]] = {}
        self.db.set_authorizer(self._observe_prepare)
        self.db.set_trace_callback(self.trace.append)

    def _observe_prepare(self, action, first, second, database, context):
        if self.active:
            self.events.append({'action': action, 'first': first, 'second': second,
                                'database': database, 'context': context})
        return sqlite3.SQLITE_OK

    def prepare(self, sql: str) -> dict:
        if sql not in QUERIES:
            raise ValueError('OUTSIDE_FIXED_QUERY_FAMILY')
        self.events = []
        self.trace.clear()
        self.db.execute('BEGIN')
        try:
            schema = self.db.execute('PRAGMA main.schema_version').fetchone()[0]
            key = (schema, sql)
            cached = self.metadata.get(key)
            self.active = True
            try:
                rows = self.db.execute(sql).fetchall()
            finally:
                self.active = False
            if len(rows) != 1 or type(rows[0][0]) is not str:
                raise ValueError('UNSUPPORTED_RESULT_SHAPE')
            fresh_tables = tuple(sorted({e['first'] for e in self.events
                if e['action'] == sqlite3.SQLITE_READ and
                   e['database'] == 'main' and e['first'] in BASE_TABLES}))
            if self.mode == 'METADATA_REUSE':
                if fresh_tables:
                    self.metadata[key] = fresh_tables
                    tables = fresh_tables
                    origin = 'FRESH_PREPARE_METADATA'
                elif cached is not None:
                    tables = cached
                    origin = 'CONNECTION_SCHEMA_SQL_METADATA'
                else:
                    return {'status': 'UNKNOWN_METADATA', 'sql': sql,
                            'schema_version': schema, 'value': rows[0][0],
                            'receipts': [], 'events': self.events.copy(),
                            'metadata_origin': 'MISSING', 'sql_trace': self.trace.copy()}
            else:
                tables = fresh_tables
                origin = 'CURRENT_CALLBACKS_ONLY'
            # These queries run AFTER callback return, in the SAME read snapshot.
            # They never modify the connection inside an authorizer callback.
            receipts = []
            for name in tables:
                rev = self.db.execute(f'SELECT revision FROM {name}').fetchone()[0]
                if type(rev) is not int or rev < 1:
                    raise ValueError('INVALID_RESOURCE_REVISION')
                receipts.append({'resource': name, 'revision': rev})
            return {'status': 'PREPARED', 'sql': sql, 'schema_version': schema,
                    'value': rows[0][0], 'receipts': receipts,
                    'events': self.events.copy(), 'metadata_origin': origin,
                    'sql_trace': self.trace.copy()}
        finally:
            self.active = False
            self.db.execute('COMMIT')

    def commit(self, request_id: str, prepared: dict) -> dict:
        """Cooperative local result publication; compare+effect is one transaction."""
        self.db.execute('BEGIN IMMEDIATE')
        try:
            schema = self.db.execute('PRAGMA main.schema_version').fetchone()[0]
            versions = {}
            for receipt in prepared['receipts']:
                name = receipt['resource']
                if name not in BASE_TABLES:
                    raise ValueError('UNKNOWN_RESOURCE')
                versions[name] = self.db.execute(
                    f'SELECT revision FROM {name}').fetchone()[0]
            accepted = (prepared['status'] == 'PREPARED' and
                        type(prepared['schema_version']) is int and
                        schema == prepared['schema_version'] and
                        all(type(r['revision']) is int and
                            versions[r['resource']] == r['revision']
                            for r in prepared['receipts']))
            if accepted:
                self.db.execute('INSERT INTO effects(request_id,payload) VALUES (?,?)',
                                (request_id, prepared['value']))
            self.db.execute('COMMIT')
            return {'accepted': accepted, 'schema_version': schema,
                    'versions_checked': versions}
        except BaseException:
            if self.db.in_transaction:
                self.db.execute('ROLLBACK')
            raise

    def close(self):
        self.db.close()
