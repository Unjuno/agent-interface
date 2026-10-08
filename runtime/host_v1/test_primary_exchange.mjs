import {createInstrumentedRelayClient} from './relay_host.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, readFile, writeFile, readdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createPrimaryExchange} from './primary_exchange.mjs';

async function fixture(send) {
  const parent=await mkdtemp(join(tmpdir(),'primary-exchange-'));
  const directory=join(parent,'exchange');
  const host={sendPresented:send,review:async(a,r)=>({attempt:a,...r}),
    acknowledgeText:async(a,r)=>({attempt:a,...r}),present:async()=>{}};
  return {directory,exchange:await createPrimaryExchange({host,directory,route:'guarded-local'})};
}

test('one command preserves original text and bytes, with exclusive source-bound files',async()=>{
  const png=Buffer.from('synthetic bytes, not a real PNG');
  const reply={attempt:4,result:{content:[{type:'text',text:'{"status":"observed"}'}]}};
  let calls=0;
  const {directory,exchange}=await fixture(async(_tool,_args,sinks)=>{
    calls++;await sinks.text(reply.result.content[0].text);await sinks.text({isError:false});
    await sinks.image({bytes:png,mimeType:'image/png'});return reply;
  });
  const result=await exchange.execute({id:1,method:'observe',args:[]});
  assert.equal(calls,1);assert.equal(result.attempt,4);
  assert.deepEqual(result.presented_text,['{"status":"observed"}',{isError:false}]);
  assert.deepEqual(await readFile(result.images[0].path),png);
  assert.deepEqual(JSON.parse(await readFile(result.original_reply_path)),reply);
  assert.deepEqual(JSON.parse(await readFile(join(directory,'request-1.json'))),{id:1,method:'observe',args:[]});
  await assert.rejects(exchange.execute({id:1,method:'observe',args:[]}),/next command id/);
  assert.equal(calls,1);
});

test('overlap refuses instead of queuing and snapshots the original arguments',async()=>{
  let resolve;let calls=0;let received;
  const {exchange}=await fixture(async(_tool,args)=>{
    calls++;received=args;await new Promise(r=>{resolve=r;});
    return {attempt:1,result:{content:[{type:'text',text:'{"status":"minted"}'}]}};
  });
  const command={id:1,method:'mint',args:['save',1,[50,60],[24,24]]};
  const pending=exchange.execute(command);command.args[2][0]=999;
  await assert.rejects(exchange.execute({id:2,method:'observe',args:[]}),/outstanding/);
  while(!resolve)await new Promise(r=>setImmediate(r));
  assert.deepEqual(received.point,[50,60]);resolve();await pending;assert.equal(calls,1);
});

test('request persistence failure invokes no operation and permits only explicit close',async()=>{
  let calls=0;const {directory,exchange}=await fixture(async()=>{
    calls++;return {result:{content:[{type:'text',text:'{"status":"closed"}'}]}};
  });
  await writeFile(join(directory,'request-1.json'),'occupied');
  await assert.rejects(exchange.execute({id:1,method:'observe',args:[]}),/EEXIST/);
  assert.equal(calls,0);assert.ok(exchange.state().stopped);
  await assert.rejects(exchange.execute({id:2,method:'observe',args:[]}),/exchange stopped/);
  await exchange.execute({id:2,method:'call',args:['interface_close',{}]});assert.equal(calls,1);
  assert.equal(await readFile(join(directory,'request-1.json'),'utf8'),'occupied');
});

test('reply persistence failure retains one effect and blocks replay',async()=>{
  let calls=0;const {directory,exchange}=await fixture(async()=>{
    calls++;return {attempt:1,result:{content:[{type:'text',text:'{"status":"observed"}'}]}};
  });
  await writeFile(join(directory,'original-reply-1.json'),'occupied');
  await assert.rejects(exchange.execute({id:1,method:'observe',args:[]}),/EEXIST/);
  assert.equal(calls,1);assert.ok(exchange.state().stopped);
  await assert.rejects(exchange.execute({id:2,method:'observe',args:[]}),/exchange stopped/);
  assert.equal(calls,1);
});

for(const command of [{id:1,method:'close',args:[]},{id:1,method:'observe',args:[],extra:true},
  {id:1,method:'observe',args:[undefined]}, {id:1,method:'observe',args:[NaN]}])
test('invalid envelope is rejected before host or file publication: '+JSON.stringify(command),async()=>{
  let calls=0;const {directory,exchange}=await fixture(async()=>{calls++;});
  await assert.rejects(exchange.execute(command));assert.equal(calls,0);
  assert.deepEqual(await readdir(directory),[]);
});

test('unknown route refuses before allocating a directory',async()=>{
  const directory=join(await mkdtemp(join(tmpdir(),'primary-exchange-route-')),'exchange');
  await assert.rejects(createPrimaryExchange({host:{},directory,route:'typo'}),/route/);
  await assert.rejects(readdir(directory),/ENOENT/);
});

