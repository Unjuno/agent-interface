import unittest

from formal import IMAGE, auditor_command, runner_command


def mounts(command):
    return [command[index + 1] for index, token in enumerate(command[:-1])
            if token == "--mount"]


class ContainerBoundaryTests(unittest.TestCase):
    def test_auditor_reads_raw_read_only_and_writes_only_separate_output(self):
        source = "type=bind,source=C:/study,target=/src,readonly"
        raw = "type=bind,source=C:/evidence/raw,target=/raw,readonly"
        audit = "type=bind,source=C:/evidence/audit,target=/audit"
        command = auditor_command(source, raw, audit)
        self.assertEqual(command[:5], ["docker", "--context", "desktop-linux", "run", "--rm"])
        self.assertEqual(mounts(command), [source, raw, audit])
        self.assertEqual(command[-3:], [IMAGE, "python", "/src/audit.py"])
        self.assertIn("readonly", mounts(command)[1])
        self.assertNotIn("readonly", mounts(command)[2])
        self.assertNotEqual(mounts(command)[1].split(",source=", 1)[1].split(",", 1)[0],
                            mounts(command)[2].split(",source=", 1)[1].split(",", 1)[0])

    def test_runner_has_its_own_raw_write_mount(self):
        source = "type=bind,source=C:/study,target=/src,readonly"
        raw_write = "type=bind,source=C:/evidence/raw,target=/out"
        command = runner_command(source, raw_write)
        self.assertEqual(mounts(command), [source, raw_write])
        self.assertEqual(command[-3:], [IMAGE, "python", "/src/runner.py"])


if __name__ == "__main__":
    unittest.main()
