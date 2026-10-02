import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,readdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createInstrumentedRelayClient} from '../../runtime/host_v1/relay_host.mjs';
import {createPrimaryTrialCaller} from './primary-policy.mjs';
const fixture=`require('node:readline').createInterface({input:process.stdin}).on('line',line=>{
 const r=JSON.parse(line); console.log(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,result:{isError:true,content:[{type:'text',text:JSON.stringify({status:'refused',error:'KeyError(4)',input_dispatched:false,replay_allowed:false,session:{binding_revision:1,recovery_required:false}})}]}}));
});`;
const args={alias:'old_source_control',source_sequence:4,point:[230,401],region_size:[24,38]};
const control={id:'revoked-source',tool:'interface_guarded_mint',args,kind:'source',error:'KeyError(4)',revision:1};
test('declared text-only refusal is acknowledged through real host without poisoning the caller',async()=>{
 const dir=join(await mkdtemp(join(tmpdir(),'primary-text-caller-')),'host');
 const host=await createInstrumentedRelayClient({command:process.execPath,args:['-e',fixture],evidenceDirectory:dir});
 try {
  const seen=[];const caller=createPrimaryTrialCaller(host,'guarded-local',{text:x=>seen.push(x),image:()=>{throw Error('unexpected image')}},[control]);
  const reply=await caller.call(control.tool,args,control.id);
  assert.equal(caller.state().stopped,null);
  assert.equal(typeof caller.acknowledgeText,'function','caller must expose separate text acknowledgment');
  const receipt=await caller.acknowledgeText(reply.attempt,{task:'task4',phase:'revoked-source',reason:'Read original KeyError(4) refusal.'});
  assert.equal(receipt.isError,true);assert.equal(caller.state().stopped,null);
  assert.equal(JSON.parse(await readFile(join(dir,'text-acknowledgment-1.json'))).relay_id,reply.id);
  assert.equal((await readdir(dir)).filter(n=>n.startsWith('request-')).length,1);
  assert.ok(seen.some(x=>typeof x==='string'&&x.includes('KeyError(4)')));
  await assert.rejects(caller.acknowledgeText(reply.attempt,{phase:'missing-task',reason:'invalid'}),/invalid primary acknowledgment/);
  assert.equal(caller.state().stopped,'invalid primary acknowledgment arguments');
  assert.equal(host.state().host_blocked,null);
  await assert.rejects(caller.call('interface_clock',{}),/trial stopped/);
 } finally {await host.close();}
});
