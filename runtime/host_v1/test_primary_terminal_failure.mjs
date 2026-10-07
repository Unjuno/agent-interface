/** Terminal first-failure precedence with real streams and inert host factories. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {PassThrough,Writable} from 'node:stream';
import {createInterface} from 'node:readline';
import {pathToFileURL} from 'node:url';
import {TextDecoder} from 'node:util';
import {setImmediate as tick} from 'node:timers/promises';
import {createContext,SourceTextModule,SyntheticModule} from 'node:vm';

// Load the production source unchanged. Only application factories are replaced:
// no relay process, command execution, provider, GUI, or network is involved.
// Run with: node --experimental-vm-modules --test this-file.mjs
async function inertOwner(counters) {
  const sourceUrl=new URL('./primary_stdio.mjs',import.meta.url);
  const context=createContext({process:{argv:[]},console});
  const exports={
    'node:readline':{createInterface},'node:fs/promises':{readFile},
    'node:url':{pathToFileURL},'node:util':{TextDecoder},
    './relay_host.mjs':{createInstrumentedRelayClient:async()=>{
      counters.starts++;
      return {async close(){counters.closes++;return {code:0,signal:null};}};
    }},
    './primary_exchange.mjs':{createPrimaryExchange:async()=>{
      counters.exchanges++;
      return {state:()=>({next_id:1}),async execute(){
        counters.executions++;throw Error('unexpected command execution');
      }};
    }}
  };
  const module=new SourceTextModule(await readFile(sourceUrl,'utf8'),{
    context,identifier:sourceUrl.href,
    initializeImportMeta(meta,mod){meta.url=mod.identifier;}
  });
  await module.link(specifier=>{
    assert.ok(Object.hasOwn(exports,specifier),'unexpected import: '+specifier);
    const values=exports[specifier];
    return new SyntheticModule(Object.keys(values),function(){
      for(const [name,value] of Object.entries(values))this.setExport(name,value);
    },{context});
  });
  await module.evaluate();
  return module.namespace.runPrimaryStdio;
}

for(const withInputError of [true,false])for(const terminal of ['close','error','success']){
  const name=(withInputError?'earlier input error survives ':'sole terminal ')+terminal;
  test(name,{timeout:3000},async t=>{
    const counters={starts:0,closes:0,exchanges:0,executions:0,settlements:0};
    const runPrimaryStdio=await inertOwner(counters);
    const events=[],rows=[];
    let readyResolve,terminalResolve,firstResolve,heldCallback,received;
    let outcome='pending';
    const readySeen=new Promise(resolve=>readyResolve=resolve);
    const terminalSeen=new Promise(resolve=>terminalResolve=resolve);
    const firstSeen=new Promise(resolve=>firstResolve=resolve);
    const first=Object.assign(Error('first input failure'),{code:'FIRST_INPUT_FAILURE'});
    const second=Object.assign(Error('terminal callback failure'),{code:'TERMINAL_OUTPUT_FAILURE'});
    const input=new PassThrough({autoDestroy:false});
    const output=new Writable({autoDestroy:false,highWaterMark:1,write(chunk,_encoding,done){
      const row=JSON.parse(String(chunk));rows.push(row);events.push('write:'+row.status);
      if(row.status==='ready'){done();readyResolve();}
      else if(row.status==='terminal'){heldCallback=done;terminalResolve();}
      else done(Error('unexpected output status: '+row.status));
    }});
    const foreignInputError=()=>{events.push('input:error');firstResolve();};
    const foreignOutputError=()=>events.push('output:error');
    const foreignOutputClose=()=>events.push('output:close');
    input.on('error',foreignInputError);
    output.on('error',foreignOutputError);output.on('close',foreignOutputClose);
    const config={host:{command:'INERT-NOT-LAUNCHED',args:[],evidenceDirectory:'/unused/host'},
      route:'guarded-local',exchangeDirectory:'/unused/exchange'};
    const owner=runPrimaryStdio(config,{input,output}).then(()=>{
      counters.settlements++;outcome='resolved';events.push('owner:resolved');
    },error=>{
      counters.settlements++;received=error;outcome='rejected';events.push('owner:rejected');
    });
    try {
      await readySeen;await tick();input.end();await terminalSeen;
      assert.equal(counters.closes,1,'same host already closed before terminal publication');
      assert.equal(typeof heldCallback,'function');
      if(withInputError){input.destroy(first);await firstSeen;}
      if(terminal==='close')output.destroy();
      else {const callback=heldCallback;heldCallback=null;callback(terminal==='error'?second:undefined);}
      await owner;
    } finally {
      heldCallback?.();input.destroy();output.destroy();await tick();await tick();
    }
    t.diagnostic(JSON.stringify({name,node:process.version,counters,outcome,
      error:received?.code??null,same_first:received===first,events}));
    assert.deepEqual(counters,{starts:1,closes:1,exchanges:1,executions:0,settlements:1});
    assert.deepEqual(input.listeners('error'),[foreignInputError]);
    assert.deepEqual(output.listeners('error'),[foreignOutputError]);
    assert.deepEqual(output.listeners('close'),[foreignOutputClose]);
    assert.deepEqual(rows.map(row=>row.status),['ready','terminal']);
    assert.deepEqual(rows[1],{schema:'agent-interface/primary-stdio-v1',status:'terminal',
      exit:{code:0,signal:null},state:{next_id:1}});
    if(withInputError){assert.equal(outcome,'rejected');assert.equal(received,first);}
    else if(terminal==='error'){assert.equal(outcome,'rejected');assert.equal(received,second);}
    else if(terminal==='close'){assert.equal(outcome,'rejected');assert.equal(received?.code,'PRIMARY_OUTPUT_CLOSED');}
    else {assert.equal(outcome,'resolved');assert.equal(received,undefined);}
  });
}
