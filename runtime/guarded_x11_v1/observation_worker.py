"""Read-only active visual checks; no access to the input owner's connection."""
import hashlib
import json
from pathlib import Path
import time
from types import SimpleNamespace

from Xlib import display
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError
from runtime.cli_v1.observe import observe_in_session
from runtime.core_v1.compiled_gui import ObservationAssociationChanged
from .process_identity import read_linux_x11_process_identity


class CaptureBindingChanged(X11BackendError, ObservationAssociationChanged):
    pass


def acquire_observation(backend,target,binding,sequence,revision,save,*,observe=observe_in_session,session=None):
    """Acquire/verify one exact frame; never publish owner sequence/history."""
    started = time.monotonic_ns()
    before = binding()
    screen = backend.d.screen()
    report = observe(session if session is not None else SimpleNamespace(backend=backend),target=target,
        frame='screen_physical_px',region=[0,0,screen.width_in_pixels,screen.height_in_pixels])
    returned = time.monotonic_ns()
    save('public-observation-'+report['observation_id']+'.json',report)
    if report['status']!='returned':
        raise X11BackendError('public observation failed; inspect retained report: '+str(report.get('error',report['status'])))
    native = report['observation']
    after = binding()
    if before!=after:
        save('capture-binding-changed-'+report['observation_id']+'.json',dict(
            reason='association_changed',before=before,after=after,
            public_report='public-observation-'+report['observation_id']+'.json',
            last_valid_sequence=sequence-1,authority_granted=False,replay_allowed=False))
        raise CaptureBindingChanged('binding changed during native capture')
    checked = time.monotonic_ns()
    artifact = native['artifact']
    data = Path(artifact['path']).read_bytes()
    if hashlib.sha256(data).hexdigest()!=artifact['sha256'] or artifact['source_raw_sha256']!=native['sha256']:
        raise X11BackendError('native artifact identity mismatch')
    verified = time.monotonic_ns()
    image = backend.take_capture_rgb(artifact)
    observation = dict(sequence=sequence,observation_id=report['observation_id'],
        binding_revision=revision,capture_ns=native['capture_started_ns'],
        image_source='exact_capture_rgb_handoff',pointer_binding=before,native=native,
        timing_ns=dict(started=started,public_returned=returned,binding_checked=checked,
                       artifact_verified=verified,decoded=time.monotonic_ns()))
    return observation,image


def open_readonly_backend(display_name,targets):
    # Reuse capture/geometry primitives, without constructing an input session,
    # requiring XTEST, or exposing input operations on the reader's interface.
    connection = display.Display(display_name)
    try:
        backend = object.__new__(X11Backend)
        backend.d = connection
        backend.root = connection.screen().root
        backend.targets = {name:connection.create_resource_object('window',xid) for name,xid in targets.items()}
        backend.capture_artifacts = None
        return backend
    except BaseException:
        connection.close()
        raise


class X11ObservationReader:
    def __init__(self,display_name,targets,target,directory):
        self.backend = open_readonly_backend(display_name,targets)
        self.target = target
        self.directory = Path(directory)
        try:
            self.directory.mkdir(parents=True,exist_ok=False)
            self.backend.configure_capture_artifacts(self.directory/'images',retain_rgb=True)
        except BaseException:
            self.backend.close()
            raise

    def _save(self,name,value):
        (self.directory/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

    def _binding(self):
        backend = self.backend
        focus = backend.d.get_input_focus().focus
        geometry = backend.geometry(self.target)
        return dict(focus=getattr(focus,'id',focus),surface=backend.targets[self.target].id,
            geometry=[geometry[k] for k in ('x','y','width','height')],
            process_generation=read_linux_x11_process_identity(backend.d,backend.targets[self.target].id))

    def read(self,operation,request):
        if operation=='binding': return self._binding()
        if operation=='verify':
            callback,stage,source,image = request
            return callback(stage,source,image)
        if operation!='capture': raise ValueError('unknown observation operation')
        observation,image = acquire_observation(self.backend,self.target,self._binding,
            request['sequence'],request['revision'],self._save)
        self._save('observation-'+str(request['sequence'])+'.json',observation)
        return observation,image

    def close(self): self.backend.close()
