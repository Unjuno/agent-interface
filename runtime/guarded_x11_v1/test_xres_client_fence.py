import unittest
import struct
from types import SimpleNamespace

from runtime.guarded_x11_v1.xres_client_fence import (
    client_is_connected,
    wait_for_client_disconnect,
)


class _ReplyConnection:
    def __init__(self, clients, *, extension=True):
        self.clients = clients
        self.extension = extension
        self.queries = 0

    def has_extension(self, name):
        return name == 'X-Resource' and self.extension

    def res_query_version(self):
        return SimpleNamespace(server_major=1, server_minor=2)

    def res_query_clients(self):
        self.queries += 1
        return SimpleNamespace(clients=self.clients)


class XResClientFenceTests(unittest.TestCase):
    def test_python_xlib_query_clients_reply_shape_identifies_resource_base(self):
        from Xlib.ext import res

        request = res.QueryClients._request.to_binary(opcode=200)
        parsed, rest = res.Client.parse_binary(
            struct.pack('=II', 0x1200000, 0x1fffff), None)
        connection = _ReplyConnection([parsed])

        self.assertEqual(request, bytes((200, res.ResQueryClients, 1, 0)))
        self.assertEqual(rest, b'')
        self.assertTrue(client_is_connected(connection, 0x1200000))

    def test_reports_owner_client_present_or_absent_by_exact_resource_base(self):
        present = _ReplyConnection([
            SimpleNamespace(resource_base=0x1200000, resource_mask=0x1fffff),
            SimpleNamespace(resource_base=0x3400000, resource_mask=0x1fffff),
        ])
        absent = _ReplyConnection([
            SimpleNamespace(resource_base=0x3400000, resource_mask=0x1fffff),
        ])

        self.assertTrue(client_is_connected(present, 0x1200000))
        self.assertFalse(client_is_connected(absent, 0x1200000))
        self.assertEqual(present.queries, 1)
        self.assertEqual(absent.queries, 1)

    def test_waits_for_exact_client_disappearance_with_a_finite_poll_budget(self):
        client = SimpleNamespace(resource_base=0x1200000, resource_mask=0x1fffff)

        class ChangingConnection(_ReplyConnection):
            def res_query_clients(self):
                self.queries += 1
                return SimpleNamespace(clients=[client] if self.queries == 1 else [])

        now = [0.0]
        connection = ChangingConnection([])
        disconnected = wait_for_client_disconnect(
            connection, 0x1200000, timeout_s=0.1, poll_interval_s=0.01,
            clock=lambda:now[0], sleep=lambda amount:now.__setitem__(0, now[0] + amount))

        self.assertTrue(disconnected)
        self.assertEqual(connection.queries, 2)
        self.assertLessEqual(now[0], 0.1)

    def test_remains_unconfirmed_when_client_stays_present_until_timeout(self):
        client = SimpleNamespace(resource_base=0x1200000, resource_mask=0x1fffff)
        now = [0.0]
        connection = _ReplyConnection([client])
        disconnected = wait_for_client_disconnect(
            connection, 0x1200000, timeout_s=0.025, poll_interval_s=0.01,
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
                client_is_connected(connection, 0x1200000)

    def test_invalid_or_ambiguous_client_catalog_fails_closed(self):
        duplicate = _ReplyConnection([
            SimpleNamespace(resource_base=0x1200000, resource_mask=0x1fffff),
            SimpleNamespace(resource_base=0x1200000, resource_mask=0x1fffff),
        ])

        with self.assertRaises(RuntimeError):
            client_is_connected(duplicate, 0x1200000)
        with self.assertRaises(ValueError):
            client_is_connected(duplicate, True)


if __name__ == '__main__':
    unittest.main()
