"""Runtime eligibility regressions; fake processes only, no native peer launch."""
import io
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from research.live_control import codex_app_server_client_v2 as module


class RuntimeEligibilityTests(unittest.TestCase):
    def refuse_before_side_effects(self, platform, version, capability, message):
        factory = Mock(side_effect=AssertionError('factory invoked before eligibility'))
        environment = SimpleNamespace(name=platform)
        if capability:
            environment.set_blocking = lambda *_: None
        with patch.object(module, 'os', environment), \
                patch.object(module, 'sys', SimpleNamespace(version_info=version), create=True), \
                patch('builtins.open', side_effect=AssertionError('journal opened before eligibility')) as opened, \
                patch.object(module.threading, 'Thread') as reader:
            with self.assertRaises(module.AppServerError) as result:
                module.CodexAppServerClient(['inert'], journal_path='must-not-open', process_factory=factory)
            self.assertEqual(type(result.exception).__name__, 'AppServerUnsupportedRuntime')
            self.assertIn(message, str(result.exception))
            factory.assert_not_called()
            opened.assert_not_called()
            reader.assert_not_called()

    def test_windows_311_refused_even_if_api_is_injected(self):
        for capability in [False, True]:
            with self.subTest(capability=capability):
                self.refuse_before_side_effects('nt', (3, 11), capability, 'Python 3.12 or later on Windows')

    def test_windows_312_without_callable_api_refused(self):
        self.refuse_before_side_effects('nt', (3, 12), False, 'os.set_blocking')

    def test_posix_without_callable_api_refused(self):
        self.refuse_before_side_effects('posix', (3, 11), False, 'os.set_blocking')

    def test_eligible_environments_reach_factory_and_preserve_call(self):
        for platform, version in [('nt', (3, 12)), ('nt', (3, 13)), ('posix', (3, 11))]:
            with self.subTest(platform=platform, version=version):
                process = SimpleNamespace(stdin=io.StringIO(), stdout=io.StringIO(), stderr=io.StringIO(), poll=lambda: 0)
                factory = Mock(return_value=process)
                environment = SimpleNamespace(name=platform, set_blocking=lambda *_: None)
                with patch.object(module, 'os', environment), \
                        patch.object(module, 'sys', SimpleNamespace(version_info=version), create=True):
                    client = module.CodexAppServerClient(['inert'], process_factory=factory)
                try:
                    client._reader.join(timeout=.5)
                    self.assertFalse(client._reader.is_alive())
                    factory.assert_called_once_with(['inert'], cwd=None, stdin=module.subprocess.PIPE,
                                                    stdout=module.subprocess.PIPE, stderr=module.subprocess.PIPE,
                                                    text=True, encoding='utf-8', errors='strict', bufsize=1)
                    self.assertFalse(client._send_uncertain)
                finally:
                    client.close(timeout=.5)
                    for stream in [process.stdin, process.stdout, process.stderr]:
                        stream.close()


if __name__ == '__main__':
    unittest.main()
