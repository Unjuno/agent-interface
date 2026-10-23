"""Read-only xterm/PTY launch qualification on its own authenticated Xvfb."""
import asyncio
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(HERE))
import trial


async def main_async():
    from Xlib import display
    bundle = Path('/home/user/.cache/agent-interface/xterm-20261023-r01/root')
    report = {'status':'RUNNING','display':':190','started_ns':time.monotonic_ns(),
              'input_calls':0,'task_effects':0}
    server = observer = None
    xvfb = xterm = None
    xvfb_fd = xterm_fd = None
    xvfb_log = xterm_log = None
    old_display, old_auth = os.environ.get('DISPLAY'), os.environ.get('XAUTHORITY')
    try:
        for path in ('/tmp/.X190-lock','/tmp/.X11-unix/X190'):
            if Path(path).exists():
                raise RuntimeError('private preflight display :190 already occupied')
        auth_dir = Path(tempfile.mkdtemp(prefix='ai-xterm-app-preflight-'))
        auth = auth_dir/'Xauthority'
        auth.touch(mode=0o600)
        subprocess.run(['/usr/bin/xauth','-f',str(auth),'add',':190','.',secrets.token_hex(16)],
                       capture_output=True,check=True,timeout=5)
        os.environ.update(DISPLAY=':190',XAUTHORITY=str(auth))
        xvfb_log=(HERE/'xvfb-preflight-r02.log').open('wb')
        xvfb=subprocess.Popen(['/usr/bin/Xvfb',':190','-screen','0','1024x768x24',
            '-nolisten','tcp','-auth',str(auth)],stdout=xvfb_log,stderr=subprocess.STDOUT,
            start_new_session=True)
        xvfb_fd=os.pidfd_open(xvfb.pid)
        report['xvfb_pid']=xvfb.pid
        report['xvfb_sha256']=__import__('hashlib').sha256(Path('/usr/bin/Xvfb').read_bytes()).hexdigest()
        await asyncio.sleep(.4)
        observer=display.Display(':190')
        report['xvfb_vendor']=observer.display.info.vendor
        root=HERE/'preflight-r02-attempt'
        journal=HERE/'preflight-r02-journal.jsonl'
        xterm,xterm_log,env,command=trial.launch_xterm(bundle,'AI-XTERM-PREFLIGHT-R03',journal,auth,root,':190')
        xterm_fd=os.pidfd_open(xterm.pid)
        report['xterm_pid']=xterm.pid
        report['xterm_command']=command
        window=await trial.find_window(observer,'AI-XTERM-PREFLIGHT-R03',xterm,timeout=5)
        geometry=window.get_geometry()
        report['window']={'xid':window.id,'title':window.get_wm_name(),
            'wm_class':window.get_wm_class(),'geometry':[geometry.x,geometry.y,geometry.width,geometry.height],
            'map_state':window.get_attributes().map_state}
        child_rows=subprocess.run(['ps','-eo','pid,ppid,pgid,stat,comm,args'],
            text=True,capture_output=True,check=True).stdout.splitlines()[1:]
        shell_rows=[]
        for line in child_rows:
            fields=line.split(None,5)
            if len(fields)>=6 and int(fields[1])==xterm.pid:
                shell_pid=int(fields[0])
                fd0=Path('/proc',str(shell_pid),'fd/0')
                shell_rows.append({'pid':shell_pid,'comm':fields[4],
                    'stdin_tty':os.readlink(fd0) if fd0.exists() else None,
                    'pgrp':int(fields[2])})
        report['direct_children']=shell_rows
        report['keymap_hex']=bytes(observer.query_keymap()).hex()
        report['journal_exists_without_input']=journal.exists()
        report['mapped_xterm_with_interactive_pty']=bool(
            report['window']['wm_class'][1]=='XTerm' and shell_rows
            and isinstance(shell_rows[0]['stdin_tty'],str)
            and shell_rows[0]['stdin_tty'].startswith('/dev/pts/'))
        if not report['mapped_xterm_with_interactive_pty']:
            raise RuntimeError('xterm window or interactive PTY did not qualify')
        if any(bytes.fromhex(report['keymap_hex'])) or journal.exists():
            raise RuntimeError('preflight unexpectedly had key state or task effect')
        report['status']='PASS_XTERM_MAPPED_INTERACTIVE_PTY_NO_INPUT'
    except BaseException as error:
        report.update(status='FAIL',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
    finally:
        cleanup_errors=[]
        for name,process,pidfd,log in (('xterm',xterm,xterm_fd,xterm_log),):
            if process is None:
                continue
            try:
                if pidfd is not None and os.getpgid(process.pid)==process.pid:
                    os.killpg(process.pid,signal.SIGTERM)
                    report[name+'_exit_code']=process.wait(timeout=5)
                    end=time.monotonic()+2
                    while time.monotonic()<end and trial.pids_in_group(process.pid):
                        await asyncio.sleep(.05)
                    report[name+'_remaining_session_pids']=trial.pids_in_group(process.pid)
                else:
                    process.terminate()
                    report[name+'_exit_code']=process.wait(timeout=5)
            except BaseException as error:
                report[name+'_cleanup_error']=repr(error)
                try:
                    if pidfd is not None:
                        signal.pidfd_send_signal(pidfd,signal.SIGKILL)
                        report[name+'_kill_exit_code']=process.wait(timeout=5)
                except BaseException as second:
                    report[name+'_kill_error']=repr(second)
            finally:
                if pidfd is not None:
                    os.close(pidfd)
                if log is not None:
                    log.close()
        if observer is not None:
            try:
                observer.close()
            except BaseException as error:
                cleanup_errors.append('observer close: '+repr(error))
        for name,process,pidfd,log in (('xvfb',xvfb,xvfb_fd,xvfb_log),):
            if process is None:
                continue
            try:
                if pidfd is not None and os.getpgid(process.pid)==process.pid:
                    os.killpg(process.pid,signal.SIGTERM)
                    report[name+'_exit_code']=process.wait(timeout=5)
                    end=time.monotonic()+2
                    while time.monotonic()<end and trial.pids_in_group(process.pid):
                        await asyncio.sleep(.05)
                    report[name+'_remaining_session_pids']=trial.pids_in_group(process.pid)
                else:
                    process.terminate()
                    report[name+'_exit_code']=process.wait(timeout=5)
            except BaseException as error:
                report[name+'_cleanup_error']=repr(error)
                try:
                    if pidfd is not None:
                        signal.pidfd_send_signal(pidfd,signal.SIGKILL)
                        report[name+'_kill_exit_code']=process.wait(timeout=5)
                except BaseException as second:
                    report[name+'_kill_error']=repr(second)
            finally:
                if pidfd is not None:
                    os.close(pidfd)
                if log is not None:
                    log.close()
        if old_display is None: os.environ.pop('DISPLAY',None)
        else: os.environ['DISPLAY']=old_display
        if old_auth is None: os.environ.pop('XAUTHORITY',None)
        else: os.environ['XAUTHORITY']=old_auth
        if 'auth_dir' in locals(): shutil.rmtree(auth_dir,ignore_errors=True)
        report['cleanup_errors']=cleanup_errors
        report['display_lock_absent']=not Path('/tmp/.X190-lock').exists()
        report['display_socket_absent']=not Path('/tmp/.X11-unix/X190').exists()
        report['journal_exists_after_cleanup']=(HERE/'preflight-r02-journal.jsonl').exists()
        report['ended_ns']=time.monotonic_ns()
        (HERE/'preflight-r02.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report


if __name__=='__main__':
    result=asyncio.run(main_async())
    print(json.dumps({'status':result['status'],'wm_class':result.get('window',{}).get('wm_class'),
        'pty':result.get('direct_children')}))
    raise SystemExit(0 if result['status']=='PASS_XTERM_MAPPED_INTERACTIVE_PTY_NO_INPUT' else 1)
