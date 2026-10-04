import {writeFileSync} from 'node:fs';
import {join} from 'node:path';
const dir=process.argv[2];
writeFileSync(join(dir,'fixture-start.json'),JSON.stringify({pid:process.pid})+'\n',{flag:'wx'});
process.stdin.resume();
process.on('exit',code=>writeFileSync(join(dir,'fixture-exit.json'),JSON.stringify({pid:process.pid,code})+'\n',{flag:'wx'}));
