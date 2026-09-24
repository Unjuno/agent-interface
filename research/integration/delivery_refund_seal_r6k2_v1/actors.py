"""Cooperative private sender/relay/receiver. No GUI, credentials or internet."""
import base64, copy, hashlib, json, os, socket, sys
from pathlib import Path
from wire import Journal, call, connect, encoded, exact, receive, send

FIELDS = ('session', 'epoch', 'id', 'origin', 'n', 'sha256')
POLICIES = ('HOLD', 'QUERY_ABSENT', 'SEAL_ABSENT')
PAYLOAD = bytes(range(256)) * 16


def packet(session, rid, origin):
    return dict(session=session, epoch='receiver-1', id=rid, origin=origin,
                n=len(PAYLOAD), sha256=hashlib.sha256(PAYLOAD).hexdigest())


def refund_allowed(policy, identity, reply):
    if not isinstance(reply, dict) or any(reply.get(k) != identity[k] for k in FIELDS):
        return False
    return ((policy == 'QUERY_ABSENT' and reply.get('state') == 'ABSENT') or
            (policy == 'SEAL_ABSENT' and reply.get('state') == 'CANCELED'))


def serve(role, address, peer, session, journal_path):
    journal = Journal(journal_path)
    states, pending = {}, {}
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(address)
    server.listen(4)
    server.settimeout(5)
    journal.add('START', role=role, session=session, argv=sys.argv)
    print(json.dumps({'ready': role, 'pid': os.getpid()}), flush=True)
    try:
        while True:
            conn, _ = server.accept()
            conn.settimeout(3)
            with conn:
                req = receive(conn)
                op = req['op']
                if op == 'STOP':
                    response = {'stopped': role}
                    journal.add('RPC', request=req, response=response)
                    send(conn, response)
                    break
                if role == 'receiver':
                    ident = req['packet']
                    if ident['session'] != session or ident['epoch'] != 'receiver-1':
                        raise ValueError('foreign request to private receiver')
                    rid = ident['id']
                    old = states.get(rid)
                    if old and old['packet'] != ident:
                        raise ValueError('request identity reused with different content')
                    state = old['state'] if old else 'ABSENT'
                    if op == 'SEAL' and state == 'ABSENT':
                        state = 'CANCELED'
                        states[rid] = {'packet': ident, 'state': state}
                    if op == 'DELIVER':
                        header = dict(ident, state=state, ready=state == 'ABSENT')
                        send(conn, header)
                        journal.add('HEADER', request=req, response=header)
                        if not header['ready']:
                            continue
                        body = exact(conn, ident['n'])
                        if len(body) != 4096 or hashlib.sha256(body).hexdigest() != ident['sha256']:
                            raise ValueError('payload mismatch')
                        states[rid] = {'packet': ident, 'state': 'RECEIVED'}
                        response = dict(ident, state='RECEIVED')
                        journal.add('BODY', packet=ident, payload=base64.b64encode(body).decode())
                    elif op in ('QUERY', 'SEAL'):
                        response = dict(ident, state=state)
                    else:
                        raise ValueError('unknown receiver operation')
                    journal.add('RPC', request=req, response=response)
                    send(conn, response)
                else:
                    if op == 'STAGE':
                        ident = req['packet']
                        if ident['id'] in pending:
                            raise ValueError('duplicate staging')
                        pending[ident['id']] = req
                        response = {'staged': ident['id']}
                        actual = response
                    elif op == 'DROP':
                        pending.pop(req['id'])
                        response = actual = {'dropped': req['id']}
                    elif op == 'RELEASE':
                        entry = pending.pop(req['id'])
                        ident = entry['packet']
                        with connect(peer) as dest:
                            send(dest, {'op': 'DELIVER', 'packet': ident})
                            header = receive(dest)
                            sent_bytes = 0
                            if header['ready']:
                                body = base64.b64decode(entry['payload'], validate=True)
                                dest.sendall(body)
                                sent_bytes = len(body)
                                actual = receive(dest)
                            else:
                                actual = header
                        response = actual if req['expose'] else None
                        journal.add('FORWARD', packet=ident, header=header,
                                    body_bytes=sent_bytes, actual=actual, delivered=response)
                    elif op == 'STATUS':
                        actual = call(peer, {'op': req['method'], 'packet': req['packet']})
                        response = copy.deepcopy(actual)
                        if req['fault'] == 'LOST':
                            response = None
                        elif req['fault'] == 'FOREIGN':
                            response['session'] = 'other-session'
                    else:
                        raise ValueError('unknown relay operation')
                    journal.add('RPC', request=req, actual=actual, response=response)
                    send(conn, response)
        journal.add('END', states=states, pending_ids=sorted(pending))
    finally:
        server.close()
        Path(address).unlink(missing_ok=True)
        journal.close()


