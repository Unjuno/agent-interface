import {appendFileSync, writeFileSync} from 'node:fs';
import {join} from 'node:path';

const directory=process.argv[2];
const event=value=>appendFileSync(join(directory,'fixture.events.jsonl'),JSON.stringify(value)+'\n');
writeFileSync(join(directory,'fixture.started.json'),JSON.stringify({pid:process.pid,ppid:process.ppid})+'\n',{flag:'wx'});
let bytes=0;
process.stdin.on('data',chunk=>{bytes+=chunk.length;event({kind:'unexpected_request',hex:chunk.toString('hex')});});
process.stdin.on('end',()=>event({kind:'stdin_end',bytes}));
process.on('exit',code=>{
  writeFileSync(join(directory,'fixture.exit.json'),JSON.stringify({pid:process.pid,code,bytes})+'\n',{flag:'wx'});
});
process.stdin.resume();
