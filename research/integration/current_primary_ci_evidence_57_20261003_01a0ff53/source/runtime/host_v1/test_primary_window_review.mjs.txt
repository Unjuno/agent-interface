import test from 'node:test';
import assert from 'node:assert/strict';
import {createPrimaryCaller} from './primary_caller.mjs';

test('configured reviewWindow uses actual snapshotted target and unchanged result',async()=>{
 const calls=[],response={result:{content:[{type:'text',text:'{"status":"reviewed"}'}]}};
 const options={reviewWindowId:8388611};
 const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{calls.push({tool,args});return response;}},'guarded-local',{},[],options);
 assert.equal(typeof caller.reviewWindow,'function');
 options.reviewWindowId=123;
 const reviewWindow=caller.reviewWindow;
 assert.equal(await reviewWindow(),response);
 assert.deepEqual(calls,[{tool:'interface_guarded_review_window',args:{window_id:8388611}}]);
 assert.equal(caller.state().stopped,null);
});

for(const value of [undefined,null,0,-1,1.5,'8388611',NaN,Infinity])test('invalid configured target '+String(value)+' stops locally',async()=>{
 let calls=0;
 const caller=createPrimaryCaller({sendPresented:async()=>{calls++;}},'guarded-local',{},[],{reviewWindowId:value});
 assert.equal(typeof caller.reviewWindow,'function');
 await assert.rejects(caller.reviewWindow(),TypeError);
 assert.ok(caller.state().stopped);
 await assert.rejects(caller.call('interface_guarded_input',{alias:'x',interaction:'click'}),/stopped/);
 assert.equal(calls,0);
});

test('per-call arguments cannot change target and STOP still allows close',async()=>{
 const calls=[],response={result:{content:[{type:'text',text:'{"status":"closed"}'}]}};
 const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{calls.push({tool,args});return response;}},'guarded-local',{},[],{reviewWindowId:8388611});
 assert.equal(typeof caller.reviewWindow,'function');
 await assert.rejects(caller.reviewWindow({window_id:123}),TypeError);
 await assert.rejects(caller.reviewWindow(),/stopped/);
 assert.equal(await caller.call('interface_close',{}),response);
 assert.deepEqual(calls,[{tool:'interface_close',args:{}}]);
});

test('direct mode cannot review a guarded window',async()=>{
 let calls=0;
 const caller=createPrimaryCaller({sendPresented:async()=>{calls++;}},'direct-post',{},[],{reviewWindowId:8388611});
 assert.equal(typeof caller.reviewWindow,'function');
 await assert.rejects(caller.reviewWindow(),TypeError);
 assert.equal(calls,0);
});
