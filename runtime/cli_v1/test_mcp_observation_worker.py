import asyncio
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from runtime.cli_v1.mcp_server import create_server, main
from runtime.cli_v1.test_mcp_process_identity import FakeX, metadata
from runtime.guarded_x11_v1.test_observation_worker import reader_backend


class MCPObservationTests(unittest.IsolatedAsyncioTestCase):
    async def test_startup_selected_worker_captures_real_guarded_input(self):
        fake = FakeX(self)
        fake.backend.d.get_display_name = lambda:':fake-qualified'
        backend = reader_backend(fake,lambda *args:SimpleNamespace(data=fake.raw,depth=24,visual=1))
        with tempfile.TemporaryDirectory() as td, \
                patch('runtime.guarded_x11_v1.observation_worker.open_readonly_backend',return_value=backend), \
                patch('runtime.guarded_x11_v1.observation_worker.read_linux_x11_process_identity',side_effect=lambda *args:fake.generation), \
                patch('runtime.guarded_x11_v1.target_queries.X11TargetQueries') as query:
            query.return_value.read.side_effect = lambda op,xid:True if op=='focus' else fake.generation
            server = create_server({'app':20},td,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,guarded_observation_worker=True)
            try:
                source = metadata(await server.call_tool('interface_guarded_observe',{}))
                minted = metadata(await server.call_tool('interface_guarded_mint',dict(alias='field',
                    source_sequence=source['source']['sequence'],point=[8,8],region_size=[12,12])))
                result = metadata(await server.call_tool('interface_guarded_input',dict(alias='field',
                    offset=minted['offset'],interaction='keyboard',observe_after=False,
                    tail=[dict(op='key_chord',keys=['CTRL','a'])])))
                self.assertEqual(result['status'],'completed',result)
                self.assertTrue(result['session']['observation_worker'])
                self.assertFalse(result['session']['observations']['retired'])
                self.assertEqual(fake.emissions,[(2,1),(2,2),(3,2),(3,1)])
                self.assertTrue(list(Path(td).rglob('isolated-observations/observation-*.json')))
            finally: await server.call_tool('interface_close',{})


class StartupTests(unittest.TestCase):
    def test_requires_explicit_query_worker_before_output_creation(self):
        with tempfile.TemporaryDirectory() as td:
            for value in (True,1,'yes',None):
                out = Path(td)/'absent'
                with self.assertRaises(ValueError):
                    create_server({'app':20},out,session_mode='guarded-x11',guarded_observation_worker=value)
                self.assertFalse(out.exists())

    def test_cli_forwards_explicit_selection(self):
        with tempfile.TemporaryDirectory() as td:
            targets = Path(td)/'targets.json';targets.write_text('{"app":20}')
            output = Path(td)/'out'
            with patch('sys.argv',['server','--targets',str(targets),'--output-directory',str(output),
                    '--session-mode','guarded-x11','--guarded-process-identity','--guarded-query-worker',
                    '--guarded-observation-worker']),patch('runtime.cli_v1.mcp_server.create_server') as create:
                main()
            create.assert_called_once_with({'app':20},output,display_name=None,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True,guarded_observation_worker=True)