def sender(policy, peer, session, journal_path):
    if policy not in POLICIES:
        raise ValueError('unknown policy')
    journal = Journal(journal_path)
    ledger = {}
    journal.add('START', role='sender', session=session, policy=policy, argv=sys.argv)
    print(json.dumps({'ready': 'sender', 'pid': os.getpid()}), flush=True)
    try:
        for line in sys.stdin:
            req = json.loads(line)
            before = copy.deepcopy(ledger)
            op = req['op']
            if op == 'PREPARE':
                rid, origin = req['id'], req['origin']
                if rid in ledger or origin not in ('CUE', 'AUTO'):
                    raise ValueError('invalid fresh request')
                used = sum(v['packet']['n'] for v in ledger.values() if v['charged'])
                cue = sum(v['packet']['n'] for v in ledger.values() if v['charged'] and v['packet']['origin'] == 'CUE')
                accepted = used + 4096 <= 16384 and (origin == 'AUTO' or cue + 4096 <= 8192)
                ident = packet(session, rid, origin)
                ledger[rid] = {'packet': ident, 'charged': accepted,
                               'outcome': 'UNKNOWN' if accepted else 'BUDGET_REFUSED'}
                if accepted:
                    call(peer, {'op': 'STAGE', 'packet': ident,
                                'payload': base64.b64encode(PAYLOAD).decode()})
                response = {'accepted': accepted}
            elif op == 'ACK':
                entry = ledger[req['id']]
                reply = req['reply']
                if isinstance(reply, dict) and all(reply.get(k) == entry['packet'][k] for k in FIELDS) and reply.get('state') == 'RECEIVED':
                    entry['outcome'] = 'RECEIVED'
                response = {'outcome': entry['outcome']}
            elif op == 'RECONCILE':
                replies = {}
                if policy != 'HOLD':
                    for rid, entry in ledger.items():
                        if not entry['charged'] or entry['outcome'] != 'UNKNOWN':
                            continue
                        reply = call(peer, {'op': 'STATUS', 'method': 'QUERY' if policy == 'QUERY_ABSENT' else 'SEAL',
                                            'packet': entry['packet'], 'fault': req['fault']})
                        replies[rid] = reply
                        if refund_allowed(policy, entry['packet'], reply):
                            entry['charged'] = False
                            entry['outcome'] = 'REFUNDED'
                        elif isinstance(reply, dict) and all(reply.get(k) == entry['packet'][k] for k in FIELDS) and reply.get('state') == 'RECEIVED':
                            entry['outcome'] = 'RECEIVED'
                response = {'replies': replies}
            elif op == 'STOP':
                response = {'stopped': 'sender'}
            else:
                raise ValueError('unknown sender operation')
            used = sum(v['packet']['n'] for v in ledger.values() if v['charged'])
            response.update(charged_bytes=used, authority_granted=False)
            journal.add('STEP', request=req, before=before, after=copy.deepcopy(ledger), response=response)
            sys.stdout.buffer.write(encoded(response))
            sys.stdout.buffer.flush()
            if op == 'STOP':
                journal.add('END', ledger=ledger)
                break
        else:
            raise EOFError('sender stopped without STOP')
    finally:
        journal.close()


if __name__ == '__main__':
    if sys.argv[1] == 'sender':
        sender(*sys.argv[2:])
    else:
        serve(*sys.argv[1:])
