/** Sequential line transport for the existing primary exchange. No action queue. */
import {createInterface} from 'node:readline';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {TextDecoder} from 'node:util';
import {createInstrumentedRelayClient} from './relay_host.mjs';
import {createPrimaryExchange} from './primary_exchange.mjs';

const schema='agent-interface/primary-stdio-v1';
const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
const fields=(value,allowed)=>Object.keys(value).every(key=>allowed.includes(key));
export function validatePrimaryConfig(config) {
  if(!object(config)||!fields(config,['host','route','exchangeDirectory','expectations','primaryOptions'])||
    !['guarded-local','direct-post'].includes(config.route)||
    typeof config.exchangeDirectory!=='string'||!config.exchangeDirectory.trim()||
    !object(config.host)||!fields(config.host,['command','args','evidenceDirectory','minimumEvidenceFreeBytes','reuseReviewedImages'])||
    typeof config.host.command!=='string'||!config.host.command.trim()||
    !Array.isArray(config.host.args)||!Array.from(config.host.args).every(arg=>typeof arg==='string')||
    typeof config.host.evidenceDirectory!=='string'||!config.host.evidenceDirectory.trim()||
    (config.expectations!==undefined&&!Array.isArray(config.expectations))||
    (config.primaryOptions!==undefined&&(!object(config.primaryOptions)||!fields(config.primaryOptions,['observationArguments','reviewWindowId']))) )
    throw TypeError('explicit primary route, host, fresh directories and known configuration fields required');
  return config;
}

function emit(output,value) {
  return new Promise((resolve,reject)=>{
    let settled=false;
    function finish(error) {
      if(settled)return;
      settled=true;output.removeListener('close',closed);
      if(error)reject(error);else resolve();
    }
    function closed() {
      const error=Error('primary output closed before write completion');
      error.code='PRIMARY_OUTPUT_CLOSED';finish(error);
    }
    // A Writable may close without an error and without completing a queued
    // write callback. Observe that boundary without replaying accepted work.
    output.once('close',closed);
    if(output.destroyed||output.closed||output.writableEnded){closed();return;}
    try {output.write(JSON.stringify(value)+'\n',finish);}
    catch(error){finish(error);}
  });
}

export async function servePrimaryLines(options) {
  return serveOwnedPrimaryLines(options);
}

