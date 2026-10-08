/** Sequential line transport for the existing primary exchange. No action queue. */
import {createInterface} from 'node:readline';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
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
    try {output.write(JSON.stringify(value)+'\n',error=>error?reject(error):resolve());}
    catch(error){reject(error);}
  });
}

export async function servePrimaryLines({exchange,input,output}) {
  const lines=createInterface({input,terminal:false});
  let pending=null,failure=null;
  const rejectedWrites=new Set();
  function failed(error) {failure??=error;input.pause();lines.close();}
  lines.on('error',failed);
  output.on('error',failed);
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
        output.removeListener('error',failed);input.removeListener('error',failed);
        if(failure)reject(failure);else resolve();
      })().catch(reject);
    });
  });
}

export async function runPrimaryStdio(config,{input=process.stdin,output=process.stdout}={}) {
  validatePrimaryConfig(config);
  if(output.isTTY)throw TypeError('primary stdout must be a pipe or file; terminal rendering is not a JSON-lines transport');
  let host,exchange,failure=null;
  function failed(error) {failure??=error;input.pause();}
  input.on('error',failed);output.on('error',failed);
  try {
    try {
      host=await createInstrumentedRelayClient(config.host);
      if(failure)throw failure;
      exchange=await createPrimaryExchange({host,route:config.route,directory:config.exchangeDirectory,
        expectations:config.expectations??[],options:config.primaryOptions??{}});
      await emit(output,{schema,status:'ready',state:exchange.state()});
      if(failure)throw failure;
      await servePrimaryLines({exchange,input,output});
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
    await emit(output,{schema,status:'terminal',exit,state:exchange.state()});
    if(failure)throw failure;
  } finally {
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
