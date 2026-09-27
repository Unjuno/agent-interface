"""Single-owner X11 connection for the optional persistent MCP route.

All methods are serialized by the transport. No restart, authority issuance,
source refresh or recovery reset. The ordinary one-shot route does not use this.
"""
from copy import deepcopy
import os
import uuid
from runtime.selector_v1 import open_session, select_backend


class MCPSessionOwner:
    def __init__(self, targets, display_name=None):
        self.targets = deepcopy(targets)
        self.display_name = display_name
        self.session_id = uuid.uuid4().hex
        self.session = None
        self.state = 'unopened'
        self.error = None
        self.dispatch_attempted = False
        self.close_report = None

    def snapshot(self):
        return {'session_id': self.session_id, 'mode': 'persistent-x11',
                'state': self.state, 'recovery_required':
                getattr(self.session, 'recovery_required', None),
                'error': self.error, 'authority_granted': False,
                'restart_allowed': False}

    def get(self):
        if self.state == 'open':
            return self.session
        if self.state != 'unopened':
            raise RuntimeError('persistent session unavailable: ' + self.state)
        # Consume initialization even on failure; later calls must not silently
        # connect to a different server or clear a recovery requirement.
        self.state = 'opening'
        try:
            env = dict(os.environ)
            if self.display_name is not None:
                env['DISPLAY'] = self.display_name
            plan = select_backend(environ=env)
            if not plan.available or plan.backend_id != 'x11-v1':
                raise RuntimeError('persistent-x11 requires the available X11 backend')
            self.session = open_session(self.targets, display_name=self.display_name)
            self.state = 'open'
            return self.session
        except Exception as error:
            self.state = 'failed'
            self.error = repr(error)
            raise

    def close(self):
        if self.close_report is not None:
            return deepcopy(self.close_report)
        row = {'status': 'closed', 'session_id': self.session_id,
               'authority_granted': False, 'restart_allowed': False,
               'release_attempted': False, 'connection_close_attempted': False}
        self.state = 'closed'
        if self.session is not None:
            try:
                if self.dispatch_attempted:
                    row['release_attempted'] = True
                    release = self.session.backend.release_all()
                    row['release'] = release
                    if not (release.get('verified') is True and
                            release.get('keys_down') == [] and release.get('buttons_down') == []):
                        row['status'] = 'cleanup_failed'
            except Exception as error:
                row.update(status='cleanup_failed', release_error=repr(error))
            finally:
                row['connection_close_attempted'] = True
                try:
                    self.session.backend.close()
                except Exception as error:
                    row.update(status='cleanup_failed', close_error=repr(error))
        self.close_report = row
        return deepcopy(row)