async function serveOwnedPrimaryLines({exchange,input,output},observeFailure=()=>{}) {
  if(output.destroyed||output.closed||output.writableEnded) {
    const error=Error('primary output unavailable before line admission');
    error.code='PRIMARY_OUTPUT_CLOSED';observeFailure(error);input.pause();throw error;
  }
  const decoder=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true});
  let lines,pending=null,failure=null;
  const rejectedWrites=new Set();
  function failed(error) {failure??=error;observeFailure(failure);input.pause();lines?.close();}
  function outputClosed() {
    const error=Error('primary output closed while line transport active');
    error.code='PRIMARY_OUTPUT_CLOSED';failed(error);
  }
  function validateBytes(chunk) {
    if(failure)return;
    try {
      if(typeof chunk==='string')decoder.decode();
      else decoder.decode(chunk,{stream:true});
    } catch(error){failed(error);}
  }
  function finishBytes() {
    if(failure)return;
    try {decoder.decode();}catch(error){failed(error);}
  }
  input.on('data',validateBytes);input.on('end',finishBytes);
  lines=createInterface({input,terminal:false});
  lines.on('error',failed);
  output.on('error',failed);
  output.on('close',outputClosed);
  input.on('error',failed);
  async function perform(line) {
    let request;
    try {request=JSON.parse(line);}
    catch(error){
      await emit(output,{schema,status:'refused',operation_invoked:false,
        next_id:exchange.state().next_id,error:String(error)});return;
    }
    let result;
    try {result=await exchange.execute(request);}
    catch(error){
      await emit(output,{schema,status:'command_error',error:String(error),
        // Correlation only: next_id may be unchanged for envelope rejection or
        // advanced for a consumed command. Neither field authorizes replay.
        command_id:Number.isSafeInteger(request?.id)?request.id:null,
        command_method:typeof request?.method==='string'&&request.method.length<=64?request.method:null,
        replay_allowed:false,state:exchange.state()});return;
    }
    await emit(output,{schema,status:'returned',result});
  }
  return new Promise((resolve,reject)=>{
    lines.on('line',line=>{
      if(failure)return;
      if(output.destroyed||output.closed||output.writableEnded){outputClosed();return;}
      if(pending){
        // One unobserved busy write is enough. A synchronous line burst can
        // continue even after input.pause(), so stop before retaining another.
        if(rejectedWrites.size){failed(Error('primary busy response backlog'));return;}
        // Refuse this line now. It is never retained as a future action.
        const write=emit(output,{schema,status:'busy',operation_invoked:false,
          pending:true,next_id:exchange.state().next_id}).catch(failed);
        rejectedWrites.add(write);write.finally(()=>rejectedWrites.delete(write));return;
      }
      pending=perform(line).catch(failed).finally(()=>{pending=null;});
    });
    lines.once('close',()=>{
      (async()=>{
        // EOF or a broken output channel does not cancel a committed command.
        // Finish observing that same promise before owner transport cleanup.
        await pending;await Promise.all(rejectedWrites);
        output.removeListener('close',outputClosed);
        output.removeListener('error',failed);input.removeListener('error',failed);
        input.removeListener('data',validateBytes);input.removeListener('end',finishBytes);
        if(failure)reject(failure);else resolve();
      })().catch(reject);
    });
  });
}

export async function runPrimaryStdio(config,{input=process.stdin,output=process.stdout}={}) {
  validatePrimaryConfig(config);
  if(output.isTTY)throw TypeError('primary stdout must be a pipe or file; terminal rendering is not a JSON-lines transport');
  if(output.destroyed||output.closed||output.writableEnded) {
    const error=Error('primary output unavailable before host startup');
    error.code='PRIMARY_OUTPUT_CLOSED';input.pause();throw error;
  }
  let host,exchange,failure=null;
  function failed(error) {failure??=error;input.pause();}
  function outputClosed() {
    const error=Error('primary output closed while owner active');
    error.code='PRIMARY_OUTPUT_CLOSED';failed(error);
  }
  input.on('error',failed);output.on('error',failed);
  output.on('close',outputClosed);
  try {
    try {
      host=await createInstrumentedRelayClient(config.host);
      if(failure)throw failure;
      exchange=await createPrimaryExchange({host,route:config.route,directory:config.exchangeDirectory,
        expectations:config.expectations??[],options:config.primaryOptions??{}});
      if(failure)throw failure;
      await emit(output,{schema,status:'ready',state:exchange.state()});
      if(failure)throw failure;
      await serveOwnedPrimaryLines({exchange,input,output},failed);
    } catch(error){failure??=error;}
    // Observe the original host after any owned stream failure, including
    // ready/terminal writes outside the inner line transport's lifetime.
    let exit;
    if(host)try {exit=await host.close();}
    catch(error){
      if(failure)throw new AggregateError([failure,error],'primary stream and transport cleanup failed');
      throw error;
    }
    if(failure)throw failure;
    try {await emit(output,{schema,status:'terminal',exit,state:exchange.state()});}
    catch(error){failure??=error;}
    if(failure)throw failure;
  } finally {
    output.removeListener('close',outputClosed);
    output.removeListener('error',failed);input.removeListener('error',failed);
  }
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href) {
  try {
    if(process.argv.length!==4||process.argv[2]!=='--config')
      throw TypeError('Usage: node primary_stdio.mjs --config /absolute/config.json');
    await runPrimaryStdio(JSON.parse(await readFile(process.argv[3],'utf8')));
  } catch(error){console.error(String(error));process.exitCode=2;}
}
