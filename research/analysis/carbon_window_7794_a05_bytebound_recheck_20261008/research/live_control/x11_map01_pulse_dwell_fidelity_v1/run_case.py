import argparse, json, os, pathlib, signal, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent

def wait_file(path, proc, timeout_s=5.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if path.exists():
            return
        if proc.poll() is not None:
            raise RuntimeError(f'process exited before {path.name}: rc={proc.returncode}')
        time.sleep(0.02)
    raise TimeoutError(str(path))

def terminate(proc):
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill(); proc.wait(timeout=2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--case-id', required=True)
    ap.add_argument('--display-num', required=True, type=int)
    ap.add_argument('--out-root', required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out_root) / args.case_id
    out.mkdir(parents=True, exist_ok=False)
    sock = pathlib.Path(f'/tmp/.X11-unix/X{args.display_num}')
    if sock.exists():
        raise RuntimeError(f'display socket already exists: {sock}')
    xauth = out / 'xauth'; xauth.write_bytes(b'')
    env = os.environ.copy(); env.update({'DISPLAY': f':{args.display_num}', 'XAUTHORITY': str(xauth), 'OUT': str(out)})
    xvfb_log = (out / 'xvfb.log').open('wb')
    recv_log = (out / 'receiver.log').open('wb')
    xvfb = recv = None
    try:
        xvfb = subprocess.Popen(['Xvfb', f':{args.display_num}', '-screen', '0', '800x600x24', '-ac'], stdout=xvfb_log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and not sock.exists():
            if xvfb.poll() is not None: raise RuntimeError(f'Xvfb rc={xvfb.returncode}')
            time.sleep(0.02)
        if not sock.exists(): raise TimeoutError(f'Xvfb socket {sock}')
        recv = subprocess.Popen([sys.executable, str(HERE/'receiver.py')], env=env, stdout=recv_log, stderr=subprocess.STDOUT)
        wait_file(out/'ready', recv)
        ctl = subprocess.run([sys.executable, str(HERE/'controller.py')], env=env, capture_output=True, text=True, timeout=8)
        (out/'controller.stdout').write_text(ctl.stdout)
        (out/'controller.stderr').write_text(ctl.stderr)
        if ctl.returncode != 0: raise RuntimeError(f'controller rc={ctl.returncode}: {ctl.stderr}')
        time.sleep(0.100)
        if not (out/'events.json').exists(): raise RuntimeError('events.json absent')
        events = json.loads((out/'events.json').read_text())
        controller = json.loads((out/'controller.json').read_text())
        receipt = {
            'case_id': args.case_id,
            'display_num': args.display_num,
            'event_count': len(events),
            'focus_verified': controller['focus_after'] == controller['window_id'],
            'final_right_down': controller['final_right_down'],
        }
        (out/'case_receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
        print(json.dumps(receipt, sort_keys=True))
    finally:
        terminate(recv); terminate(xvfb); recv_log.close(); xvfb_log.close()

if __name__ == '__main__': main()
