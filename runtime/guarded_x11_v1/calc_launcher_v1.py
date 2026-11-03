"""Parent-held launch and exact-process exit custody for one Calc artifact.

The default mode retains the GUI as the direct child. A narrowly scoped Debian
LibreOffice 7.4.7 mode can instead retain ``soffice``/``oosplash`` as the Popen
child and separately bind the exact ``soffice.bin`` GUI child. It accepts the
launcher exit code only when the pinned launcher package, parent/child
identities, command line and observed child sequence match that contract.
"""
from copy import deepcopy
import os
from pathlib import Path
import re
import subprocess
import time

from .calc_task_artifact_v1 import CalcTaskArtifact, _BLANK_FODS, _read_regular
from .process_identity import process_generation_from_identity


_EXIT_SCHEMA = 'agent-interface/calc-target-exit-receipt-v1'
_WRAPPED_EXIT_SCHEMA = 'agent-interface/calc-target-exit-receipt-v2'
_PROFILE_DIR = 'calc-launch-profile'
_LIBREOFFICE_PACKAGE_VERSION = '4:7.4.7-1+deb12u14'


def _linux_start_ticks(pid):
    """Read the kernel process start tick for one live local PID."""
    if type(pid) is not int or pid <= 0:
        raise ValueError('invalid Calc process PID')
    stat = Path('/proc', str(pid), 'stat').read_text(encoding='ascii')
    opening, closing = stat.find('('), stat.rfind(')')
    if opening < 1 or closing <= opening or stat[:opening].strip() != str(pid):
        raise RuntimeError('Calc process stat identity mismatch')
    fields = stat[closing + 1:].split()
    if (len(fields) <= 19 or fields[0] in ('Z', 'X', 'x')
            or not fields[19].isascii() or not fields[19].isdigit()):
        raise RuntimeError('Calc process start tick unavailable')
    return int(fields[19])


def _linux_cmdline(pid):
    raw = Path('/proc', str(pid), 'cmdline').read_bytes()
    if not raw or not raw.endswith(b'\0'):
        raise RuntimeError('Calc process command line unavailable')
    return tuple(part.decode('utf-8', 'strict')
                 for part in raw[:-1].split(b'\0'))


def _linux_parent_pid(pid):
    stat = Path('/proc', str(pid), 'stat').read_text(encoding='ascii')
    opening, closing = stat.find('('), stat.rfind(')')
    if opening < 1 or closing <= opening or stat[:opening].strip() != str(pid):
        raise RuntimeError('Calc process parent identity mismatch')
    fields = stat[closing + 1:].split()
    if len(fields) <= 1 or not fields[1].isascii() or not fields[1].isdigit():
        raise RuntimeError('Calc process parent PID unavailable')
    return int(fields[1])


def _linux_executable(pid):
    return str(Path('/proc', str(pid), 'exe').resolve(strict=True))


def _linux_direct_children(pid):
    """Enumerate unreaped children created by every thread in one process.

    Linux records a forked child in the creating task's ``children`` file;
    reading only the thread-group leader misses children launched by a worker
    thread (as LibreOffice's oosplash does).
    """
    if type(pid) is not int or pid <= 0:
        raise ValueError('invalid Calc launcher PID')
    task_root = Path('/proc', str(pid), 'task')
    task_ids = []
    for entry in task_root.iterdir():
        if entry.name.isascii() and entry.name.isdigit() and entry.is_dir():
            task_ids.append(int(entry.name))
    if pid not in task_ids:
        raise RuntimeError('Calc launcher thread group is unavailable')
    children = set()
    for task_id in task_ids:
        raw = Path(task_root, str(task_id), 'children').read_text(
            encoding='ascii').strip()
        for value in raw.split():
            if not value.isascii() or not value.isdigit() or int(value) <= 0:
                raise RuntimeError('Calc launcher child identity is malformed')
            children.add(int(value))
    return tuple(sorted(children))


def _debian_libreoffice_version():
    result = subprocess.run(
        ['dpkg-query', '-W', '-f=${Version}', 'libreoffice-core'],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=2)
    return result.stdout.strip()


