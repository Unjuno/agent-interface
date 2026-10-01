import test from 'node:test';
import assert from 'node:assert/strict';
import {PassThrough,Writable} from 'node:stream';
import {servePrimaryLines,validatePrimaryConfig} from './primary_stdio.mjs';

function setup(execute) {
  const input=new PassThrough(),output=new PassThrough();let bytes='';
  output.on('data',chunk=>{bytes+=chunk});
  let next=1;
  const exchange={state:()=>({next_id:next}),execute:async request=>{next++;return execute(request);}};
  return {input,output,exchange,rows:()=>bytes.trim().split('\n').filter(Boolean).map(JSON.parse)};
}
test('numbered commands return exact file/text descriptors with no image encoding',async()=>{
  const value={id:1,attempt:3,presented_text:['original metadata',{isError:false}],
    images:[{path:'/original.png',sha256:'abc',bytes:4,mime_type:'image/png'}]};
  const s=setup(async()=>value);const pending=servePrimaryLines(s);
  s.input.end('{"id":1,"method":"observe","args":[]}\n');await pending;
  assert.deepEqual(s.rows()[0],{schema:'agent-interface/primary-stdio-v1',status:'returned',result:value});
});
test('commands arriving while outstanding are rejected rather than queued',async()=>{
  let release,calls=0;const s=setup(async()=>{calls++;await new Promise(r=>{release=r;});return {id:1};});
  const pending=servePrimaryLines(s);s.input.write('{"id":1}\n');
  while(!release)await new Promise(r=>setImmediate(r));
  s.input.write('{"id":2}\n');await new Promise(r=>setImmediate(r));
  assert.equal(calls,1);assert.equal(s.rows()[0].status,'busy');assert.equal(s.rows()[0].operation_invoked,false);
  release();s.input.end();await pending;assert.equal(calls,1);
  assert.equal(s.rows()[1].status,'returned');
});
test('EOF waits for the already committed command without replaying it',async()=>{
  let release,calls=0;const s=setup(async()=>{calls++;await new Promise(r=>{release=r;});return {id:1};});
  let ended=false;const pending=servePrimaryLines(s).then(()=>{ended=true;});
  s.input.write('{"id":1}\n');while(!release)await new Promise(r=>setImmediate(r));
  s.input.end();await new Promise(r=>setImmediate(r));assert.equal(ended,false);
  release();await pending;assert.equal(calls,1);assert.equal(s.rows().length,1);
});
test('malformed JSON is refused without invoking exchange or consuming a command',async()=>{
  let calls=0;const s=setup(async()=>{calls++;return {id:1};});const pending=servePrimaryLines(s);
  s.input.write('{invalid\n');await new Promise(r=>setImmediate(r));
  assert.equal(calls,0);assert.equal(s.rows()[0].status,'refused');assert.equal(s.rows()[0].next_id,1);
  s.input.end('{"id":1}\n');await pending;assert.equal(calls,1);
});
test('command error reports uncertainty and state without retry',async()=>{
  let calls=0;const s=setup(async()=>{calls++;throw Error('reply write failed after input');});
  const pending=servePrimaryLines(s);s.input.end('{"id":1}\n');await pending;
  const row=s.rows()[0];assert.equal(row.status,'command_error');assert.equal(row.replay_allowed,false);
  assert.match(row.error,/after input/);assert.equal(calls,1);assert.equal(row.state.next_id,2);
});
test('output failure rejects the stream owner after one completed command',async()=>{
  const input=new PassThrough();let calls=0;
  const output=new Writable({write(_chunk,_encoding,callback){callback(Error('sink unavailable'));}});
  const exchange={state:()=>({next_id:2}),execute:async()=>{calls++;return {id:1};}};
  const pending=servePrimaryLines({input,output,exchange});input.end('{"id":1}\n');
  await assert.rejects(pending,/sink unavailable/);assert.equal(calls,1);
});
const valid={host:{command:'/node',args:[],evidenceDirectory:'/evidence'},route:'guarded-local',exchangeDirectory:'/exchange'};
test('config refuses unknown routes and fields before starting a host',()=>{
  assert.deepEqual(validatePrimaryConfig(valid),valid);
  for(const config of [{...valid,route:'typo'},{...valid,extra:true},{...valid,host:{...valid.host,shell:true}},
    {...valid,host:{...valid.host,args:[null]}},{...valid,exchangeDirectory:''}])
    assert.throws(()=>validatePrimaryConfig(config));
});
