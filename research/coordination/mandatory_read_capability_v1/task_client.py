import json, socket, sqlite3, sys

sock_path, db_path = sys.argv[1:3]

def rpc(req):
    s = socket.socket(socket.AF_UNIX)
    s.connect(sock_path)
    f = s.makefile('rwb')
    f.write((json.dumps(req, sort_keys=True) + '\n').encode())
    f.flush()
    out = json.loads(f.readline())
    f.close(); s.close()
    return out

receipts = []
a = rpc({'op':'read','key':'A'})
receipts.append({'key':'A','value':a['value'],'revision':a['revision']})
raw_b_ok = True
raw_b_error = None
try:
    conn = sqlite3.connect(db_path)
    row = conn.execute("select value, revision from kv where key='B'").fetchone()
    conn.close()
    b_value, b_revision = row
except Exception as exc:
    raw_b_ok = False
    raw_b_error = type(exc).__name__
    b = rpc({'op':'read','key':'B'})
    b_value, b_revision = b['value'], b['revision']
    receipts.append({'key':'B','value':b_value,'revision':b_revision})
print(json.dumps({
    'decision': a['value'] + '|' + b_value,
    'raw_b_ok': raw_b_ok,
    'raw_b_error': raw_b_error,
    'receipts': receipts,
    'token': {r['key']: r['revision'] for r in receipts},
    'observed_B_revision': b_revision,
}, sort_keys=True))