class CalcLaunchSupervisor:
    """Launch one reserved document and retain its exact direct child handle.

    executable is server configuration, never request data. The one-shot
    instance retains the Popen handle, PID and kernel start tick in parent
    memory. A target identity may be bound once after XRes/window admission.
    Only a clean wait on that same direct GUI process can produce the exact
    target-exit receipt consumed by the existing artifact verifier.
    """

    def __init__(self, executable, *, popen_factory=subprocess.Popen,
                 start_ticks_reader=_linux_start_ticks,
                 cmdline_reader=_linux_cmdline, clock=time.monotonic_ns,
                 custody_mode='direct-child', gui_executable=None,
                 oosplash_executable=None,
                 package_version_reader=_debian_libreoffice_version,
                 parent_pid_reader=_linux_parent_pid,
                 executable_reader=_linux_executable,
                 direct_children_reader=_linux_direct_children,
                 monotonic=time.monotonic, sleep=time.sleep):
        executable = Path(executable)
        if not executable.is_absolute():
            raise ValueError('Calc executable must be an absolute server-configured path')
        self.executable = executable.resolve(strict=True)
        if (self.executable.is_symlink() or not self.executable.is_file()
                or not os.access(self.executable, os.X_OK)):
            raise ValueError('Calc executable must resolve to an executable regular file')
        if custody_mode not in ('direct-child', 'libreoffice-oosplash-child'):
            raise ValueError('unsupported Calc process custody mode')
        if not callable(popen_factory) or not callable(start_ticks_reader) \
                or not callable(cmdline_reader) or not callable(clock) \
                or not callable(monotonic) or not callable(sleep):
            raise ValueError('Calc launch dependencies must be callable')
        if custody_mode == 'libreoffice-oosplash-child':
            gui_executable = Path(gui_executable) if gui_executable else None
            oosplash_executable = (Path(oosplash_executable)
                                   if oosplash_executable else None)
            if (gui_executable is None or oosplash_executable is None
                    or not gui_executable.is_absolute()
                    or not oosplash_executable.is_absolute()
                    or not callable(package_version_reader)
                    or not callable(parent_pid_reader)
                    or not callable(executable_reader)
                    or not callable(direct_children_reader)):
                raise ValueError('pinned LibreOffice child-custody dependencies are required')
        else:
            gui_executable = oosplash_executable = None
        self._popen_factory = popen_factory
        self._start_ticks_reader = start_ticks_reader
        self._cmdline_reader = cmdline_reader
        self._clock = clock
        self._custody_mode = custody_mode
        self._gui_executable = gui_executable
        self._oosplash_executable = oosplash_executable
        self._package_version_reader = package_version_reader
        self._parent_pid_reader = parent_pid_reader
        self._executable_reader = executable_reader
        self._direct_children_reader = direct_children_reader
        self._monotonic = monotonic
        self._sleep = sleep
        self._launch_attempted = False
        self._process = None
        self._artifact = None
        self._profile_dir = None
        self._stdout = None
        self._pid = None
        self._start_ticks = None
        self._target_identity = None
        self._package_version = None
        self._replacement_observed = False
        self._exit_code = None
        self._exit_observed_ns = None
        self._exit_receipt = None

    @property
    def pid(self):
        return self._pid

    @property
    def start_ticks(self):
        return self._start_ticks

    @property
    def launched(self):
        return self._process is not None

    def launch(self, artifact):
        """Start the configured GUI with exactly the reserved FODS and profile."""
        if self._launch_attempted:
            raise RuntimeError('Calc launch is one-shot')
        self._launch_attempted = True
        if self._custody_mode == 'libreoffice-oosplash-child':
            self._package_version = self._package_version_reader()
            if self._package_version != _LIBREOFFICE_PACKAGE_VERSION:
                raise ValueError('LibreOffice child-exit contract package version mismatch')
        if not isinstance(artifact, CalcTaskArtifact):
            raise TypeError('a server-created CalcTaskArtifact is required')
        if (artifact.process_generation is not None
                or artifact.window_generation is not None
                or artifact._save_request_id is not None):
            raise ValueError('Calc artifact must be fresh and unbound before launch')
        data, identity = _read_regular(artifact.path, max_bytes=64 * 1024 * 1024)
        if (data != _BLANK_FODS
                or identity != artifact._blank_identity
                or artifact.path.name != 'task-artifact.fods'
                or artifact.path.parent != artifact.call_root):
            raise ValueError('reserved Calc artifact is not the original blank file')

        profile_dir = artifact.call_root / _PROFILE_DIR
        profile_dir.mkdir(mode=0o700, exist_ok=False)
        self._profile_dir = profile_dir
        self._artifact = artifact
        log_path = artifact.call_root / 'calc-launch.log'
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(log_path, flags, 0o600)
        try:
            self._stdout = os.fdopen(fd, 'wb', closefd=True)
        except BaseException:
            os.close(fd)
            raise
        profile_uri = profile_dir.as_uri()
        self.argv = (
            str(self.executable),
            f'-env:UserInstallation={profile_uri}',
            '--calc', str(artifact.path),
            '--nologo', '--nodefault', '--nofirststartwizard', '--norestore')
        launch_env = os.environ.copy()
        if self._custody_mode == 'libreoffice-oosplash-child':
            # The pinned Debian/Xvfb Calc path is qualified with LibreOffice's
            # generic VCL backend. Without it, Calc maps/focuses a window but
            # the captured client surface can remain a uniform gray canvas.
            launch_env['SAL_USE_VCLPLUGIN'] = 'gen'
        try:
            self._process = self._popen_factory(
                list(self.argv), stdin=subprocess.DEVNULL,
                stdout=self._stdout, stderr=subprocess.STDOUT,
                close_fds=True, start_new_session=True, shell=False,
                env=launch_env)
            self._pid = self._process.pid
            if type(self._pid) is not int or self._pid <= 0:
                raise RuntimeError('Calc launcher returned an invalid direct-child PID')
            self._start_ticks = self._start_ticks_reader(self._pid)
            if type(self._start_ticks) is not int or self._start_ticks <= 0:
                raise RuntimeError('Calc direct-child start tick is invalid')
        except BaseException:
            self._close_log()
            raise
        return {'status':'launched','pid':self._pid,
            'start_ticks':self._start_ticks,'argv':list(self.argv),
            'environment_overrides':({'SAL_USE_VCLPLUGIN':'gen'}
                if self._custody_mode == 'libreoffice-oosplash-child' else {}),
            'artifact_path':str(artifact.path),
            'profile_directory':str(profile_dir),
            'input_dispatched':False,'task_success':None,
            'replay_allowed':False}

    def retain_initial_process_group_custody(self, owned_owner):
        """Retain launcher-only or exact-child custody immediately after spawn."""
        if (self._process is None or self._custody_mode != 'libreoffice-oosplash-child'
                or self._target_identity is not None):
            raise RuntimeError('initial Calc group custody requires one unbound LO launch')
        from .calc_process_group_v1 import (
            make_launcher_process_group_custody, make_process_group_custody,
            read_linux_process_group)
        owned_owner.get()
        owned_owner._calc_process_group_cleanup_target = self.cleanup_owned_process_group
        rows=read_linux_process_group(self._pid,self._pid)
        child=None
        try:
            child=self.validate_current_gui_child()
        except (OSError,RuntimeError,ValueError):
            custody=make_launcher_process_group_custody(
                leader_pid=self._pid,leader_start_ticks=self._start_ticks,
                group_snapshot=rows)
            status='launcher_retained'
        else:
            custody=make_process_group_custody(
                leader_pid=self._pid,leader_start_ticks=self._start_ticks,
                target_pid=child['pid'],target_start_ticks=child['start_ticks'],
                group_snapshot=rows)
            status='child_retained'
        retained=owned_owner.retain_calc_process_group_custody(custody)
        return {'status':status,'custody':retained,
            'child':child,
            'authority_granted':False,'input_dispatched':False,
            'task_success':None,'replay_allowed':False}

    def validate_current_gui_child(self):
        """Validate the sole current pinned LO child before window admission.

        LibreOffice may replace its bootstrap ``soffice.bin`` before opening
        the reserved document. This read-only check permits the caller to
        consider the current child generation for pre-review custody handoff;
        it does not bind a window, mint an exit receipt, or grant input.
        """
        if (self._process is None or self._custody_mode != 'libreoffice-oosplash-child'
                or self._target_identity is not None or self._process.poll() is not None):
            raise RuntimeError('current GUI child inspection requires an idle unbound LO launch')
        children=tuple(self._direct_children_reader(self._pid))
        if len(children)!=1:
            raise RuntimeError('exactly one current direct GUI child is required')
        pid=children[0]
        if (type(pid) is not int or pid <= 0 or pid == self._pid
                or self._parent_pid_reader(pid) != self._pid
                or self._executable_reader(pid) != str(self._gui_executable)):
            raise ValueError('current GUI child executable or parent changed')
        argv=self._cmdline_reader(pid)
        if type(argv) not in (tuple,list) or not argv:
            raise ValueError('current GUI child command line unavailable')
        profile_arg=f'-env:UserInstallation={self._profile_dir.as_uri()}'
        expected=[profile_arg,'--calc',str(self._artifact.path),'--nologo',
            '--nodefault','--nofirststartwizard','--norestore']
        splash=[value for value in argv[1:]
            if re.fullmatch(r'--splash-pipe=[0-9]+',value)]
        normalized=[value for value in argv[1:] if value not in splash]
        if (argv[0] != str(self._gui_executable) or normalized != expected
                or len(splash)>1):
            raise ValueError('current GUI child command line changed')
        ticks=self._start_ticks_reader(pid)
        if type(ticks) is not int or ticks <= 0:
            raise ValueError('current GUI child generation unavailable')
        return {'pid':pid,'start_ticks':ticks,'parent_pid':self._pid,
            'executable':str(self._gui_executable),'argv':list(argv),
            'expected_argv':[str(self._gui_executable),*expected],
            'launcher_pid':self._pid,'launcher_start_ticks':self._start_ticks,
            'package_version':self._package_version,
            'authority_granted':False,'input_dispatched':False,
            'task_success':None,'replay_allowed':False}

    def synchronize_owned_process_group(self, owned_owner):
        """Retain or advance exact pre-review custody to the current LO child."""
        child=self.validate_current_gui_child()
        from .calc_process_group_v1 import (
            make_process_group_custody, read_linux_process_group)
        rows=read_linux_process_group(self._pid,self._pid)
        current=getattr(owned_owner,'_calc_process_group_custody',None)
        if current is None:
            custody=make_process_group_custody(
                leader_pid=self._pid,leader_start_ticks=self._start_ticks,
                target_pid=child['pid'],target_start_ticks=child['start_ticks'],
                group_snapshot=rows)
            retained=owned_owner.retain_calc_process_group_custody(custody)
            return {'status':'retained','custody':retained,'child':child,
                'authority_granted':False,'input_dispatched':False,
                'task_success':None,'replay_allowed':False}
        launcher=current.get('launcher',{})
        target=current.get('target',{})
        if (launcher.get('pid')!=self._pid
                or launcher.get('start_ticks')!=self._start_ticks):
            raise ValueError('owned Calc custody belongs to another launcher generation')
        if (isinstance(target,dict) and target.get('pid')==child['pid']
                and target.get('start_ticks')==child['start_ticks']):
            observed=make_process_group_custody(
                leader_pid=self._pid,leader_start_ticks=self._start_ticks,
                target_pid=child['pid'],target_start_ticks=child['start_ticks'],
                group_snapshot=rows)
            if observed!=current:
                raise ValueError('current Calc group differs from retained custody')
            return {'status':'unchanged','custody':observed,'child':child,
                'authority_granted':False,'input_dispatched':False,
                'task_success':None,'replay_allowed':False}
        advanced=owned_owner.advance_calc_process_group_custody(
            target_pid=child['pid'],target_start_ticks=child['start_ticks'],
            gui_executable=child['executable'],expected_argv=child['expected_argv'])
        return {'status':'advanced','custody':advanced['custody'],'child':child,
            'transition':advanced['transition'],'authority_granted':False,
            'input_dispatched':False,'task_success':None,'replay_allowed':False}

    def discover_owned_window(self, owned_owner, *, title_hint, deadline_s=20.0,
                              sample_interval_s=0.15):
        """Boundedly discover one exact launched GUI window without reviewing it.

        The owner connection must already be open on a configured X11 root
        target. Process-generation custody is retained/advanced in the server
        parent before each XRes query. A title is only a query cue: this method
        never chooses a window for input, activates it, or grants authority.
        The caller must inspect the single returned candidate and explicitly
        review its XID on this same owner session before binding it for input.
        """
        if self._process is None or self._custody_mode != 'libreoffice-oosplash-child':
            raise RuntimeError('owned Calc discovery requires a launched pinned LibreOffice owner')
        if (type(title_hint) is not str or not title_hint
                or len(title_hint) > 128 or not title_hint.isprintable()):
            raise ValueError('bounded printable Calc title hint required')
        if (type(deadline_s) not in (int,float) or deadline_s <= 0
                or deadline_s > 60
                or type(sample_interval_s) not in (int,float)
                or sample_interval_s <= 0 or sample_interval_s > 1):
            raise ValueError('finite Calc discovery bounds required')
        owned_owner.get()
        owned_owner._calc_process_group_cleanup_target = self.cleanup_owned_process_group
        deadline = self._monotonic() + deadline_s
        samples=[]
        last_child=None
        while self._monotonic() < deadline:
            if self._process.poll() is not None:
                return {'status':'unknown','reason':'calc_launcher_exited_during_discovery',
                    'samples':samples,'launch_pid':self._pid,
                    'input_dispatched':False,'authority_granted':False,
                    'task_success':None,'replay_allowed':False}
            try:
                synchronized=self.synchronize_owned_process_group(owned_owner)
                child=synchronized['child']
                windows=owned_owner.windows_for_process(child['pid'],title_hint)
                rows=windows.get('windows') if isinstance(windows,dict) else None
                sample={'monotonic_ns':time.monotonic_ns(),
                    'synchronization':synchronized,
                    'query_status':windows.get('status') if isinstance(windows,dict) else None,
                    'windows':deepcopy(rows)}
                samples.append(sample)
                if type(rows) is not list:
                    raise RuntimeError('owned XRes discovery reply is malformed')
                matched=[row for row in rows
                    if isinstance(row,dict)
                    and row.get('process_pid')==child['pid']
                    and row.get('process_start_ticks')==child['start_ticks']
                    and row.get('mapped') is True]
                if len(matched)>1:
                    return {'status':'ambiguous','reason':'multiple_mapped_calc_windows',
                        'child':child,'candidates':matched,'samples':samples,
                        'input_dispatched':False,'authority_granted':False,
                        'task_success':None,'replay_allowed':False}
                if len(matched)==1:
                    candidate=matched[0]
                    return {'status':'candidate_found','child':child,
                        'candidate':deepcopy(candidate),'samples':samples,
                        'custody':deepcopy(owned_owner._calc_process_group_custody),
                        'input_dispatched':False,'authority_granted':False,
                        'task_success':None,'replay_allowed':False}
                last_child=child
            except (OSError,RuntimeError,ValueError,KeyError) as error:
                samples.append({'monotonic_ns':time.monotonic_ns(),
                    'status':'query_or_generation_unavailable',
                    'error_type':type(error).__name__,'error':str(error)[:500],
                    'child':deepcopy(last_child)})
            self._sleep(min(sample_interval_s,
                max(0,deadline-self._monotonic())))
        return {'status':'unknown','reason':'calc_window_discovery_deadline',
            'child':last_child,'samples':samples,
            'input_dispatched':False,'authority_granted':False,
            'task_success':None,'replay_allowed':False}

    def review_and_bind_owned_window(self, owned_owner, window_id, *, call_root):
        """Explicitly review one discovered window, then bind its exact generation.

        No activation is attempted. A nonfocused candidate fails closed. Fresh
        metadata is read before and after the owner's explicit review; XID,
        process/window incarnation and process generation must remain exact.
        """
        if self._target_identity is not None:
            raise RuntimeError('Calc launch supervisor already has a reviewed target')
        child=self.validate_current_gui_child()
        custody=deepcopy(getattr(owned_owner,'_calc_process_group_custody',None))
        if (not isinstance(custody,dict)
                or custody.get('launcher',{}).get('pid')!=self._pid
                or custody.get('launcher',{}).get('start_ticks')!=self._start_ticks):
            return {'status':'needs_review','reason':'parent_process_group_custody_unavailable',
                'input_dispatched':False,'authority_granted':False,
                'task_success':None,'replay_allowed':False}
        candidates=owned_owner.windows_for_process(
            child['pid'],self._artifact.path.name)
        rows=candidates.get('windows') if isinstance(candidates,dict) else None
        if type(rows) is not list:
            return {'status':'needs_review','reason':'owned_window_candidates_unavailable',
                'input_dispatched':False,'authority_granted':False,
                'task_success':None,'replay_allowed':False}
        matched=[row for row in rows if isinstance(row,dict)
            and row.get('xid')==window_id and row.get('mapped') is True]
        if len(matched)!=1:
            return {'status':'needs_review','reason':'window_not_unique_discovered_candidate',
                'candidate_count':len(matched),'input_dispatched':False,
                'authority_granted':False,'task_success':None,'replay_allowed':False}
        if (matched[0].get('process_pid')!=child['pid']
                or matched[0].get('process_start_ticks')!=child['start_ticks']):
            return {'status':'needs_review','reason':'candidate_process_generation_changed',
                'input_dispatched':False,'authority_granted':False,
                'task_success':None,'replay_allowed':False}
        before=owned_owner.inspect_window_metadata(window_id).get('window_metadata')
        identity_fields=('xid','process_pid','process_start_ticks','process_generation',
            'process_incarnation','window_incarnation')
        if (not isinstance(before,dict)
                or any(before.get(field)!=matched[0].get(field)
                    for field in identity_fields)
                or before.get('mapped') is not True
                or before.get('focused_before') is not True
                or before.get('focused_after') is not True):
            return {'status':'needs_review','reason':'fresh_candidate_metadata_mismatch_or_unfocused',
                'candidate_metadata':before,'custody':custody,
                'input_dispatched':False,'authority_granted':False,
                'task_success':None,'replay_allowed':False}
        review=owned_owner.invoke_guarded('guarded_review_window',
            {'window_id':window_id},call_root=call_root)
        if not isinstance(review,dict) or review.get('status')!='reviewed':
            return {'status':'needs_review','reason':'explicit_window_review_failed',
                'review':review,'input_dispatched':False,'authority_granted':False,
                'task_success':None,'replay_allowed':False}
        after=owned_owner.inspect_window_metadata(window_id).get('window_metadata')
        if (not isinstance(after,dict)
                or any(after.get(field)!=before.get(field) for field in identity_fields)
                or after.get('mapped') is not True
                or after.get('focused_before') is not True
                or after.get('focused_after') is not True):
            return {'status':'needs_review','reason':'window_changed_during_explicit_review',
                'review':review,'before':before,'after':after,
                'input_dispatched':False,'authority_granted':False,
                'task_success':None,'replay_allowed':False}
        bound=self.bind_xres_target(after)
        return {'status':'reviewed','candidate':matched[0],
            'review':review,'fresh_metadata':after,'binding':bound,
            'input_dispatched':False,'authority_granted':False,
            'task_success':None,'replay_allowed':False}

    def cleanup_owned_process_group(self, custody):
        """Clean only this retained launch group and reap its direct launcher.

        Reaping the exact Popen child after each bounded signal lets the group
        verifier distinguish a zombie launcher from a still-running member.
        The cleanup result remains separate from clean target exit and task
        effect receipts.
        """
        if self._process is None or not isinstance(custody,dict):
            raise ValueError('owned Calc launch and custody are required')
        if (custody.get('pgid')!=self._pid
                or custody.get('session_id')!=self._pid):
            raise ValueError('Calc cleanup custody belongs to another launch group')
        from .calc_process_group_v1 import cleanup_process_group
        group_signal=getattr(os,'killpg',None)
        if not callable(group_signal):
            raise OSError('process-group signaling is unavailable')

        def signal_and_reap(pgid, sig):
            if pgid!=self._pid:
                raise OSError('refusing to signal another process group')
            group_signal(pgid,sig)
            try:
                self._process.wait(timeout=0.25)
            except subprocess.TimeoutExpired:
                pass

        return cleanup_process_group(custody,killpg=signal_and_reap)

    def bind_xres_target(self, target_metadata):
        """Bind a reviewed window to the direct GUI or configured LO child."""
        if self._process is None or self._target_identity is not None:
            raise RuntimeError('Calc target binding requires one launched, unbound process')
        fields = {'xid','process_pid','process_start_ticks','process_generation',
                  'window_incarnation','mapped','focused_before','focused_after'}
        if type(target_metadata) is not dict or not fields.issubset(target_metadata):
            raise ValueError('complete parent-observed XRes/window metadata is required')
        xid = target_metadata['xid']
        pid = target_metadata['process_pid']
        ticks = target_metadata['process_start_ticks']
        generation = target_metadata['process_generation']
        expected_pid = (pid == self._pid if self._custody_mode == 'direct-child'
                        else pid != self._pid)
        if (type(xid) is not int or not 1 < xid < 2**32
                or not expected_pid or type(ticks) is not int or ticks <= 0
                or type(generation) is not str
                or generation != process_generation_from_identity(xid,pid,ticks)
                or target_metadata['mapped'] is not True
                or target_metadata['focused_before'] is not True
                or target_metadata['focused_after'] is not True
                or type(target_metadata['window_incarnation']) is not str
                or len(target_metadata['window_incarnation']) != 64):
            raise ValueError('XRes target is not this live Calc GUI process')
        try:
            live_ticks = self._start_ticks_reader(pid)
        except (OSError, RuntimeError, ValueError) as exc:
            raise ValueError('XRes target is not this live Calc GUI process') from exc
        if live_ticks != ticks:
            raise ValueError('XRes target is not this live Calc process generation')
        argv = self._cmdline_reader(pid)
        profile_arg = f'-env:UserInstallation={self._profile_dir.as_uri()}'
        if self._custody_mode == 'direct-child':
            valid_argv = (type(argv) in (tuple,list) and bool(argv)
                and str(self.executable) in argv[0]
                and str(self._artifact.path) in argv
                and profile_arg in argv)
        else:
            expected_args = [profile_arg, '--calc', str(self._artifact.path),
                '--nologo', '--nodefault', '--nofirststartwizard', '--norestore']
            valid_argv = False
            if type(argv) in (tuple,list) and argv:
                actual_args = list(argv[1:])
                splash_args = [value for value in actual_args
                               if re.fullmatch(r'--splash-pipe=[0-9]+', value)]
                base_args = [value for value in actual_args
                             if value not in splash_args]
                valid_argv = (
                    argv[0] == str(self._gui_executable)
                    and base_args == expected_args
                    and len(splash_args) <= 1
                    and self._parent_pid_reader(pid) == self._pid
                    and self._executable_reader(self._pid)
                        == str(self._oosplash_executable)
                    and tuple(self._direct_children_reader(self._pid)) == (pid,))
        if not valid_argv:
            raise ValueError('Calc GUI command line or launcher custody mismatch')
        if self._process.poll() is not None:
            raise RuntimeError('Calc GUI exited before target binding')
        self._target_identity = {
            'xid':xid,'pid':pid,'start_ticks':ticks,
            'process_generation':generation,
            'window_generation':target_metadata['window_incarnation']}
        if self._custody_mode == 'libreoffice-oosplash-child':
            self._target_identity.update({
                'launcher_pid':self._pid,
                'launcher_start_ticks':self._start_ticks,
                'launcher_executable':str(self._oosplash_executable),
                'launcher_package_version':self._package_version})
        return deepcopy(self._target_identity)

    def wait_for_verified_exit(self, *, timeout_s):
        """Wait boundedly; return a receipt only for a clean exact-child exit."""
        if self._process is None or self._target_identity is None:
            return {'status':'unknown','reason':'exact_calc_target_not_bound',
                    'task_success':None,'replay_allowed':False}
        if (type(timeout_s) not in (int,float) or timeout_s <= 0
                or timeout_s > 300):
            raise ValueError('Calc exit wait must be finite and <=300 seconds')
        if self._exit_receipt is not None:
            return deepcopy(self._exit_receipt)
        if self._custody_mode == 'direct-child':
            try:
                code = self._process.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                return {'status':'unknown','reason':'calc_target_exit_timeout',
                        'pid':self._pid,'task_success':None,'replay_allowed':False}
        else:
            deadline = self._monotonic() + timeout_s
            code = None
            while self._monotonic() < deadline:
                code = self._process.poll()
                if code is not None:
                    try:
                        self._process.wait(timeout=0)
                    except subprocess.TimeoutExpired:
                        code = None
                    else:
                        break
                try:
                    children = tuple(self._direct_children_reader(self._pid))
                except (OSError, RuntimeError, ValueError):
                    return {'status':'unknown','reason':'launcher_child_sequence_unavailable',
                            'pid':self._pid,'task_success':None,'replay_allowed':False}
                if any(child != self._target_identity['pid'] for child in children):
                    self._replacement_observed = True
                    return {'status':'unknown','reason':'calc_gui_child_replaced',
                            'pid':self._target_identity['pid'],
                            'task_success':None,'replay_allowed':False}
                self._sleep(min(0.01, max(0, deadline - self._monotonic())))
            if code is None:
                return {'status':'unknown','reason':'calc_target_exit_timeout',
                        'pid':self._pid,'task_success':None,'replay_allowed':False}
            try:
                current_ticks = self._start_ticks_reader(self._target_identity['pid'])
            except (OSError, RuntimeError, ValueError):
                current_ticks = None
            if current_ticks == self._target_identity['start_ticks']:
                return {'status':'unknown','reason':'calc_gui_child_still_live',
                        'pid':self._target_identity['pid'],
                        'task_success':None,'replay_allowed':False}
        self._exit_code = code
        self._exit_observed_ns = self._clock()
        self._close_log()
        if type(code) is not int or code != 0:
            return {'status':'unknown','reason':'calc_target_nonzero_exit',
                    'exit_code':code,'pid':self._pid,
                    'task_success':None,'replay_allowed':False}
        row = self._target_identity
        receipt = {
            'schema':(_EXIT_SCHEMA if self._custody_mode == 'direct-child'
                      else _WRAPPED_EXIT_SCHEMA),
            'status':'exited','verified':True,
            'process_generation':row['process_generation'],
            'xid':row['xid'],'pid':row['pid'],
            'start_ticks':row['start_ticks'],'exit_code':code,
            'observed_monotonic_ns':self._exit_observed_ns}
        if self._custody_mode == 'libreoffice-oosplash-child':
            receipt.update({
                'custody':'libreoffice-oosplash-direct-child-v1',
                'launcher_pid':row['launcher_pid'],
                'launcher_start_ticks':row['launcher_start_ticks'],
                'launcher_executable':row['launcher_executable'],
                'launcher_package_version':row['launcher_package_version'],
                'launcher_exit_code':code,
                'replacement_observed':self._replacement_observed})
        self._exit_receipt = receipt
        return deepcopy(self._exit_receipt)

    def _close_log(self):
        if self._stdout is not None:
            try:
                self._stdout.close()
            finally:
                self._stdout = None

    def close(self):
        """Close only the retained log handle; never signals or reaps by force."""
        self._close_log()
