"""One frozen public guarded MCP task through a real rootless Ubuntu xterm."""
import asyncio
import hashlib
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
sys.path.insert(0, str(ROOT))


def save(name, obj):
    (HERE/name).write_text(json.dumps(obj, indent=2)+'\n', encoding='utf-8')


async def task(report, env, td, bundle):
    from Xlib import X, display
    from PIL import Image, ImageStat
    from runtime.cli_v1.mcp_server import create_server
    observer = display.Display(':188')
    terminal = None
    terminal_fd = None
    server = None
    try:
        home = td/'home'
        home.mkdir()
        binpath = td/'bin'
        binpath.mkdir()
        shutil.copyfile(HERE/'record_helper.py', binpath/'record')
        (binpath/'record').chmod(0o700)
        rc = td/'shellrc'
        rc.write_text("PS1='READY> '; export PS1\numask 077\n")
        env.update(HOME=str(home), ENV=str(rc), PATH=str(binpath)+':/usr/bin:/bin',
            AI_TASK_JOURNAL=str(HERE/'journal.jsonl'), XDG_CACHE_HOME=str(home/'.cache'))
        title = 'AI-XTERM-TASK-R01'
        command = [str(bundle/'usr/bin/xterm'), '-ut', '+bc', '-fn', 'fixed',
            '-geometry','80x24+20+20','-title',title,'-e','/bin/sh','-i']
        with (HERE/'xterm.txt').open('wb') as log:
            terminal = subprocess.Popen(command, env=env, cwd=home,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        terminal_fd = os.pidfd_open(terminal.pid)
        report.update(xterm_pid=terminal.pid, xterm_command=command,
            xterm_stat=Path('/proc/'+str(terminal.pid)+'/stat').read_text())
        window = None
        deadline = time.monotonic()+5
        while time.monotonic() < deadline:
            if terminal.poll() is not None:
                raise RuntimeError('xterm exited before mapped window')
            for candidate in observer.screen().root.query_tree().children:
                if candidate.get_wm_name() == title and candidate.get_attributes().map_state == X.IsViewable:
                    window = candidate
                    break
            if window is not None:
                break
            await asyncio.sleep(0.05)
        assert window is not None, 'owned xterm window not found'
        geometry = window.get_geometry()
        report['window'] = {'id':window.id,'x':geometry.x,'y':geometry.y,
                            'width':geometry.width,'height':geometry.height,
                            'wm_class':window.get_wm_class()}
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        observer.screen().root.warp_pointer(geometry.x+18, geometry.y+14)
        observer.sync()
        await asyncio.sleep(1.0)
        report['initial_keymap_hex'] = bytes(observer.query_keymap()).hex()
        assert not any(bytes.fromhex(report['initial_keymap_hex']))
        assert not (HERE/'journal.jsonl').exists()
        server = create_server({'terminal':window.id}, HERE/'mcp',
            session_mode='guarded-x11', display_name=':188', guarded_process_identity=True)
        async def call(name, args, label):
            reply = await asyncio.wait_for(server.call_tool(name, args), timeout=15)
            save(label+'-reply-0.json', reply.model_dump(mode='json'))
            row = json.loads(reply.content[0].text)
            for index in range(1, 61):
                if row.get('status') != 'pending':
                    return row
                await asyncio.sleep(0.05)
                reply = await asyncio.wait_for(server.call_tool('interface_results',
                    {'call_id':row['call_id']}), timeout=5)
                save(label+'-reply-'+str(index)+'.json', reply.model_dump(mode='json'))
                row = json.loads(reply.content[0].text)
            raise TimeoutError('public result polling exhausted')
        observed = await call('interface_guarded_observe', {}, 'observe')
        assert observed['status'] == 'observed', observed
        report['source_binding'] = observed['source']['pointer_binding']
        artifact = observed['observation_report']['observation']['artifact']
        image = Image.open(artifact['path']).convert('RGB')
        point = [geometry.x+18, geometry.y+14]
        box = [point[0]-12,point[1]-12,point[0]+12,point[1]+12]
        report['prompt_anchor'] = {'point':point,'box':box,
            'stddev':ImageStat.Stat(image.crop(box)).stddev}
        assert max(report['prompt_anchor']['stddev']) >= 8
        minted = await call('interface_guarded_mint', {'alias':'prompt',
            'source_sequence':observed['source']['sequence'],'point':point,
            'region_size':[24,24]}, 'mint')
        assert minted['status'] == 'minted', minted
        report['input_started_ns'] = time.monotonic_ns()
        report['input_result'] = await call('interface_guarded_input',
            {'alias':'prompt','offset':minted['offset'],'interaction':'keyboard',
             'observe_after':False,'wait_for_result_ms':10000,
             'tail':[{'op':'text','text':'record a1'},{'op':'key_chord','keys':['Return']}]}, 'input')
        report['input_returned_ns'] = time.monotonic_ns()
        deadline = time.monotonic()+2
        while not (HERE/'journal.done.json').exists() and time.monotonic() < deadline:
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.25)
        report['oracle_read_started_ns'] = time.monotonic_ns()
        rows = [json.loads(line) for line in (HERE/'journal.jsonl').read_text().splitlines()]
        done = json.loads((HERE/'journal.done.json').read_text())
        report['oracle_read_completed_ns'] = time.monotonic_ns()
        report['journal_rows'] = rows
        report['application_commit'] = done
        report['final_keymap_hex'] = bytes(observer.query_keymap()).hex()
        report['task_success'] = (len(rows) == 1 and rows[0]['argv'] == ['a1']
            and rows[0]['stdin_tty'] and rows[0]['stdout_tty']
            and (rows[0]['ppid'] == terminal.pid or rows[0]['parent_ppid'] == terminal.pid))
        assert report['input_result']['status'] == 'completed', report['input_result']
        assert report['task_success'] and not any(bytes.fromhex(report['final_keymap_hex']))
        report['close'] = await call('interface_close', {}, 'close')
        assert report['close']['status'] == 'closed', report['close']
        server = None
        report['status'] = 'PASS_XTERM_TASK_SCOPED'
    finally:
        if server is not None:
            try:
                reply = await asyncio.wait_for(server.call_tool('interface_close', {}), timeout=5)
                save('exception-close.json', reply.model_dump(mode='json'))
            except BaseException as error:
                report['close_cleanup_error'] = repr(error)
        observer.close()
        if terminal_fd is not None:
            try:
                signal.pidfd_send_signal(terminal_fd, signal.SIGTERM)
                report['xterm_cleanup_exit_code'] = terminal.wait(timeout=5)
            except BaseException as error:
                report['xterm_cleanup_error'] = repr(error)
                report['status'] = 'FAIL_CLEANUP'
                signal.pidfd_send_signal(terminal_fd, signal.SIGKILL)
                report['xterm_kill_exit_code'] = terminal.wait(timeout=5)
            os.close(terminal_fd)
        elif terminal is not None:
            terminal.terminate()
            report['unpinned_xterm_exit_code'] = terminal.wait(timeout=5)


