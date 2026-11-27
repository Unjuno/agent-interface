import asyncio, json
from pathlib import Path
from runtime.cli_v1.test_mcp_owned_process import create_server, metadata, _fake_owner_factory, _compiled_profile_payload

async def main():
    out=Path(__file__).resolve().parent/'run'
    out.mkdir(parents=True, exist_ok=False)
    (out/'compiled-profile-mode').write_text('enabled')
    server=create_server({'app':20},out,session_mode='guarded-x11',
        guarded_process_identity=True,guarded_query_worker=True,
        guarded_owned_process=True,guarded_retention_mode='journal',
        _guarded_owner_factory=_fake_owner_factory)
    try:
        observed=metadata(await server.call_tool('interface_guarded_observe',{}))
        minted=metadata(await server.call_tool('interface_guarded_mint',dict(
            alias='field',source_sequence=observed['source']['sequence'],
            point=[8,8],region_size=[12,12],freshness_ms=5000)))
        payload=_compiled_profile_payload(observed['session']['compiled_scope'],
            observed['session']['compiled_surface'],minted['offset'])
        payload['wait_for_result_ms']=10000
        result=metadata(await server.call_tool('interface_guarded_compiled',payload))
        (out/'public-call-initial.json').write_text(json.dumps(result,indent=2))
        call_id=result.get('call_id')
        deadline=asyncio.get_running_loop().time()+20
        while call_id and result.get('status') in ('pending','running') and asyncio.get_running_loop().time()<deadline:
            await asyncio.sleep(.02)
            result=metadata(await server.call_tool('interface_results',{'call_id':call_id,'include_image':False}))
        (out/'public-call-terminal.json').write_text(json.dumps(result,indent=2))
        close=metadata(await server.call_tool('interface_close',{}))
        (out/'close.json').write_text(json.dumps(close,indent=2))
        print(json.dumps({'initial_status':json.loads((out/'public-call-initial.json').read_text()).get('status'),
            'terminal_status':result.get('status'),'method':result.get('method_receipt'),
            'close':close.get('status'),'owner_retired':close.get('owner_process_retired'),
            'call_id':call_id},indent=2))
    finally:
        try:
            close=metadata(await server.call_tool('interface_close',{}))
            (out/'close-finally.json').write_text(json.dumps(close,indent=2))
        except Exception as e:
            (out/'close-finally-error.txt').write_text(repr(e))

if __name__ == '__main__':
    asyncio.run(main())

