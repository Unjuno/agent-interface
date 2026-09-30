"""Single-owner X11 connection for the optional persistent MCP route.

All methods are serialized by the transport. No restart, authority issuance,
source refresh or implicit recovery reset. The ordinary one-shot route does not use this.
"""
from copy import deepcopy
import os
import uuid
import time
from .x11_target_review import inspect_focused_target
from .observe import observe_in_session, valid_observation_request
from runtime.selector_v1 import open_session, select_backend


class MCPSessionOwner:
    def __init__(self, targets, display_name=None):
        self.targets = deepcopy(targets)
        self.family_roots = deepcopy(targets)
        self.binding_revision = 1
        self.target_review = None
        self.display_name = display_name
        self.session_id = uuid.uuid4().hex
        self.session = None
        self.state = 'unopened'
        self.error = None
        self.dispatch_attempted = False
        self.close_report = None

    def snapshot(self):
        return {'session_id': self.session_id, 'mode': 'persistent-x11',
                'state': self.state, 'binding_revision': self.binding_revision,
                'targets': deepcopy(self.targets), 'recovery_required':
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

    def inspect_target(self, target, screen_region=None, capture_directory=None):
        self.target_review = None
        if target not in self.targets:
            raise ValueError('unknown configured target')
        session = self.get()
        evidence = inspect_focused_target(session.backend, self.family_roots[target])
        observation = None
        if screen_region is not None:
            observation = observe_in_session(session, target=target,
                frame='screen_physical_px', region=screen_region,
                capture_directory=capture_directory)
            failure = None
            if observation.get('status') != 'returned':
                failure = 'TARGET_CAPTURE_FAILED'
            else:
                try:
                    if inspect_focused_target(session.backend, self.family_roots[target]) != evidence:
                        failure = 'TARGET_CHANGED_DURING_CAPTURE'
                except Exception as error:
                    failure = 'TARGET_RECHECK_FAILED: ' + repr(error)
            if failure:
                return {'status': 'needs_review', 'error': failure,
                        'evidence': evidence, 'observation_report': observation,
                        'input_dispatched': False, 'authority_granted': False}
        review = {'review_id': uuid.uuid4().hex, 'target': target,
                  'binding_revision': self.binding_revision, 'evidence': evidence,
                  'expires_at_ns': time.monotonic_ns() + 30_000_000_000}
        self.target_review = review
        row = dict(deepcopy(review), status='needs_review', input_dispatched=False,
                   authority_granted=False)
        arguments = {'target': target, 'window_id': evidence['window_id'],
                     'review_id': review['review_id']}
        if screen_region is not None:
            arguments['screen_region'] = deepcopy(screen_region)
        row['review_request'] = {'tool': 'interface_review_target', 'arguments': arguments}
        row['review_request_scope'] = (
            'Candidate call after your explicit review of this evidence; not executed. '
            'The one-use ID expires at expires_at_ns and target evidence is rechecked. '
            'Retained results do not renew it. No input authority or replay permission.')
        if observation is not None:
            row['observation_report'] = observation
        return row

    def inspect_after_dispatch(self, report, target, screen_region=None, capture_directory=None):
        """Read-only inspection/capture after completed released input; no replay."""
        started = time.monotonic_ns()
        result = report.get('result', {})
        releases = result.get('execution', {}).get('releases', [])
        self.target_review = None
        ready = (self.state == 'open' and self.session is not None
                 and self.session.recovery_required is False
                 and result.get('status') == 'completed'
                 and result.get('recovery_required') is False
                 and bool(releases) and all(
                     item.get('verified') is True and item.get('keys_down') == []
                     and item.get('buttons_down') == [] and 'error' not in item
                     for item in releases))
        if not ready:
            inspection = {'status': 'skipped', 'reason': 'DISPATCH_NOT_COMPLETED_AND_RELEASED'}
        else:
            try:
                inspection = self.inspect_target(target, screen_region=screen_region,
                                                 capture_directory=capture_directory)
            except Exception as error:
                inspection = {'status': 'needs_review', 'error': repr(error)}
        return dict(inspection, started_ns=started, ended_ns=time.monotonic_ns(),
                    input_dispatched=False, authority_granted=False,
                    scope='Metadata sampled after dispatch. Not atomically bound to its image; '
                          'no redraw or task completion acknowledgement. Review explicitly; '
                          'retained lookup does not renew the review ID.')

    def recover_input(self, current_binding_revision, target=None, region=None,
                      capture_directory=None):
        # Never open/reopen a connection to recover a different input owner.
        if self.state != 'open' or self.session is None:
            return {'status': 'refused', 'error': 'RECOVERY_REQUIRES_OPEN_SESSION',
                    'release_attempted': False, 'authority_granted': False}
        if (type(current_binding_revision) is not int
                or current_binding_revision != self.binding_revision):
            return {'status': 'refused', 'error': 'SESSION_BINDING_REVISION_MISMATCH',
                    'release_attempted': False, 'authority_granted': False}
        wants_capture = target is not None or region is not None
        if wants_capture and (not valid_observation_request(target, 'window_client', region)
                              or target not in self.targets):
            return {'status': 'refused', 'error': 'INVALID_RECOVERY_OBSERVATION',
                    'release_attempted': False, 'authority_granted': False}
        report = self.session.recover_input()
        if report.get('release_attempted'):
            self.dispatch_attempted = True
        if report.get('status') == 'input_recovered':
            self.target_review = None
            self.binding_revision += 1
            if wants_capture:
                # Recovery has committed. A capture failure must retain its
                # receipt/revision rather than invite a repeated release.
                try:
                    observation = observe_in_session(self.session, target=target,
                        frame='window_client', region=region,
                        capture_directory=capture_directory)
                except Exception as error:
                    observation = {'status': 'observation_failed', 'error': repr(error),
                                   'input_dispatched': False, 'side_effect_authority': False}
                report = dict(report, observation_report=observation)
        recovery_note = (
            'Input recovery is still required. The release attempt did not verify neutrality. '
            'Do not send a new program or replay the previous one. '
            if report.get('recovery_required') is True else '')
        return dict(report, binding_revision=self.binding_revision,
                    authority_granted=False,
                    note=recovery_note + 'Only input neutrality was checked. Prior task effects remain unknown; '
                         'Review the returned image, or observe separately if no usable image '
                         'was returned, before a new program. Capture does not acknowledge redraw. '
                         'Use the returned binding revision; no lease/source is issued.')

    def review_target(self, target, window_id, review_id, screen_region=None,
                      capture_directory=None):
        review = self.target_review
        self.target_review = None
        if (review is None or review['target'] != target or review['review_id'] != review_id
                or review['binding_revision'] != self.binding_revision
                or time.monotonic_ns() > review['expires_at_ns']
                or review['evidence']['window_id'] != window_id):
            raise ValueError('missing, expired or mismatched target review')
        session = self.get()
        evidence = inspect_focused_target(session.backend, self.family_roots[target])
        if evidence != review['evidence']:
            raise ValueError('target changed since inspection; inspect again')
        previous = self.targets[target]
        session.backend.targets[target] = session.backend.d.create_resource_object('window', window_id)
        self.targets[target] = window_id
        self.binding_revision += 1
        row = {'status': 'target_reviewed', 'target': target,
                'previous_window_id': previous, 'window_id': window_id,
                'binding_revision': self.binding_revision, 'evidence': evidence,
                'input_dispatched': False, 'authority_granted': False,
                'note': 'Capture and review the selected surface before new input; no lease issued.'}
        if screen_region is not None:
            # Selection has committed. Capture failure must not hide or undo the
            # revision change, nor make replaying this one-use review appropriate.
            row['observation_report'] = observe_in_session(session, target=target,
                frame='screen_physical_px', region=screen_region,
                capture_directory=capture_directory)
            row['capture_consistency'] = 'unconfirmed'
            if row['observation_report'].get('status') == 'returned':
                try:
                    current = inspect_focused_target(session.backend, self.family_roots[target])
                    row['capture_consistency'] = ('matched' if current == evidence else 'changed')
                except Exception as error:
                    row['capture_recheck_error'] = repr(error)
            row['note'] = ('Selection committed; review image delivery and capture_consistency '
                           'before input. On unavailable/changed evidence, inspect again; '
                           'do not replay this review. Matching metadata is not a redraw '
                           'acknowledgement or semantic completion. No lease issued.')
        return row

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
