import {writeFile,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const root='/var/tmp/agent-interface-evidence-storage-main/results-local/primary-exchange-01';
const {createInstrumentedRelayClient}=await import(pathToFileURL(join(root,'host/relay_host.mjs')));
const {createPrimaryExchange}=await import(pathToFileURL(join(root,'host/primary_exchange.mjs')));
await writeFile(join(root,'targets.json'),'{"smoke":1}\n',{flag:'wx'});
const host=await createInstrumentedRelayClient({command:'/tmp/agent-interface-mcp-venv/bin/python',
  args:[join(root,'runtime.pyz'),'relay','--','--targets',join(root,'targets.json'),
    '--output-directory',join(root,'server')],evidenceDirectory:join(root,'transport')});
const exchange=await createPrimaryExchange({host,route:'direct-post',directory:join(root,'exchange'),
  options:{observationArguments:{target:'smoke',frame:'screen_physical_px',region:[0,0,10,10]}}});
const results=[];
try {
  const clock=await exchange.execute({id:1,method:'call',args:['interface_clock',{}]});
  results.push(clock);
  const value=JSON.parse(await readFile(clock.original_reply_path));
  assert.equal(value.result.isError,false);
  assert.ok(clock.presented_text.length);assert.equal(clock.images.length,0);
  const invalid=await exchange.execute({id:2,method:'call',args:['interface_validate',{program:{}}]});
  results.push(invalid);
  assert.ok(exchange.state().caller_state.stopped);
  await assert.rejects(exchange.execute({id:3,method:'observe',args:[]}),/trial stopped/);
  assert.equal(host.state().attempts,2);
  // Rejected attempt consumes the local command ID, but sends no MCP request.
  results.push(await exchange.execute({id:4,method:'call',args:['interface_close',{}]}));
  assert.equal(host.state().attempts,3);
} finally {
  const exit=await host.close();
  await writeFile(join(root,'smoke.json'),JSON.stringify({results,exit,state:exchange.state(),
    scope:'Actual packaged host/relay/public MCP; no GUI, input or speed comparison.'},null,2)+'\n',{flag:'wx'});
}
console.log('PASS actual packaged clock, refusal, blocked ordinary call and explicit close');
