"""Experimental composition of JobHost and the WSLc driver for run_attempt.

The adapter only maps separately observed receipts. It is not a parent-death
custodian, a live model host, or proof of GUI input release.
"""
import math
import json
from pathlib import Path
import re
import time

from job_host import JobHost
from wslc_driver import ContainerDriver


class WslcLifecycleAdapter:
    def __init__(self, *, host_argv, image, container_command, audit,
                 mounts=None, environment=None, runner=None,
                 container_start_timeout_s=30.0, host_factory=JobHost,
                 container_factory=ContainerDriver):
        if (not isinstance(host_argv, list) or not host_argv
                or any(not isinstance(arg, str) or not arg or '\0' in arg for arg in host_argv)):
            raise ValueError('host_argv must be a nonempty string list')
        if (not isinstance(container_command, list) or not container_command
                or any(not isinstance(arg, str) or not arg or '\0' in arg
                       for arg in container_command)):
            raise ValueError('container_command must be a nonempty string list')
        if not callable(audit):
            raise ValueError('audit callback required')
        if (type(container_start_timeout_s) not in (int, float)
                or not math.isfinite(container_start_timeout_s)
                or container_start_timeout_s <= 0):
            raise ValueError('positive finite container start timeout required')
        self.host_argv = list(host_argv)
        self.image = image
        self.container_command = list(container_command)
        self.audit_callback = audit
        self.mounts = dict(mounts or {})
        self.environment = dict(environment or {})
        self.runner = runner
        self.container_start_timeout_s = container_start_timeout_s
        self.host_factory = host_factory
        self.container_factory = container_factory

    def prepare_host(self, allocation):
        path = Path(allocation) / 'host'
        path.mkdir()
        return self.host_factory(self.host_argv, path)

    def prepare_container(self, allocation):
        allocation = Path(allocation)
        conditions = (allocation / 'conditions.json').read_text(encoding='utf-8')
        row = json.loads(conditions)
        run_id = row.get('run_id') if isinstance(row, dict) else None
        if not isinstance(run_id, str) or not re.fullmatch('[0-9a-f]{32}', run_id):
            raise ValueError('conditions require a full run_id')
        allocation = allocation.resolve(strict=True)
        root = allocation / 'container'
        root.mkdir()
        for target, pair in self.mounts.items():
            if (target not in ('/src', '/in', '/out', '/exchange')
                    or not isinstance(pair, tuple) or len(pair) != 2
                    or type(pair[1]) is not bool):
                raise ValueError('invalid mount')
            mount_path = Path(pair[0]).resolve(strict=False)
            if target in ('/src', '/in') and pair[1] is not True:
                raise ValueError('source mounts must be read-only')
            try:
                mount_path.relative_to(allocation)
            except ValueError as exc:
                raise ValueError('mount must be inside the attempt allocation') from exc
            if mount_path == allocation:
                raise ValueError('mount cannot expose the whole attempt allocation')
            if target in ('/out', '/exchange') and not mount_path.exists():
                mount_path.mkdir(parents=True, exist_ok=False)
        kwargs = {
            'mounts': self.mounts,
            'environment': self.environment,
        }
        if self.runner is not None:
            kwargs['runner'] = self.runner
        return self.container_factory(root, run_id, self.image,
                                      self.container_command, **kwargs)

    @staticmethod
    def start_host(host, allocation):
        host.start()

    def start_container(self, container, allocation, timeout_s):
        if (type(timeout_s) not in (int, float)
                or not math.isfinite(timeout_s) or timeout_s <= 0):
            raise TimeoutError('no execution budget remains for container start')
        receipt = container.start(timeout_s=min(self.container_start_timeout_s, timeout_s))
        if not isinstance(receipt, dict) or receipt.get('status') not in ('running', 'exited'):
            raise RuntimeError('container start identity is unresolved')

    @staticmethod
    def wait_container(container, timeout_s):
        return container.wait(timeout_s=timeout_s)

    @staticmethod
    def stop_host(host, timeout_s):
        valid_budget = (type(timeout_s) in (int, float)
                        and math.isfinite(timeout_s) and timeout_s > 0)
        deadline = time.monotonic() + timeout_s if valid_budget else time.monotonic()
        wait_error = close_error = None
        if valid_budget:
            try:
                wait_receipt = host.wait(timeout_s=max(0.001, deadline - time.monotonic()))
            except BaseException as exc:
                wait_error = exc
                wait_receipt = {'status': 'UNKNOWN', 'error_type': type(exc).__name__}
        else:
            wait_receipt = {'status': 'UNKNOWN', 'reason': 'no_cleanup_budget'}
        try:
            close_receipt = host.close(timeout_s=max(0.001, deadline - time.monotonic()))
        except BaseException as exc:
            close_error = exc
            close_receipt = {'status': 'UNKNOWN', 'error_type': type(exc).__name__}
        late = not valid_budget or time.monotonic() >= deadline
        errors = [error for error in (wait_error, close_error) if error is not None]
        if errors:
            primary = next((error for error in errors if not isinstance(error, Exception)), errors[0])
            for error in errors:
                if error is not primary:
                    try:
                        primary.add_note('additional host cleanup error: ' + repr(error))
                    except AttributeError:
                        pass
            if not isinstance(primary, Exception):
                raise primary
            return {'status': 'UNKNOWN', 'exit_code': None, 'wait': wait_receipt,
                    'retirement': close_receipt, 'returned_late': late,
                    'error_type': type(primary).__name__}
        code = wait_receipt.get('exit_code') if isinstance(wait_receipt, dict) else None
        closed = (isinstance(close_receipt, dict)
                  and close_receipt.get('status') == 'closed_scoped')
        if (not late and isinstance(wait_receipt, dict)
                and wait_receipt.get('status') == 'exited'
                and type(code) is int and closed):
            status = 'exited'
        else:
            status = 'UNKNOWN'
            code = None
        return {'status': status, 'exit_code': code, 'wait': wait_receipt,
                'retirement': close_receipt, 'returned_late': late}

    @staticmethod
    def cleanup_container(container, timeout_s):
        if (type(timeout_s) not in (int, float)
                or not math.isfinite(timeout_s) or timeout_s <= 0):
            return {'status': 'UNKNOWN', 'reason': 'no_cleanup_budget'}
        receipt = container.reconcile(timeout_s=timeout_s)
        if not isinstance(receipt, dict):
            return {'status': 'UNKNOWN', 'reconcile': {'status': 'UNKNOWN'}}
        # The second reconciliation pass follows stop and may reveal that the
        # exact container is still present or has reappeared. Only its final
        # exact-ID absence observation can confirm cleanup for this attempt.
        final_remove = receipt.get('remove')
        absent = (isinstance(final_remove, dict)
                  and final_remove.get('status') == 'observed_absent'
                  and receipt.get('remove_returned_late') is False)
        return {'status': 'confirmed' if absent else 'UNKNOWN',
                'reconcile': receipt}

    def audit(self, allocation):
        return self.audit_callback(Path(allocation))
