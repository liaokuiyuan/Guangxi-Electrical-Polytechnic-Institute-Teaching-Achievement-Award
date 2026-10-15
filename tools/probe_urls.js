// 在真实浏览器里逐个打开候选地址，记录 HTTP 状态，用于挑选可用的替换链接。
// 用法：node _dsh_probe_urls.js <url1> <url2> ...
const { spawn } = require('child_process');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9354;
const URLS = process.argv.slice(2);

const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu',
  '--remote-debugging-port=' + PORT,
  '--window-size=1200,800',
  '--user-data-dir=' + process.env.TEMP + '\\cdp-urls-' + Date.now(),
  'about:blank',
], { stdio: 'ignore' });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function getTarget() {
  for (let i = 0; i < 40; i++) {
    try {
      const res = await fetch('http://127.0.0.1:' + PORT + '/json/list');
      const list = await res.json();
      const page = list.find((t) => t.type === 'page');
      if (page && page.webSocketDebuggerUrl) return page;
    } catch (e) { /* 等端口 */ }
    await sleep(300);
  }
  throw new Error('CDP 端口未就绪');
}

async function main() {
  const target = await getTarget();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  let lastStatus = 0;
  ws.addEventListener('message', (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.method === 'Network.responseReceived' && msg.params.type === 'Document') {
      lastStatus = msg.params.response.status;
    }
    if (msg.method === 'Network.loadingFailed' && msg.params.type === 'Document') {
      lastStatus = 'fail:' + msg.params.errorText;
    }
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  });
  const send = (method, params) => new Promise((resolve) => {
    const mid = ++id;
    pending.set(mid, resolve);
    ws.send(JSON.stringify({ id: mid, method, params: params || {} }));
  });
  await new Promise((r) => ws.addEventListener('open', r));
  await send('Page.enable');
  await send('Network.enable');

  for (const url of URLS) {
    lastStatus = 0;
    try {
      await send('Page.navigate', { url });
    } catch (e) { /* 忽略导航异常 */ }
    await sleep(6000);
    console.log('%s  %s', String(lastStatus).padEnd(22), url);
  }
  ws.close();
  chrome.kill();
}

main().catch((e) => { console.error('出错:', e.message); try { chrome.kill(); } catch (err) {} process.exit(1); });
