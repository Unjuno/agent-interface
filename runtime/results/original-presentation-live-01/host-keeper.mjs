import {readFile,writeFile,rename} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const [caseArg,archiveArg,bundleArg,display,targetsArg]=process.argv.slice(2);
const caseDir=resolve(caseArg),archive=resolve(archiveArg),bundle=resolve(bundleArg);
const {createInstrumentedRelayClient}=await import(pathToFileURL(join(bundle,'relay_host.mjs')));
const {createPrimaryCaller}=await import(pathToFileURL(join(bundle,'primary_caller.mjs')));
const host=await createInstrumentedRelayClient({command:'/tmp/agent-interface-mcp-venv/bin/python',args:[archive,'relay','--','--targets',targetsArg,'--output-directory',join(caseDir,'calls'),'--display',display,'--session-mode','guarded-x11'],evidenceDirectory:join(caseDir,'host')});
let commandIndex=0,imagePath=null,textValues=[];
const sinks={text:async value=>{textValues.push(value);},image:async picture=>{
  if(imagePath)throw Error('unexpected second image');
  imagePath=join(caseDir,`primary-${String(commandIndex).padStart(3,'0')}.png`);
  await writeFile(imagePath,picture.bytes,{flag:'wx'});
}};
const caller=createPrimaryCaller(host,'guarded-local',sinks);
async function write(path,row){const temp=path+'.tmp';await writeFile(temp,JSON.stringify(row,null,2)+'\n',{flag:'wx'});await rename(temp,path);}
console.log('READY HOST');
try {
  for(commandIndex=1;commandIndex<20;commandIndex++){
    const name=String(commandIndex).padStart(3,'0')+'.json',path=join(caseDir,'commands',name);
    let request;
    for(;;){try{request=JSON.parse(await readFile(path,'utf8'));break;}catch(e){if(e.code!=='ENOENT')throw e;await new Promise(r=>setTimeout(r,20));}}
    const started=process.hrtime.bigint();imagePath=null;textValues=[];let reply;
    if(request.op==='observe')reply=await caller.observe();
    else if(request.op==='mint')reply=await caller.mint(request.alias,request.sequence,request.point,[24,24]);
    else if(request.op==='input')reply=request.feedback?await caller.inputWithFeedback(request.alias,request.offset,'click',[],request.feedback):await caller.input(request.alias,request.offset,'click',[]);
    else if(request.op==='present_original'){await caller.presentOriginal(request.attempt);reply={presentation_only:true,source_attempt:request.attempt};}
    else if(request.op==='review')reply=await caller.review(request.attempt,{task:'t1001073',phase:request.phase,reason:request.reason});
    else if(request.op==='results')reply=await caller.call('interface_results',{call_id:request.call_id,include_image:false,detail:'full'});
    else if(request.op==='ack')reply=await caller.acknowledgeText(request.attempt,{task:'t1001073',phase:request.phase,reason:request.reason});
    else if(request.op==='close')reply=await caller.call('interface_close',{});
    else throw Error('unknown primary command');
    const meta=reply.result?.content?.find(b=>b.type==='text')?.text;
    await write(join(caseDir,'replies',name),{request,started_ns:started.toString(),ended_ns:process.hrtime.bigint().toString(),attempt:reply.attempt??null,isError:reply.result?.isError??null,metadata:meta?JSON.parse(meta):reply,image_path:imagePath,caller_state:caller.state(),presented_text:textValues});
    console.log('REPLY '+commandIndex);
    if(request.op==='close')break;
  }
} catch(error){await write(join(caseDir,'host-exception.json'),{error:String(error),replay_allowed:false});throw error;}
finally {const exit=await host.close();await write(join(caseDir,'host-terminal.json'),{exit,caller_state:caller.state()});console.log('TERMINAL HOST');}
