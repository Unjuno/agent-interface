import test from 'node:test';
import assert from 'node:assert/strict';
import {createPrimaryCaller} from './primary_caller.mjs';
const result = (payload,isError=false) => ({status:'returned',result:{isError,content:[{type:'text',text:JSON.stringify(payload)}]}});
const failure=result({operation:'guarded_input',status:'execution_failed',replay_allowed:false,
  session:{state:'open',binding_revision:7,recovery_required:true}},true);
const recovered=result({operation:'guarded_recover_input',status:'input_recovered',
  previous_binding_revision:7,binding_revision:8,release:{verified:true,keys_down:[],buttons_down:[]},
  recovery_required:false,review_required:true,replay_allowed:false});

test('explicit recovery can release once after a known guarded input failure, without re-enabling input',async()=>{
 const calls=[];const host={sendPresented:async(tool,args)=>{calls.push([tool,args]);return tool==='interface_guarded_input'?failure:recovered;}};
 const caller=createPrimaryCaller(host,'guarded-local',{});
 assert.equal(await caller.input('cell',[1,1],'keyboard',[]),failure);
 assert.ok(caller.state().stopped);
 await assert.rejects(caller.call('interface_guarded_recover_input',{current_binding_revision:6}),/recovery/);
 assert.equal(await caller.call('interface_guarded_recover_input',{current_binding_revision:7}),recovered);
 await assert.rejects(caller.call('interface_guarded_recover_input',{current_binding_revision:7}),/recovery|stopped/);
 await assert.rejects(caller.input('cell',[1,1],'keyboard',[]),/stopped/);
 assert.deepEqual(calls.map(x=>x[0]),['interface_guarded_input','interface_guarded_recover_input']);
});

test('unrelated or uncertain stops cannot authorize recovery',async()=>{
 const calls=[];const host={sendPresented:async(tool,args)=>{calls.push(tool);throw Error('uncertain transport');}};
 const caller=createPrimaryCaller(host,'guarded-local',{});
 await assert.rejects(caller.input('cell',[1,1],'keyboard',[]),/uncertain/);
 await assert.rejects(caller.call('interface_guarded_recover_input',{current_binding_revision:7}),/stopped|recovery/);
 assert.deepEqual(calls,['interface_guarded_input']);
});

test('unknown recovery delivery consumes the single permit',async()=>{
 const calls=[];const caller=createPrimaryCaller({sendPresented:async tool=>{
   calls.push(tool);if(tool==='interface_guarded_input')return failure;throw Error('recovery transport uncertain');
 }},'guarded-local',{});
 await caller.input('cell',[1,1],'keyboard',[]);
 await assert.rejects(caller.call('interface_guarded_recover_input',{current_binding_revision:7}),/uncertain/);
 await assert.rejects(caller.call('interface_guarded_recover_input',{current_binding_revision:7}),/recovery/);
 assert.deepEqual(calls,['interface_guarded_input','interface_guarded_recover_input']);
});

for (const bad of [
 {operation:'guarded_input',status:'completed',replay_allowed:false,session:{state:'open',binding_revision:7,recovery_required:true}},
 {operation:'guarded_input',status:'execution_failed',replay_allowed:false,session:{state:'closed',binding_revision:7,recovery_required:true}},
 {operation:'guarded_input',status:'execution_failed',replay_allowed:true,session:{state:'open',binding_revision:7,recovery_required:true}},
 {operation:'guarded_input',status:'execution_failed',replay_allowed:false,session:{state:'open',binding_revision:7,recovery_required:false}},
]) test('unconfirmed failure does not authorize release recovery '+JSON.stringify(bad),async()=>{
 let count=0;const caller=createPrimaryCaller({sendPresented:async()=>{count++;return result(bad,true);}},'guarded-local',{});
 await caller.input('cell',[1,1],'keyboard',[]);
 await assert.rejects(caller.call('interface_guarded_recover_input',{current_binding_revision:7}),/recovery/);
 assert.equal(count,1);
});

test('primary exchange keeps release recovery explicit and retains original stopped state',async()=>{
 const {createPrimaryExchange}=await import('./primary_exchange.mjs');
 const {mkdtemp,readFile,rm}=await import('node:fs/promises');
 const {tmpdir}=await import('node:os');const {join}=await import('node:path');
 const dir=await mkdtemp(join(tmpdir(),'primary-recovery-'));
 try {
  const calls=[];const host={sendPresented:async tool=>{calls.push(tool);return tool==='interface_guarded_input'?failure:recovered;}};
  const exchange=await createPrimaryExchange({host,route:'guarded-local',directory:join(dir,'exchange')});
  const input=await exchange.execute({id:1,method:'input',args:['cell',[1,1],'keyboard',[]]});
  assert.ok(input.caller_state.stopped);
  const cleanup=await exchange.execute({id:2,method:'call',args:['interface_guarded_recover_input',{current_binding_revision:7}]});
  assert.ok(cleanup.caller_state.stopped);
  assert.equal(JSON.parse(await readFile(cleanup.original_reply_path,'utf8')).result.isError,false);
  await assert.rejects(exchange.execute({id:3,method:'input',args:['cell',[1,1],'keyboard',[]]}),/stopped/);
  assert.deepEqual(calls,['interface_guarded_input','interface_guarded_recover_input']);
 } finally {await rm(dir,{recursive:true,force:true});}
});

test('normal MCP envelope with execution_failed also permits one explicit recovery',async()=>{
 const calls=[];const normalFailure=result({operation:'guarded_input',status:'execution_failed',replay_allowed:false,
  session:{state:'open',binding_revision:0,recovery_required:true}},false);
 const caller=createPrimaryCaller({sendPresented:async tool=>{calls.push(tool);return tool==='interface_guarded_input'?normalFailure:recovered;}},'guarded-local',{});
 await caller.input('cell',[1,1],'keyboard',[]);
 assert.ok(caller.state().stopped);
 await caller.call('interface_guarded_recover_input',{current_binding_revision:0});
 assert.ok(caller.state().stopped);
 assert.deepEqual(calls,['interface_guarded_input','interface_guarded_recover_input']);
});
