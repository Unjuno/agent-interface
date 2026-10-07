/** Explicit sequential primary commands with original file presentation.
 * No action policy, queue, retry, implicit review, transport startup or cleanup.
 */
import {mkdir, writeFile} from 'node:fs/promises';
import {resolve, join} from 'node:path';
import {createHash} from 'node:crypto';
import {createPrimaryCaller} from './primary_caller.mjs';

const methods=new Set(['call','observe','mint','mintMany','input','inputWithFeedback',
  'reviewWindow','review','acknowledgeText','presentOriginal']);
const snapshot=value=>JSON.parse(JSON.stringify(value,(_key,item)=>{
  if(item===undefined||typeof item==='function'||typeof item==='symbol'||
    (typeof item==='number'&&!Number.isFinite(item)))throw TypeError('finite JSON required');
  return item;
}));

export async function createPrimaryExchange({host,directory,route,expectations=[],options={}}) {
  if(!['guarded-local','direct-post'].includes(route))throw TypeError('explicit supported route required');
  if(typeof directory!=='string'||!directory.trim())throw TypeError('fresh exchange directory required');
  const path=resolve(directory);
  // Caller-owned existing parent; never reuse an occupied directory.
  await mkdir(path);
  let nextId=1,busy=false,stopped=null,current=null;
  const sinks={
    text:async value=>{
      if(!current)throw Error('presentation outside command');
      current.presented_text.push(snapshot(value));
    },
    image:async ({bytes,mimeType})=>{
      if(!current)throw Error('presentation outside command');
      if(mimeType!=='image/png'||!Buffer.isBuffer(bytes)||!bytes.length)
        throw TypeError('original nonempty PNG bytes required');
      const copy=Buffer.from(bytes);
      const imagePath=join(path,`image-${current.id}-${current.images.length+1}.png`);
      await writeFile(imagePath,copy,{flag:'wx'});
      current.images.push({path:imagePath,mime_type:mimeType,bytes:copy.length,
        sha256:createHash('sha256').update(copy).digest('hex')});
    }
  };
  const primary=createPrimaryCaller(host,route,sinks,expectations,options);
  return {
    state:()=>({next_id:nextId,busy,stopped,caller_state:primary.state()}),
    async execute(command) {
      if(busy)throw Error('command outstanding; wait, do not queue or resend');
      const request=snapshot(command);
      if(!request||typeof request!=='object'||Array.isArray(request)||
        Object.keys(request).sort().join(',')!=='args,id,method'||
        !Number.isSafeInteger(request.id)||request.id!==nextId)
        throw TypeError(`next command id must be ${nextId}; exact id/method/args envelope required`);
      if(!methods.has(request.method)||!Array.isArray(request.args))throw TypeError('known method and positional args required');
      const closing=request.method==='call'&&request.args.length===2&&
        request.args[0]==='interface_close'&&request.args[1]&&
        typeof request.args[1]==='object'&&!Array.isArray(request.args[1])&&
        Object.keys(request.args[1]).length===0;
      if(stopped&&!closing)throw Error('exchange stopped: '+stopped);
      busy=true;nextId++;
      current={id:request.id,method:request.method,presented_text:[],images:[]};
      try {
        // Consume once before persistence/dispatch, even on ambiguous failure.
        await writeFile(join(path,`request-${request.id}.json`),JSON.stringify(request)+'\n',{flag:'wx'});
        const reply=await primary[request.method](...request.args);
        const originalReplyPath=join(path,`original-reply-${request.id}.json`);
        await writeFile(originalReplyPath,JSON.stringify(reply??null)+'\n',{flag:'wx'});
        const result={...current,attempt:reply?.attempt??null,
          original_reply_path:originalReplyPath,caller_state:primary.state(),next_id:nextId};
        await writeFile(join(path,`presentation-${request.id}.json`),JSON.stringify(result)+'\n',{flag:'wx'});
        return result;
      } catch(error) {
        stopped??=String(error)+'; inspect retained original files; never replay input';
        // Evidence errors are not repaired by a second action. The caller owns
        // transport lifetime and can explicitly attempt public close once.
        throw error;
      } finally {current=null;busy=false;}
    }
  };
}