def main():
    for name, expected in json.loads((HERE/'SOURCES.json').read_text()).items():
        assert hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() == expected, name
    for name, expected in json.loads((HERE/'native-binaries.json').read_text()).items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
    for name in ('/tmp/.X188-lock','/tmp/.X11-unix/X188'):
        assert not Path(name).exists(), name
    with (HERE/'attempt-started.json').open('x') as f:
        json.dump({'started_ns':time.monotonic_ns(),
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()},f)
    report = {'status':'FAIL','model_calls':0}
    proc = None
    pidfd = None
    def deadline(_signum, _frame):
        report['deadline_triggered'] = True
        if pidfd is not None:
            try:
                signal.pidfd_send_signal(pidfd, signal.SIGCONT)
                signal.pidfd_send_signal(pidfd, signal.SIGTERM)
            except OSError:
                pass
        raise TimeoutError('45 second owned experiment deadline')
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(45)
    try:
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
        os.nice(10)
        with tempfile.TemporaryDirectory(prefix='ai-xterm-task-r01-') as temp:
            td = Path(temp)
            auth = td/'Xauthority'
            auth.touch(mode=0o600)
            subprocess.run(['/usr/bin/xauth','-f',str(auth),'add',':188','.',secrets.token_hex(16)],
                capture_output=True, check=True, timeout=5)
            bundle = Path('/home/user/.cache/agent-interface/xterm-20261023-r01/root')
            env = dict(os.environ, DISPLAY=':188', XAUTHORITY=str(auth), LC_ALL='C',
                LD_LIBRARY_PATH=str(bundle/'usr/lib/x86_64-linux-gnu'),
                XAPPLRESDIR=str(bundle/'etc/X11/app-defaults'))
            env.pop('WAYLAND_DISPLAY',None)
            os.environ.update(DISPLAY=':188',XAUTHORITY=str(auth))
            os.environ.pop('WAYLAND_DISPLAY',None)
            with (HERE/'xvfb.txt').open('wb') as log:
                proc = subprocess.Popen(['/usr/bin/Xvfb',':188','-screen','0','1024x768x24',
                    '-nolisten','tcp','-auth',str(auth)],stdout=log,stderr=subprocess.STDOUT,env=env)
                pidfd = os.pidfd_open(proc.pid)
                report['xvfb_pid'] = proc.pid
                report['xvfb_stat'] = Path('/proc/'+str(proc.pid)+'/stat').read_text()
                save('process-started.json',report)
                time.sleep(0.5)
                assert proc.poll() is None
                asyncio.run(task(report,env,td,bundle))
    except BaseException as error:
        report.update(status='FAIL',error=repr(error),traceback=traceback.format_exc())
    finally:
        if pidfd is not None:
            try:
                signal.pidfd_send_signal(pidfd,signal.SIGCONT)
                signal.pidfd_send_signal(pidfd,signal.SIGTERM)
                report['xvfb_cleanup_exit_code'] = proc.wait(timeout=5)
            except BaseException as error:
                report.update(status='FAIL_CLEANUP',server_cleanup_error=repr(error))
                signal.pidfd_send_signal(pidfd,signal.SIGKILL)
                report['xvfb_kill_exit_code'] = proc.wait(timeout=5)
            os.close(pidfd)
        elif proc is not None:
            proc.terminate()
            report['unpinned_xvfb_exit_code'] = proc.wait(timeout=5)
        report['ended_ns'] = time.monotonic_ns()
        signal.alarm(0)
        save('result.json',report)
    print(json.dumps({'status':report['status'],'error':report.get('error')}))
    return 0 if report['status'] == 'PASS_XTERM_TASK_SCOPED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
