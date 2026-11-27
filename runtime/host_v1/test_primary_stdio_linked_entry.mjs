import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,copyFile,symlink,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';

test('linked parent directory starts CLI and importing through link has no CLI side effect',async()=>{
 const root=await mkdtemp(join(tmpdir(),'primary-entry-link-'));const real=join(root,'real');const alias=join(root,'alias');
 try {
  await mkdir(real);
  for(const name of ['primary_stdio.mjs','primary_exchange.mjs','primary_caller.mjs','relay_host.mjs','relay_client.mjs','json_unique.mjs']) await copyFile(fileURLToPath(new URL('./'+name,import.meta.url)),join(real,name));
  await symlink(real,alias,process.platform==='win32'?'junction':'dir');
  const target=join(alias,'primary_stdio.mjs');
  for(const flags of [[],['--preserve-symlinks-main']]){
   const cli=spawnSync(process.execPath,[...flags,target],{encoding:'utf8',timeout:10000});
   assert.equal(cli.status,2,cli.stderr);assert.match(cli.stderr,/Usage: node primary_stdio\.mjs --config/);assert.equal(cli.stdout,'');
  }
  const imported=spawnSync(process.execPath,['--input-type=module','-e',`await import(${JSON.stringify(pathToFileURL(target).href)})`],{encoding:'utf8',timeout:10000});
  assert.equal(imported.status,0,imported.stderr);assert.equal(imported.stdout,'');assert.equal(imported.stderr,'');
 } finally {await rm(root,{recursive:true,force:true});}
});
