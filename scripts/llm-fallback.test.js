const http = require('http');
const MODULE = require.resolve('../llm_providers');
/* Provider-chain regression test: stubs OpenAI, DeepSeek and Nemotron on one
   local server and asserts the fallback order, retry policy and model picks.
   No network, no keys, no deps.   Run: node scripts/llm-fallback.test.js */

// One stub that impersonates all three providers, keyed by path prefix.
const behaviour = {};   // name -> {status, body} | 'ok'
const seen = [];
const srv = http.createServer((req, res) => {
  const name = req.url.split('/')[1];
  let raw = '';
  req.on('data', d => raw += d);
  req.on('end', () => {
    const body = JSON.parse(raw);
    seen.push({ name, model: body.model, jsonMode: !!body.response_format });
    const b = behaviour[name];
    if (b === 'ok') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ choices: [{ message: { content: '```json\n{"ok":"' + name + '"}\n```' } }] }));
    }
    res.writeHead(b.status, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: { message: b.msg || 'boom' } }));
  });
});

const base = p => `http://127.0.0.1:${srv.address().port}/${p}`;
let fails = 0;
const check = (l, c, x) => { if (c) console.log('   ok   ' + l); else { fails++; console.log('   FAIL ' + l + (x ? ' — ' + x : '')); } };

srv.listen(0, async () => {
  process.env.OPENAI_BASE_URL = base('openai');
  process.env.DEEPSEEK_BASE_URL = base('deepseek');
  process.env.FALLBACK_BASE_URL = base('nemotron');
  process.env.OPENAI_API_KEY = 'k1';
  process.env.DEEPSEEK_API_KEY = 'k2';
  process.env.FALLBACK_API_KEY = 'k3';
  const { chatCompletion, parseJsonContent, availableProviders } = require(MODULE);

  const run = (fast = false) => chatCompletion({
    fast, body: { response_format: { type: 'json_object' }, messages: [] },
    parse: parseJsonContent, onFallback: () => {},
  });
  const reset = () => { seen.length = 0; };

  check('chain order', availableProviders().join(',') === 'openai,deepseek,nemotron', availableProviders().join(','));

  // 1. OpenAI healthy → no fallback
  behaviour.openai = 'ok'; behaviour.deepseek = 'ok'; behaviour.nemotron = 'ok';
  reset();
  let r = await run();
  check('healthy OpenAI answers', r.provider === 'openai' && r.value.ok === 'openai');
  check('no other provider touched', seen.length === 1, JSON.stringify(seen));

  // 2. OpenAI out of credits (429 insufficient_quota) → DeepSeek, no retries
  behaviour.openai = { status: 429, msg: 'You exceeded your current quota, insufficient_quota' };
  reset();
  r = await run();
  check('out of credits → deepseek', r.provider === 'deepseek', r.provider);
  check('no retry burnt on exhausted provider', seen.filter(s => s.name === 'openai').length === 1,
    JSON.stringify(seen.map(s => s.name)));
  check('deepseek default model', r.model === 'deepseek-v4-pro', r.model);

  // 3. fast:true picks the flash model
  reset();
  r = await run(true);
  check('fast mode uses deepseek-v4-flash', r.model === 'deepseek-v4-flash', r.model);

  // 4. DeepSeek down too → nemotron, and response_format is stripped for it
  behaviour.deepseek = { status: 402, msg: 'Payment required' };
  reset();
  r = await run();
  check('deepseek 402 → nemotron', r.provider === 'nemotron', r.provider);
  check('nemotron model id', r.model === 'nvidia/nemotron-3-ultra-550b-a55b:free', r.model);
  check('json mode stripped for nemotron',
    seen.find(s => s.name === 'nemotron').jsonMode === false);
  check('json mode kept for openai/deepseek',
    seen.filter(s => s.name !== 'nemotron').every(s => s.jsonMode === true));

  // 5. every provider down → throws, message names the last one
  behaviour.nemotron = { status: 500, msg: 'upstream' };
  let threw = null;
  try { await run(); } catch (e) { threw = e.message; }
  check('all providers down → throws', /nemotron/.test(threw || ''), threw);

  // 6. our own bad request (400) does not cascade
  behaviour.openai = { status: 400, msg: 'bad model' };
  reset();
  threw = null;
  try { await run(); } catch (e) { threw = e.message; }
  check('400 fails fast on openai', /openai API error 400/.test(threw || ''), threw);
  check('400 did not hit fallbacks', seen.length === 1, JSON.stringify(seen.map(s => s.name)));

  // 7. plain rate limit retries the same provider, then falls through
  behaviour.openai = { status: 429, msg: 'Rate limit reached' };
  behaviour.deepseek = 'ok'; behaviour.nemotron = 'ok';
  reset();
  r = await run();
  check('rate limit retries openai 3x then falls through',
    seen.filter(s => s.name === 'openai').length === 3, JSON.stringify(seen.map(s => s.name)));

  // 8. only a fallback key configured
  delete process.env.OPENAI_API_KEY;
  delete process.env.DEEPSEEK_API_KEY;
  behaviour.nemotron = 'ok';
  reset();
  r = await run();
  check('unkeyed providers skipped', r.provider === 'nemotron' && seen.length === 1,
    JSON.stringify(seen.map(s => s.name)));

  // 9. no keys at all
  delete process.env.FALLBACK_API_KEY;
  threw = null;
  try { await run(); } catch (e) { threw = e.code; }
  check('no keys → NO_API_KEY', threw === 'NO_API_KEY', String(threw));

  srv.close();
  console.log('\n' + (fails ? fails + ' FAILURES' : 'all checks passed'));
  process.exit(fails ? 1 : 0);
});
