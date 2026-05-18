import { webcrypto } from 'crypto';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dir = dirname(fileURLToPath(import.meta.url));
const data  = JSON.parse(readFileSync(join(__dir, 'tests', 'vectors.json'), 'utf8'));
const enc = new TextEncoder(), dec = new TextDecoder();
let passed = 0, failed = 0;

console.log(`.klickd test vectors (JS) — spec ${data.spec_version}`);

for (const v of data.vectors) {
  const env = v.envelope;
  const salt = Buffer.from(env.kdf_salt, 'base64');
  const iv   = Buffer.from(env.iv,        'base64');
  const raw  = Buffer.from(env.ciphertext,'base64');
  const aad  = enc.encode(JSON.stringify(
    Object.fromEntries(
      ['created_at','domain','encrypted','klickd_version'].map(k=>[k,env[k]])
    )
  ));
  const km = await webcrypto.subtle.importKey('raw',enc.encode(v.passphrase),{name:'PBKDF2'},false,['deriveKey']);
  const key = await webcrypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:600000,hash:'SHA-256'},km,{name:'AES-GCM',length:256},false,['decrypt']);
  try {
    const pt = await webcrypto.subtle.decrypt({name:'AES-GCM',iv,additionalData:aad,tagLength:128},key,raw);
    const payload = JSON.parse(dec.decode(pt));
    if (v.expected_behavior?.includes('KlickdAuthError')) {
      console.log(`  FAIL ${v.id}: expected error, got success`); failed++;
    } else {
      console.log(`  PASS ${v.id}: display_name=${JSON.stringify(payload.display_name)}`); passed++;
    }
  } catch {
    if (v.expected_behavior?.includes('KlickdAuthError')) {
      console.log(`  PASS ${v.id}: rejected as expected`); passed++;
    } else {
      console.log(`  FAIL ${v.id}: unexpected decrypt failure`); failed++;
    }
  }
}
console.log(`\n${passed}/${passed+failed} passed`);
process.exit(failed > 0 ? 1 : 0);
