import json, os, tempfile, threading, traceback
from pathlib import Path
from Xlib import display
from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
from runtime.guarded_x11_v1.owned_xlib_connector import OwnedXlibConnector
from runtime.guarded_x11_v1.target_queries import X11TargetQueries
from runtime.guarded_x11_v1.observation_worker import open_readonly_backend

results = {'cases': {}, 'cleanup': []}
with tempfile.TemporaryDirectory() as td:
    a = PrivateDisplayOwner(Path(td)/'a'); b = PrivateDisplayOwner(Path(td)/'b')
    guard = None
    try:
        sa = a.start(timeout_s=5); sb = b.start(timeout_s=5)
        for label, session in [('a', sa), ('b', sb)]:
            os.environ['XAUTHORITY'] = str(session.authority)
            conn = display.Display(session.display); conn.sync(); conn.close()
            results['cases']['control_'+label] = 'connected'
        fd, pid = a.duplicate_server_pidfd(timeout_s=1)
        try: guard = OwnedXlibConnector(fd, pid, disposable=True)
        finally: os.close(fd)
        def worker(label, kind, session):
            try:
                # A's authority is intentional: a peer mismatch must precede B auth.
                os.environ['XAUTHORITY'] = str(sa.authority)
                obj = X11TargetQueries(session.display) if kind == 'query' else open_readonly_backend(session.display,{})
                obj.close()
                results['cases'][label] = 'connected'
            except Exception as e:
                results['cases'][label] = type(e).__name__ + ': ' + str(e)
        for kind in ('query','observation'):
            for label, session in [('a', sa), ('b', sb)]:
                t=threading.Thread(target=worker,args=(kind+'_'+label,kind,session)); t.start(); t.join(5)
                if t.is_alive(): raise RuntimeError('thread did not finish: '+kind+'_'+label)
        c=results['cases']
        results['pass'] = (c.get('control_a') == c.get('control_b') == 'connected' and c.get('query_a') == c.get('observation_a') == 'connected' and all('peer mismatch' in c.get(x,'') for x in ('query_b','observation_b')))
    except BaseException:
        results['exception'] = traceback.format_exc(); results['pass'] = False
    finally:
        if guard:
            try: results['cleanup'].append(['guard',guard.close()])
            except Exception as e: results['cleanup'].append(['guard_error',repr(e)])
        for name, owner in [('b',b),('a',a)]:
            try: results['cleanup'].append([name, owner.retire(timeout_s=3)])
            except Exception as e: results['cleanup'].append([name+'_error',repr(e)])
print(json.dumps(results, indent=2, default=str),flush=True)
raise SystemExit(0 if results.get('pass') and all(x[1].get('status') == 'retired' if isinstance(x[1],dict) else x[1] is True for x in results['cleanup']) else 1)
