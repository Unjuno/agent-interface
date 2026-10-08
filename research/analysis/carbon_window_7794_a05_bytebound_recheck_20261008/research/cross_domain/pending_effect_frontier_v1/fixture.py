"""Controlled native GUI. Only XTEST F1..F4 requests effects; F5 queries status.

The controller reads public receipts, never this application's scoring database.
No deduplication: every received mutating key can append another effect row.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time
import tkinter as tk


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def description(scenario, token):
    alias = 'shortcut/A' if scenario == 'alias' else 'document/A'
    return {
        'A': {'read': [], 'write': ['document/A'], 'value': token + ':A', 'delay_ms': 240},
        'D': {'read': [alias], 'write': ['report/D'], 'value': None, 'delay_ms': 20},
        'B': {'read': [], 'write': ['document/B'], 'value': token + ':B', 'delay_ms': 100},
        'C': {'read': [], 'write': ['document/C'], 'value': token + ':C', 'delay_ms': 100}}


def main(root):
    root = Path(root)
    config = json.loads((root / 'config.json').read_text())
    scenario, token, epoch = (config[k] for k in ('scenario', 'token', 'epoch'))
    ops = description(scenario, token)
    aliases = {'document/A': 'A', 'shortcut/A': 'A', 'document/B': 'B', 'document/C': 'C', 'report/D': 'D'}
    hashes = {k: digest(json.dumps(v, sort_keys=True)) for k, v in ops.items()}
    db = sqlite3.connect(root / 'private.sqlite', isolation_level=None)
    db.execute('PRAGMA journal_mode=DELETE')
    db.execute('PRAGMA synchronous=FULL')
    db.executescript('CREATE TABLE documents (name TEXT PRIMARY KEY, value TEXT, version INTEGER);'
                    'CREATE TABLE effects (operation TEXT, value TEXT, read_version INTEGER, applied_ns INTEGER);')
    for key in 'ADBC':
        db.execute('INSERT INTO documents VALUES (?,?,?)', (key, 'old:' + key, 0))
    (root / 'public').mkdir()
    log = (root / 'application.jsonl').open('w')
    serial = 0
    jobs = 0
    durable = {}
    app = tk.Tk()
    app.title('Pending-effect frontier fixture')
    app.geometry('620x210+60+60')
    label = tk.Label(app, text='F1: produce A    F2: copy A to D\nF3: save B    F4: save C    F5: read-only status A', font=('sans', 15))
    label.pack(pady=25)
    status = tk.Label(app, text='Ready', font=('sans', 12)); status.pack()

    def record(event, **fields):
        log.write(json.dumps(dict(event=event, ns=time.perf_counter_ns(), **fields), sort_keys=True) + '\n'); log.flush()

    def publish(operation, kind, status, rowid=None, durable_ns=None):
        nonlocal serial
        serial += 1
        row = dict(epoch=epoch, operation=operation, payload_sha256=hashes[operation],
                   kind=kind, status=status, effect_rowid=rowid, durable_ns=durable_ns,
                   published_ns=time.perf_counter_ns())
        path = root / 'public' / f'{serial:04d}.json'
        tmp = path.with_suffix('.tmp'); tmp.write_text(json.dumps(row, sort_keys=True)); tmp.rename(path)

    def apply(operation, read_value, read_version):
        nonlocal jobs
        spec = ops[operation]
        value = read_value if spec['read'] else spec['value']
        target = aliases[spec['write'][0]]
        db.execute('BEGIN IMMEDIATE')
        try:
            db.execute('UPDATE documents SET value=?, version=version+1 WHERE name=?', (value, target))
            cur = db.execute('INSERT INTO effects VALUES (?,?,?,?)', (operation, value, read_version, time.perf_counter_ns()))
            db.execute('COMMIT')
        except BaseException:
            db.execute('ROLLBACK'); raise
        now = time.perf_counter_ns(); durable[operation] = (cur.lastrowid, now)
        record('committed', operation=operation, value=value, read_version=read_version, rowid=cur.lastrowid, durable_ns=now)
        if not (scenario == 'ack_lost' and operation == 'A'):
            publish(operation, 'ack', 'COMMITTED', cur.lastrowid, now)
        jobs -= 1
        status.config(text='Committed ' + operation)

    def receive(event):
        nonlocal jobs
        if event.keysym == 'F5':
            record('lookup', operation='A')
            rows = db.execute("SELECT rowid FROM effects WHERE operation='A'").fetchall()
            if len(rows) == 1 and 'A' in durable:
                rowid, ns = durable['A']; publish('A', 'lookup', 'COMMITTED', rowid, ns)
            else:
                publish('A', 'lookup', 'UNKNOWN')
            return
        operation = {'F1': 'A', 'F2': 'D', 'F3': 'B', 'F4': 'C'}.get(event.keysym)
        if operation is None:
            return
        spec = ops[operation]
        read_value, read_version = None, None
        if spec['read']:
            read_value, read_version = db.execute('SELECT value,version FROM documents WHERE name=?',
                                                 (aliases[spec['read'][0]],)).fetchone()
        record('request', operation=operation, read_value=read_value, read_version=read_version)
        if scenario == 'dropped' and operation == 'A':
            record('dropped', operation='A'); return
        jobs += 1
        app.after(spec['delay_ms'], lambda: apply(operation, read_value, read_version))
        status.config(text='Pending ' + operation)

    app.bind('<KeyPress>', receive)
    app.update(); app.focus_force(); app.update()
    manifest = {}
    for k, spec in ops.items():
        manifest[k] = {'reads': spec['read'], 'writes': spec['write'], 'payload_sha256': hashes[k]}
    if scenario == 'opaque':
        manifest['A']['reads'] = manifest['A']['writes'] = None
    ready = dict(window_id=app.winfo_id(), epoch=epoch, catalogue_version=1,
                 aliases=aliases, effects=manifest, tkinter_version=tk.TkVersion)
    tmp = root / 'ready.tmp'; tmp.write_text(json.dumps(ready, sort_keys=True)); tmp.rename(root / 'ready.json')

    def stop_check():
        if (root / 'stop').exists() and jobs == 0:
            app.destroy()
        else:
            app.after(5, stop_check)
    app.after(5, stop_check)
    try:
        app.mainloop()
    finally:
        db.close(); log.close()


if __name__ == '__main__':
    main(sys.argv[1])
