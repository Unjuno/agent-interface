import unittest
import struct
import importlib
import os
import time
from types import SimpleNamespace
from unittest.mock import patch

from runtime.guarded_x11_v1.xres_client_fence import (
    client_is_connected,
    client_pid_at_base,
    wait_for_client_disconnect,
)


class _ReplyConnection:
    def __init__(self, clients, *, client_ids=None, extension=True):
        self.clients = clients
        self.client_ids = client_ids
        self.extension = extension
        self.queries = 0
        self.id_queries = []
        self.display = SimpleNamespace(info=SimpleNamespace(
            resource_id_base=0x5600000))

    def has_extension(self, name):
        return name == 'X-Resource' and self.extension

    def res_query_version(self):
        return SimpleNamespace(server_major=1, server_minor=2)

    def res_query_clients(self):
        self.queries += 1
        return SimpleNamespace(clients=self.clients)

    def res_query_client_ids(self, specs):
        self.id_queries.append(specs)
        return SimpleNamespace(ids=self.client_ids)


class XResClientFenceTests(unittest.TestCase):
    @staticmethod
    def _client_id(resource_base, pid, *, mask=2):
        return SimpleNamespace(
            spec=SimpleNamespace(client=resource_base, mask=mask),
            value=[pid],
        )

    @classmethod
    def _process_ids(cls, resource_base, pid, *, observer_pid=None):
        if observer_pid is None:
            observer_pid = os.getpid()
        observer_base = 0x5600000
        if resource_base == observer_base:
            return [cls._client_id(observer_base, pid)]
        return [cls._client_id(observer_base, observer_pid),
                cls._client_id(resource_base, pid)]

    @staticmethod
    def _blocked_worker(_send_connection):
        time.sleep(5)

    @staticmethod
    def _completed_worker(send_connection):
        send_connection.send({'status':'disconnected'})

    @staticmethod
    def _malformed_result_worker(send_connection):
        send_connection.send({'status':'released'})

    @staticmethod
    def _released_worker(send_connection):
        send_connection.send({'status':'released', 'release':{
            'verified':True, 'keys_down':[], 'buttons_down':[]}})

    @staticmethod
    def _result_then_delayed_exit_worker(send_connection):
        send_connection.send({'status':'released', 'release':{
            'verified':True, 'keys_down':[], 'buttons_down':[]}})
        time.sleep(0.3)

    def test_supervisor_terminates_a_query_worker_that_exceeds_its_budget(self):
        module = importlib.import_module('runtime.guarded_x11_v1.xres_client_fence')
        supervise = getattr(module, 'supervise_xres_worker', None)
        self.assertTrue(callable(supervise), 'bounded XRes worker supervisor is missing')

        started = time.monotonic()
        result = supervise(self._blocked_worker, (), timeout_s=0.1,
                           terminate_grace_s=0.1)

        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'supervision_timeout', result)
        self.assertTrue(result['worker_retired'], result)
        self.assertLess(time.monotonic() - started, 1.5)

    def test_supervisor_budget_starts_after_worker_process_creation(self):
        module = importlib.import_module('runtime.guarded_x11_v1.xres_client_fence')
        receive = SimpleNamespace(timeout=None)
        def poll(timeout):
            receive.timeout = timeout
            return True
        receive.poll = poll
        receive.recv = lambda: {'status':'disconnected'}
        receive.close = lambda: None
        send = SimpleNamespace(close=lambda: None)

        class Process:
            def __init__(self):
                self.alive = True
                self.exitcode = None
            def start(self):
                time.sleep(0.15)
            def join(self, timeout=None):
                self.alive = False
                self.exitcode = 0
            def is_alive(self):
                return self.alive

        process = Process()
        context = SimpleNamespace(
            Pipe=lambda duplex=False: (receive, send),
            Process=lambda target, args, name: process)
        with patch.object(module.multiprocessing, 'get_context', return_value=context):
            result = module.supervise_xres_worker(
                self._completed_worker, (), timeout_s=0.1,
                terminate_grace_s=0.1)

        self.assertEqual(result['status'], 'disconnected', result)
        self.assertGreater(receive.timeout, 0.08, receive.timeout)
        self.assertLess(receive.timeout, 0.101)

    def test_supervisor_preserves_a_completed_worker_result(self):
        module = importlib.import_module('runtime.guarded_x11_v1.xres_client_fence')
        supervise = getattr(module, 'supervise_xres_worker', None)
        self.assertTrue(callable(supervise), 'bounded XRes worker supervisor is missing')

        result = supervise(self._completed_worker, (), timeout_s=1.0,
                           terminate_grace_s=0.1)

        self.assertEqual(result['status'], 'disconnected')
        self.assertTrue(result['worker_retired'], result)

    def test_supervisor_retains_result_status_when_worker_shutdown_exceeds_grace(self):
        module = importlib.import_module('runtime.guarded_x11_v1.xres_client_fence')

        result = module.supervise_xres_worker(
            self._result_then_delayed_exit_worker, (), timeout_s=1.0,
            terminate_grace_s=0.05, accepted_statuses=('released',))

        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['reason'], 'worker_did_not_exit_cleanly', result)
        self.assertEqual(result.get('worker_result_status'), 'released', result)
        self.assertIsInstance(result.get('worker_result_received_monotonic_ns'), int,
                              result)
        self.assertIsInstance(result.get('worker_exit_observed_monotonic_ns'), int,
                              result)
        self.assertGreater(result['worker_exit_observed_monotonic_ns'],
                           result['worker_result_received_monotonic_ns'])

    def test_supervisor_classifies_an_unrecognized_worker_status_as_malformed(self):
        module = importlib.import_module('runtime.guarded_x11_v1.xres_client_fence')
        result = module.supervise_xres_worker(
            self._malformed_result_worker, (), timeout_s=1.0,
            terminate_grace_s=0.1)

        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'malformed_worker_result', result)
        self.assertTrue(result['worker_retired'], result)
        self.assertEqual(result['worker_exitcode'], 0)

    def test_supervisor_can_accept_an_independent_release_receipt(self):
        module = importlib.import_module('runtime.guarded_x11_v1.xres_client_fence')
        result = module.supervise_xres_worker(
            self._released_worker, (), timeout_s=1.0,
            terminate_grace_s=0.1, accepted_statuses=('released', 'unknown'))

        self.assertEqual(result['status'], 'released', result)
        self.assertEqual(result['release'], {
            'verified':True, 'keys_down':[], 'buttons_down':[]})
        self.assertTrue(result['worker_retired'], result)

    def test_python_xlib_query_clients_reply_shape_identifies_resource_base(self):
        from Xlib.ext import res

        request = res.QueryClients._request.to_binary(opcode=200)
        parsed, rest = res.Client.parse_binary(
            struct.pack('=II', 0x1200000, 0x1fffff), None)
        connection = _ReplyConnection(
            [parsed], client_ids=self._process_ids(0x1200000, 4321))

        self.assertEqual(request, bytes((200, res.ResQueryClients, 1, 0)))
        self.assertEqual(rest, b'')
        self.assertTrue(client_is_connected(
            connection, 0x1200000, expected_pid=4321))

    def test_python_xlib_query_client_ids_wire_and_reply_shape(self):
        from Xlib.ext import res

        base = 0x1200000
        request = res.QueryClientIds._request.to_binary(
            opcode=200, specs=[{'client':base,
                                'mask':res.LocalClientPIDMask}])
        parsed, rest = res.ClientIdValue.parse_binary(
            struct.pack('=IIII', base, res.LocalClientPIDMask, 4, 4321), None)

        self.assertEqual(request, bytes((
            200, res.ResQueryClientIds, 4, 0,
            1, 0, 0, 0,
            0, 0, 0x20, 0x01,
            res.LocalClientPIDMask, 0, 0, 0,
        )))
        self.assertEqual(parsed.spec.client, base)
        self.assertEqual(parsed.spec.mask, res.LocalClientPIDMask)
        self.assertEqual(parsed.value, [4321])
        self.assertEqual(rest, b'')

    def test_reports_expected_owner_pid_present_or_absent_at_resource_base(self):
        present = _ReplyConnection([
            SimpleNamespace(resource_base=0x1200000, resource_mask=0x1fffff),
            SimpleNamespace(resource_base=0x3400000, resource_mask=0x1fffff),
        ], client_ids=self._process_ids(0x1200000, 4321))
        absent = _ReplyConnection([
            SimpleNamespace(resource_base=0x3400000, resource_mask=0x1fffff),
        ])

        self.assertTrue(client_is_connected(
            present, 0x1200000, expected_pid=4321))
        self.assertFalse(client_is_connected(
            absent, 0x1200000, expected_pid=4321))
        self.assertEqual(present.queries, 1)
        self.assertEqual(absent.queries, 1)

    def test_identifies_expected_process_when_resource_base_is_reused(self):
        from Xlib.ext import res

        base = 0x1200000
        connection = _ReplyConnection(
            [SimpleNamespace(resource_base=base, resource_mask=0x1fffff)],
            client_ids=self._process_ids(base, 4321),
        )

        self.assertTrue(client_is_connected(connection, base, expected_pid=4321))
        self.assertFalse(client_is_connected(connection, base, expected_pid=9876))
        expected_specs = [
            {'client':base, 'mask':res.LocalClientPIDMask},
            {'client':0x5600000, 'mask':res.LocalClientPIDMask},
        ]
        self.assertEqual(connection.id_queries, [expected_specs] * 2)

    def test_observer_reusing_retired_owner_base_is_not_mistaken_for_owner(self):
        observer_base = 0x5600000
        connection = _ReplyConnection(
            [SimpleNamespace(resource_base=observer_base,
                             resource_mask=0x1fffff)],
            client_ids=self._process_ids(observer_base, os.getpid()),
        )

        self.assertFalse(client_is_connected(
            connection, observer_base, expected_pid=4321))

    def test_reports_the_observed_pid_for_a_reused_resource_base(self):
        observer_base = 0x5600000
        connection = _ReplyConnection(
            [SimpleNamespace(resource_base=observer_base,
                             resource_mask=0x1fffff)],
            client_ids=self._process_ids(observer_base, os.getpid()),
        )

        self.assertEqual(client_pid_at_base(connection, observer_base), os.getpid())

    def test_process_identity_query_fails_closed_on_missing_or_ambiguous_pid(self):
        base = 0x1200000
        client = SimpleNamespace(resource_base=base, resource_mask=0x1fffff)
        observer = self._client_id(0x5600000, os.getpid())
        replies = (
            None,
            [],
            [observer, self._client_id(base, 4321),
             self._client_id(base, 9876)],
            [observer, self._client_id(0x3400000, 4321)],
            [observer, self._client_id(base, True)],
        )
        for ids in replies:
            connection = _ReplyConnection([client], client_ids=ids)
            with self.subTest(ids=ids), self.assertRaises(RuntimeError):
                client_is_connected(connection, base, expected_pid=4321)

    def test_process_identity_rejects_a_different_pid_namespace(self):
        base = 0x1200000
        connection = _ReplyConnection(
            [SimpleNamespace(resource_base=base, resource_mask=0x1fffff)],
            client_ids=self._process_ids(
                base, 4321, observer_pid=os.getpid() + 1),
        )
        with self.assertRaisesRegex(RuntimeError, 'PID namespace'):
            client_is_connected(connection, base, expected_pid=4321)

    def test_process_identity_requires_xres_version_12(self):
        base = 0x1200000

        class Version11Connection(_ReplyConnection):
            def res_query_version(self):
                return SimpleNamespace(server_major=1, server_minor=1)

        connection = Version11Connection([
            SimpleNamespace(resource_base=base, resource_mask=0x1fffff)],
            client_ids=self._process_ids(base, 4321),
        )
        with self.assertRaises(RuntimeError):
            client_is_connected(connection, base, expected_pid=4321)

    def test_process_identity_requires_a_positive_unsigned_pid(self):
        connection = _ReplyConnection([])
        for pid in (0, -1, True, 2**32):
            with self.subTest(pid=pid), self.assertRaises(ValueError):
                client_is_connected(connection, 0x1200000, expected_pid=pid)

    def test_waits_for_expected_process_disappearance_with_finite_poll_budget(self):
        client = SimpleNamespace(resource_base=0x1200000, resource_mask=0x1fffff)

        class ChangingConnection(_ReplyConnection):
            def res_query_clients(self):
                self.queries += 1
                return SimpleNamespace(clients=[client] if self.queries == 1 else [])

        now = [0.0]
        connection = ChangingConnection(
            [], client_ids=self._process_ids(0x1200000, 4321))
        disconnected = wait_for_client_disconnect(
            connection, 0x1200000, expected_pid=4321,
            timeout_s=0.1, poll_interval_s=0.01,
            clock=lambda:now[0], sleep=lambda amount:now.__setitem__(0, now[0] + amount))

        self.assertTrue(disconnected)
        self.assertEqual(connection.queries, 2)
        self.assertLessEqual(now[0], 0.1)

    def test_remains_unconfirmed_when_client_stays_present_until_timeout(self):
        client = SimpleNamespace(resource_base=0x1200000, resource_mask=0x1fffff)
        now = [0.0]
        connection = _ReplyConnection(
            [client], client_ids=self._process_ids(0x1200000, 4321))
        disconnected = wait_for_client_disconnect(
            connection, 0x1200000, expected_pid=4321,
            timeout_s=0.025, poll_interval_s=0.01,
            clock=lambda:now[0], sleep=lambda amount:now.__setitem__(0, now[0] + amount))

        self.assertFalse(disconnected)
        self.assertEqual(connection.queries, 3)
        self.assertLessEqual(now[0], 0.025)

    def test_missing_xres_or_malformed_reply_fails_closed(self):
        missing = _ReplyConnection([], extension=False)
        malformed = _ReplyConnection([
            SimpleNamespace(resource_base=True, resource_mask=0x1fffff),
        ])

        for connection in (missing, malformed):
            with self.subTest(connection=connection), self.assertRaises(RuntimeError):
                client_is_connected(connection, 0x1200000, expected_pid=4321)

    def test_invalid_or_ambiguous_client_catalog_fails_closed(self):
        duplicate = _ReplyConnection([
            SimpleNamespace(resource_base=0x1200000, resource_mask=0x1fffff),
            SimpleNamespace(resource_base=0x1200000, resource_mask=0x1fffff),
        ])

        with self.assertRaises(RuntimeError):
            client_is_connected(duplicate, 0x1200000, expected_pid=4321)
        with self.assertRaises(ValueError):
            client_is_connected(duplicate, True, expected_pid=4321)


if __name__ == '__main__':
    unittest.main()
