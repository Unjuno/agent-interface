import asyncio, base64, io, sys, tempfile
from collections import Counter
from pathlib import Path
from PIL import Image

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent / 'standard_mcp_task_ledger_57_v1'))
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.mcp_relay import Relay
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory
from provider_attempt_recorder import ProviderAttemptRecorder
from recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller

class Client:
    def __init__(self, server): self.server = server
    async def call_tool(self, name, arguments): return await self.server.call_tool(name, arguments)

async def main():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        server_root = root / 'server'; server_root.mkdir()
        (server_root / 'compiled-profile-mode').write_text('enabled')
        server = create_server({'app': 20}, server_root, session_mode='guarded-x11',
            guarded_process_identity=True, guarded_query_worker=True, guarded_owned_process=True,
            _guarded_owner_factory=_fake_owner_factory)
        caller = RecordedPublicMcpCaller(Relay(Client(server)), ProviderAttemptRecorder(root/'ledger'))
        try:
            obs = await caller.call_tool(None, 'inspect', 'interface_guarded_observe', {})
            rows = [x for x in obs['result']['content'] if x.get('type') == 'image']
            print('image_count', len(rows))
            raw = base64.b64decode(rows[0]['data'], validate=True)
            im = Image.open(io.BytesIO(raw)).convert('RGB')
            print('size', im.size, 'unique', len(Counter(im.getdata())))
            print('common_colors', Counter(im.getdata()).most_common(12))
        finally:
            await server.call_tool('interface_close', {})

if __name__ == '__main__':
    asyncio.run(main())
