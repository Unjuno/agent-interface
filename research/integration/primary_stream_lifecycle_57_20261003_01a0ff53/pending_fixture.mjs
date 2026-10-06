import {createInterface} from 'node:readline';
import {appendFileSync,existsSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
const directory=process.argv[2];
const log=value=>appendFileSync(join(directory,'fixture.events.jsonl'),JSON.stringify(value)+'\n');
let requests=0,pending=false;
writeFileSync(join(directory,'fixture.started.json'),JSON.stringify({pid:process.pid,ppid:process.ppid})+'\n',{flag:'wx'});
const reader=createInterface({input:process.stdin});
reader.on('line',line=>{
  requests++;if(requests!==1)throw Error('fixture received a replay');
  const request=JSON.parse(line);pending=true;
  writeFileSync(join(directory,'fixture.request.json'),JSON.stringify(request)+'\n',{flag:'wx'});
  log({kind:'request_received',request});
  const wait=()=>{
    if(!existsSync(join(directory,'release'))){setTimeout(wait,5);return;}
    const reply={id:request.id,tool:request.tool,next_id:request.id+1,status:'returned',result:{isError:false,content:[{type:'text',text:'{"status":"clock","fixture":"original once"}'}]}};
    const bytes=JSON.stringify(reply)+'\n';
    writeFileSync(join(directory,'fixture.reply.jsonl'),bytes,{flag:'wx'});
    process.stdout.write(bytes);pending=false;log({kind:'reply_written'});
  };wait();
});
reader.on('close',()=>log({kind:'stdin_end',pending,requests}));
process.on('exit',code=>writeFileSync(join(directory,'fixture.exit.json'),JSON.stringify({pid:process.pid,code,requests,pending})+'\n',{flag:'wx'}));
