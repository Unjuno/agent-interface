"""Read-only stdio replay of an explicitly named completed recovery run."""
import argparse, asyncio, base64, hashlib, json, os, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def digest(data):
    return hashlib.sha256(data).hexdigest()

def snapshot(root):
    return {str(p.relative_to(root)): {'sha256': digest(p.read_bytes()),
            'mtime_ns': p.stat().st_mtime_ns} for p in root.rglob('*') if p.is_file()}

async def check(root, output):
    output = output.resolve()
    if output == root or root in output.parents:
        raise ValueError("write the report outside the retained run")
    before = snapshot(root)
    requests = [(root/f'request-{stage}.json').read_bytes() for stage in (1,2)]
    rows = []
    parameters = StdioServerParameters(command=sys.executable,
        args=[str(Path(__file__).resolve().parents[1]/'native_mcp_v1.py'),
              '--run-directory', str(root)], env=dict(os.environ))
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            for stage, raw in enumerate(requests, 1):
                result = await client.call_tool('native_resume', {
                    'stage': stage, 'decision_sha256': digest(raw), 'timeout': 0})
                assert not result.isError
                m = json.loads(result.content[0].text)
                assert m['exchange']['resumed_read_only'] is True
                images = [b for b in result.content if b.type == 'image']
                assert len(images) == 1
                image_hash = digest(base64.b64decode(images[0].data, validate=True))
                assert image_hash == m['image_reference']['sha256']
                if stage == 1:
                    assert m['continuation']['status'] == 'already_submitted'
                    assert m['outcome_summary']['target_refusal']['input_dispatched'] is False
                    assert m['outcome_summary']['action_status'] is None
                else:
                    assert m['continuation']['status'] == 'unavailable'
                    assert m['outcome_summary']['evaluation_success'] is True
                rows.append({'stage': stage, 'decision_sha256': digest(raw),
                    'image_sha256': image_hash, 'metadata': m})
    after = snapshot(root)
    assert after == before, 'read-only resume changed retained files'
    report = {'scope': 'completed-run read-only MCP replay; no live GUI or input',
              'run_directory': str(root), 'files_unchanged': len(before),
              'before': before, 'after': after, 'responses': rows}
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps({'files_unchanged': len(before),
        'continuations': [r['metadata']['continuation']['status'] for r in rows]}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-directory', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    asyncio.run(check(Path(args.run_directory).resolve(strict=True), Path(args.output)))