test('image write failure stops without a repeated native call or an implicit review',async()=>{
  let calls=0;const {directory,exchange}=await fixture(async(_tool,_args,sinks)=>{
    calls++;await sinks.image({bytes:Buffer.from('fixture'),mimeType:'image/png'});
  });
  await writeFile(join(directory,'image-1-1.png'),'occupied');
  await assert.rejects(exchange.execute({id:1,method:'observe',args:[]}),/EEXIST/);
  assert.ok(exchange.state().caller_state.stopped);
  await assert.rejects(exchange.execute({id:2,method:'input',args:['save',[1,1],'click',[]]}),/exchange stopped/);
  assert.equal(calls,1);assert.equal(await readFile(join(directory,'image-1-1.png'),'utf8'),'occupied');
});

test('original presentation is explicit and adds no new host send or review',async()=>{
  let sends=0,presents=0,reviews=0;
  const directory=join(await mkdtemp(join(tmpdir(),'exchange-original-')),'exchange');
  const host={sendPresented:async()=>{sends++;return {attempt:1,result:{content:[{type:'text',text:'{"status":"observed"}'}]}};},
    present:async(attempt,sinks,options)=>{presents++;assert.equal(attempt,1);assert.equal(options.forceImage,true);
      await sinks.image({bytes:Buffer.from('unchanged original'),mimeType:'image/png'});},
    review:async()=>{reviews++;}};
  const exchange=await createPrimaryExchange({host,directory,route:'guarded-local'});
  await exchange.execute({id:1,method:'observe',args:[]});
  const result=await exchange.execute({id:2,method:'presentOriginal',args:[1]});
  assert.equal(result.attempt,null);assert.equal(result.images.length,1);
  assert.equal(sends,1);assert.equal(presents,1);assert.equal(reviews,0);
  assert.equal(JSON.parse(await readFile(result.original_reply_path)),null);
});

test('explicit command attribution reaches the existing host dispatch',async()=>{
 const calls=[];
 const host={sendPresented:async(...args)=>{calls.push(args);return {attempt:1,result:{content:[{type:'text',text:'{"status":"closed"}'}]}};}};
 const exchange=await createPrimaryExchange({host,route:'direct-post',directory:join(await mkdtemp(join(tmpdir(),'exchange-attribution-')),'exchange')});
 const attribution={evaluation_id:'owned-evaluation',phase:'termination',model_stage_id:'stage-1',primary_call_id:'call_owned'};
 await exchange.execute({id:1,method:'call',args:['interface_close',{}],attribution});
 assert.equal(calls.length,1);assert.deepEqual(calls[0][3],attribution);
});

test('command metadata survives actual exchange/caller/relay path and cannot leak into next command',async()=>{
 const root=await mkdtemp(join(tmpdir(),'attribution-path-'));const transport=join(root,'transport');const directory=join(root,'exchange');
 const peer=`require('readline').createInterface({input:process.stdin}).on('line',s=>{const r=JSON.parse(s);console.log(JSON.stringify({id:r.id,tool:r.tool,status:'returned',next_id:r.id+1,result:{content:[{type:'text',text:JSON.stringify({status:r.tool==='interface_close'?'closed':'clock'})}]}}));});`;
 const host=await createInstrumentedRelayClient({command:process.execPath,args:['-e',peer],evidenceDirectory:transport});
 const exchange=await createPrimaryExchange({host,route:'direct-post',directory});
 const attribution={evaluation_id:'owned',phase:'preflight',model_stage_id:'stage-1',primary_call_id:'call_owned'};const original={...attribution};
 try{
  for(const value of [{...attribution,phase:'unknown'},{...attribution,provider_tokens:0},{...attribution,model_stage_id:''}]){
   await assert.rejects(exchange.execute({id:1,method:'call',args:['interface_clock',{}],attribution:value}),TypeError);
   assert.equal(exchange.state().next_id,1);assert.equal(exchange.state().stopped,null);assert.equal(host.state().attempts,0);
  }
  const pending=exchange.execute({id:1,method:'call',args:['interface_clock',{}],attribution});attribution.phase='bounded_repair';
  await assert.rejects(exchange.execute({id:2,method:'call',args:['interface_clock',{}]}),/outstanding/);
  const result=await pending;assert.deepEqual(result.attribution,original);
  await exchange.execute({id:2,method:'call',args:['interface_close',{}]});
  const rows=(await readFile(join(transport,'host-events.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
  const first=rows.filter(r=>r.attempt===1&&['send_requested','reply_available'].includes(r.kind));assert.equal(first.length,2);first.forEach(r=>assert.deepEqual(r.caller_attribution,original));
  rows.filter(r=>r.attempt===2).forEach(r=>assert.equal(Object.hasOwn(r,'caller_attribution'),false));
  const persisted=JSON.parse(await readFile(join(directory,'request-1.json'),'utf8'));assert.deepEqual(persisted.attribution,original);
  const raw=JSON.parse(await readFile(join(transport,'request-1.json'),'utf8'));assert.deepEqual(raw,{id:1,tool:'interface_clock',arguments:{}});
  assert.equal(host.state().attempts,2);assert.equal(exchange.state().next_id,3);
 }finally{await host.close();}
});

