'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const https = require('node:https');
const http2 = require('node:http2');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const { once } = require('node:events');
const { Worker } = require('node:worker_threads');
const { spawn } = require('node:child_process');
const { AsyncLocalStorage } = require('node:async_hooks');

const deadline = setTimeout(() => { throw new Error('App runtime smoke timed out'); }, 60000);
async function main() {
  assert.equal(process.versions.node, '24.22.0');
  assert.equal(process.config.variables.node_use_quic, true, 'QUIC must be compiled');
  assert.ok(process.versions.ngtcp2 && process.versions.nghttp3);
  assert.equal(typeof require('node:quic').connect, 'function', 'QUIC enabled by default');
  assert.equal(process.config.variables.v8_enable_webassembly, 1);
  assert.equal(process.config.variables.node_use_openssl, true);
  assert.equal(process.config.variables.node_use_sqlite, false);
  assert.equal(process.config.variables.node_use_amaro, false);
  assert.equal(process.config.variables.v8_enable_inspector, 0);
  require('../smoke/mobile-features.js');
  require('./runtime-polyfills.js');
  const normalMap = new Map();
  assert.equal(normalMap.getOrInsert('a', 1), 1);
  const wasm = new WebAssembly.Module(Uint8Array.from([0,97,115,109,1,0,0,0]));
  assert.ok(new WebAssembly.Instance(wasm));
  for (const name of ['http2', 'dns', 'net', 'tls', 'crypto', 'stream', 'stream/web',
    'fs', 'module', 'vm', 'perf_hooks', 'diagnostics_channel', 'async_hooks', 'wasi']) {
    assert.ok(require('node:' + name), name);
  }
  const payload = Buffer.from('弹幕压缩与编码检查 '.repeat(64));
  for (const [compress, decompress] of [['gzipSync','gunzipSync'],
    ['deflateSync','inflateSync'], ['brotliCompressSync','brotliDecompressSync'],
    ['zstdCompressSync','zstdDecompressSync']]) {
    assert.deepEqual(zlib[decompress](zlib[compress](payload)), payload);
  }
  const encrypted = crypto.createCipheriv('aes-256-gcm', crypto.randomBytes(32), crypto.randomBytes(12));
  assert.ok(encrypted.update(payload).length);
  encrypted.final();
  const store = new AsyncLocalStorage();
  await store.run({value:42}, async () => {
    await Promise.resolve();
    assert.equal(store.getStore().value, 42);
  });
  const worker = new Worker("require('node:worker_threads').parentPort.postMessage('worker-ok')", {eval:true});
  assert.equal((await once(worker, 'message'))[0], 'worker-ok');
  await worker.terminate();
  // The App uses spawn for its outbound helper. Test Android's shell, not a child Node.
  const child = spawn('/system/bin/sh', ['-c', 'printf child-ok']);
  let childOutput = '';
  child.stdout.on('data', chunk => { childOutput += chunk; });
  assert.equal((await once(child, 'close'))[0], 0);
  assert.equal(childOutput, 'child-ok');
  const folder = await fs.mkdtemp(path.join(os.tmpdir(), 'app-runtime-'));
  try {
    await fs.writeFile(path.join(folder,'probe.cjs'), 'module.exports=42;');
    assert.equal(require(path.join(folder,'probe.cjs')), 42);
    await fs.writeFile(path.join(folder,'probe.mjs'), 'export default 43;');
    assert.equal((await import(require('node:url').pathToFileURL(path.join(folder,'probe.mjs')).href)).default, 43);
  } finally {
    await fs.rm(folder,{recursive:true,force:true});
  }
  const servers = [];
  async function serve(server) {
    servers.push(server);
    server.listen(0,'127.0.0.1');
    await once(server,'listening');
    return server.address().port;
  }
  try {
    const port = await serve(http.createServer((req,res) => res.end('http-ok')));
    assert.equal(await (await fetch(`http://127.0.0.1:${port}/`)).text(),'http-ok');
    const {default: nodeFetch} = await import('node-fetch');
    assert.equal(await (await nodeFetch(`http://127.0.0.1:${port}/`)).text(),'http-ok');
    const key = await fs.readFile(path.join(__dirname,'../private-cert/key.pem'));
    const cert = await fs.readFile(path.join(__dirname,'../private-cert/cert.pem'));
    const tlsPort = await serve(https.createServer({key,cert},(req,res) => res.end('tls-ok')));
    const data = await new Promise((resolve,reject) => {
      https.get({host:'127.0.0.1',port:tlsPort,servername:'localhost',ca:cert},res => {
        let body='';res.on('data',chunk => {body+=chunk;});res.on('end',() => resolve(body));
      }).on('error',reject);
    });
    assert.equal(data,'tls-ok');
    const h2 = http2.createServer();
    h2.on('stream',stream => {stream.respond({':status':200});stream.end('h2-ok');});
    const h2Port = await serve(h2);
    const session=http2.connect(`http://127.0.0.1:${h2Port}`);
    try {
      const req=session.request({':path':'/'});
      let text='';req.on('data',chunk => {text+=chunk;});req.end();
      await once(req,'end');assert.equal(text,'h2-ok');
    } finally { session.close(); }
  } finally {
    for (const server of servers) {
      server.closeAllConnections?.();
      await new Promise(resolve => server.close(resolve));
    }
  }
  const {default:pako} = await import('pako');
  assert.deepEqual(Buffer.from(pako.inflate(pako.deflate(payload))),payload);
  const {default:brotli} = await import('brotli');
  assert.deepEqual(Buffer.from(brotli.decompress(brotli.compress(payload))),payload);
  const adapters=await import('@dan-uni/dan-any/adapters');
  const core=await import('@dan-uni/dan-any/core/main/pure');
  assert.equal(typeof core.UniDB,'function');
  const db=new core.UniDB().init();
  const chunk=db.makeChunk({});
  chunk.upsertDanmakus([{SOID:'smoke',progress:1000,mode:'Normal',fontsize:25,color:0xffffff,
    senderID:'s',content:'弹幕',ctime:new Date(0),weight:1,pool:'Def',attr:[],platform:'smoke',extra:null}],true);
  assert.equal(chunk.$count,1);
  assert.equal(typeof adapters.BiliCommonParser,'function');
  const {ConverterFactory}=await import('opencc-js/core');
  const {default:toCN}=await import('opencc-js/to/cn');
  assert.equal(ConverterFactory(toCN)('漢語'),'汉语');
  const {HttpsProxyAgent}=await import('https-proxy-agent');
  assert.ok(new HttpsProxyAgent('http://127.0.0.1:8080'));
  console.log('PRIVATE_APP_RUNTIME_OK');
}
main().then(() => clearTimeout(deadline), error => {clearTimeout(deadline);console.error(error);process.exitCode=1;});
