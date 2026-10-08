import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createInstrumentedRelayClient} from '../../../runtime/host_v1/relay_host.mjs';
import {createPrimaryTrialCaller} from './primary-policy.mjs';

test('the actual failed focus interaction is rejected before any host request',async()=>{
 const dir=join(await mkdtemp(join(tmpdir(),'primary-invalid-interaction-')),'host');
 const host=await createInstrumentedRelayClient({command:process.execPath,args:['-e',"require('node:readline').createInterface({input:process.stdin}).on('line',line=>{const r=JSON.parse(line);console.log(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,result:{content:[{type:'text',text:'{}'}]}}));});"],evidenceDirectory:dir});
 try {
  const caller=createPrimaryTrialCaller(host,'guarded-local',{text:()=>{},image:()=>{}});
  const failed=JSON.parse(await readFile(new URL('../guarded-local/host/request-4.json',import.meta.url)));
  await assert.rejects(caller.call(failed.tool,failed.arguments),/invalid guarded interaction/);
  assert.equal(host.state().attempts,0,'invalid interaction must not cross the host boundary');
  assert.equal(caller.state().stopped,'invalid guarded interaction');
  await assert.rejects(caller.call(failed.tool,{...failed.arguments,interaction:'keyboard'}),/trial stopped/);
  assert.equal(host.state().attempts,0,'corrected arguments do not silently restart a stopped arm');
 } finally {await host.close();}
});
