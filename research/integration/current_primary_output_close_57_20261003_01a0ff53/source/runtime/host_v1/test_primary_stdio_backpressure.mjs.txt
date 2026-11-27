import test from 'node:test';
import assert from 'node:assert/strict';
import {PassThrough, Writable} from 'node:stream';
import {servePrimaryLines} from './primary_stdio.mjs';

const turn=()=>new Promise(resolve=>setImmediate(resolve));
function heldSink() {
  let callback,open=false,bytes='';
  const output=new Writable({highWaterMark:1,write(chunk,_encoding,done){
    bytes+=chunk;
    if(open)done();else callback=done;
  }});
  return {output,rows:()=>bytes.trim().split('\n').filter(Boolean).map(JSON.parse),
    flush(){open=true;const done=callback;callback=null;done?.();}};
}
function committed() {
  const input=new PassThrough(),sink=heldSink();
  let release,calls=0,completed=0;
  const exchange={state:()=>({next_id:2}),execute:async()=>{
    calls++;await new Promise(resolve=>{release=resolve;});completed++;return {id:1};
  }};
  let settled=false;
  const outcome=servePrimaryLines({input,output:sink.output,exchange})
    .then(()=>({status:'resolved'}),error=>({status:'rejected',error}))
    .finally(()=>{settled=true;});
  input.write('{"id":1}\n');
  return {input,sink,outcome,release:()=>release(),calls:()=>calls,completed:()=>completed,settled:()=>settled};
}

// Removing the outstanding-response guard makes blocked output grow with the burst.
test('blocked busy output bounds response work for a batch of rejected commands',async()=>{
  const s=committed();
  try {
    await turn();
    s.input.write(Array.from({length:256},(_,i)=>JSON.stringify({id:i+2})+'\n').join(''));
    await turn();
    assert.ok(s.sink.output.writableLength<1024,'busy replies accumulated behind the stalled sink');
    assert.equal(s.calls(),1);
    assert.equal(s.input.isPaused(),true);
    assert.equal(s.settled(),false);
  } finally {s.release();s.input.end();s.sink.flush();await s.outcome;}
});

// Resolving/abandoning the owner on overload before the original promise settles fails here.
test('overload preserves the committed result before rejecting the stream owner',async()=>{
  const s=committed();
  try {
    await turn();s.input.write('{"id":2}\n{"id":3}\n');await turn();
    s.sink.flush();await turn();
    assert.equal(s.completed(),0);assert.equal(s.settled(),false);
    s.release();s.input.end();
    const result=await s.outcome;
    assert.equal(result.status,'rejected');assert.match(result.error.message,/busy response backlog/);
    assert.equal(s.calls(),1);assert.equal(s.completed(),1);
    assert.deepEqual(s.sink.rows().map(row=>row.status),['busy','returned']);
    assert.deepEqual(s.sink.rows()[1].result,{id:1});
  } finally {s.release();s.input.end();s.sink.flush();await s.outcome;}
});

// Failing to clear the observed busy write would wrongly stop these later refusals.
test('separately observed busy replies remain available during one committed command',async()=>{
  const s=committed();
  try {
    await turn();s.input.write('{"id":2}\n');await turn();s.sink.flush();await turn();
    s.input.write('{"id":2}\n');await turn();
    assert.deepEqual(s.sink.rows().map(row=>row.status),['busy','busy']);
    assert.equal(s.calls(),1);assert.equal(s.completed(),0);
    s.release();s.input.end();assert.deepEqual(await s.outcome,{status:'resolved'});
    assert.deepEqual(s.sink.rows().map(row=>row.status),['busy','busy','returned']);
    assert.equal(s.completed(),1);
  } finally {s.release();s.input.end();s.sink.flush();await s.outcome;}
});
