import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createPrivateKey} from 'node:crypto';
import {connect,listen} from 'node:quic';

const deadline=setTimeout(() => {throw new Error('HTTP/3 round trip timed out');},45000);
const key=createPrivateKey(await readFile(new URL('../private-cert/key.pem',import.meta.url)));
const cert=await readFile(new URL('../private-cert/cert.pem',import.meta.url));
const sessions=new Set();
async function collect(stream) {
  const chunks=[];
  for await (const batch of stream) for (const chunk of batch) chunks.push(Buffer.from(chunk));
  return Buffer.concat(chunks);
}
const endpoint=await listen(session => {
  sessions.add(session);
  session.onstream=async stream => {
    const input=await collect(stream);
    assert.ok(['GET','POST'].includes(stream.headers[':method']));
    const body=stream.headers[':method']==='POST' ? input : Buffer.from('h3-中文-ok');
    stream.sendHeaders({':status':200,'content-type':'application/octet-stream'});
    stream.setBody(body);
  };
},{sni:{'*':{keys:[key],certs:[cert]}},onheaders:function(headers){
  assert.equal(headers[':authority'],'localhost');
}});
let client;
try {
  client=await connect(endpoint.address,{servername:'localhost',ca:[cert]});
  const opened=await client.opened;
  assert.equal(opened.protocol,'h3');
  for(const [method,body] of [['GET',undefined],['POST',Buffer.from('弹幕 H3 '.repeat(4096))]]) {
    const stream=await client.createBidirectionalStream({
      headers:{':method':method,':path':'/smoke',':scheme':'https',':authority':'localhost'},
      ...(body===undefined?{}:{body}),
      onheaders(headers){assert.equal(headers[':status'],200);}
    });
    assert.deepEqual(await collect(stream),body ?? Buffer.from('h3-中文-ok'));
    await stream.closed;
  }
  console.log('PRIVATE_APP_H3_OK');
} finally {
  if(client) await client.close();
  for(const session of sessions) await session.close();
  await endpoint.close();
  clearTimeout(deadline);
}
