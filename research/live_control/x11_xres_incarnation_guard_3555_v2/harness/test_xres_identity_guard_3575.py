import unittest

from xres_identity_guard_3575 import owner_identity, permits


class Reply:
    def __init__(self, xid, mask, pids):
        self.spec = type("Spec", (), {"client": xid, "mask": mask})()
        self.value = pids


class Display:
    def __init__(self, rows, version=(1, 2)):
        self.rows = rows
        self.version = type("Version", (), {"server_major": version[0], "server_minor": version[1]})()
        self.request = None

    def res_query_version(self):
        return self.version

    def res_query_client_ids(self, specs):
        self.request = specs
        return type("Reply", (), {"ids": self.rows})()


class XResIdentityGuardTests(unittest.TestCase):
    def test_owner_query_uses_server_local_pid_and_proc_start(self):
        d = Display([Reply(4194304, 1, []), Reply(4194304, 2, [16])])
        got = owner_identity(d, 4194304, start_reader=lambda pid: "5087262")
        self.assertEqual(got["pid"], 16)
        self.assertEqual(got["pid_start_ticks"], "5087262")
        self.assertEqual(d.request, [{"client": 4194304, "mask": 3}])

    def test_refuses_recycled_xid_with_new_owner(self):
        captured = {"xid": 4194304, "pid": 15, "pid_start_ticks": "5087261"}
        current = {"xid": 4194304, "pid": 16, "pid_start_ticks": "5087262"}
        self.assertEqual(permits(captured, current), (False, "PROCESS_INCARNATION_MISMATCH"))

    def test_refuses_pid_reuse_with_new_start_ticks(self):
        captured = {"xid": 4194304, "pid": 15, "pid_start_ticks": "100"}
        current = {"xid": 4194304, "pid": 15, "pid_start_ticks": "200"}
        self.assertFalse(permits(captured, current)[0])

    def test_fails_closed_on_missing_identity(self):
        self.assertEqual(permits({"xid": 4}, {"xid": 4}), (False, "IDENTITY_INCOMPLETE"))

    def test_allows_same_incarnation(self):
        identity = {"xid": 4, "pid": 12, "pid_start_ticks": "9"}
        self.assertEqual(permits(identity, identity), (True, "SAME_PROCESS_INCARNATION"))

    def test_requires_xres_1_2(self):
        d = Display([], version=(1, 1))
        with self.assertRaisesRegex(RuntimeError, "version < 1.2"):
            owner_identity(d, 4)

    def test_missing_local_pid_fails_closed(self):
        d = Display([Reply(4, 1, [])])
        with self.assertRaisesRegex(RuntimeError, "one local process identity"):
            owner_identity(d, 4)


if __name__ == "__main__":
    unittest.main()
