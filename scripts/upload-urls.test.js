const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const ejs = require('ejs');
const { JSDOM, VirtualConsole } = require('jsdom');

test('upload and analysis requests work with hooks requiring absolute URLs', async () => {
  const slots = ['sales', 'sessions', 'checkins', 'leads', 'new', 'lapsed', 'active']
    .map(field => ({ field, label: field }));
  const html = await ejs.renderFile(path.join(__dirname, '../views/upload.ejs'), {
    slots, error: null, previousMonth: { label: 'September 2026' },
  });
  const requests = [];
  const dom = new JSDOM(html, {
    url: 'http://localhost:3000/#/', runScripts: 'dangerously',
    virtualConsole: new VirtualConsole(),
    beforeParse(window) {
      window.fetch = async (input) => {
        // Browser request hooks may parse fetch inputs without a base URL.
        const url = new URL(input);
        requests.push(url.pathname);
        return { ok: true, json: async () => url.pathname === '/api/saved-sessions'
          ? { sessions: [] } : { ok: true, redirectUrl: '#complete' } };
      };
    },
  });
  try {
    const document = dom.window.document;
    for (const input of document.querySelectorAll('.dropzone input[type=file]')) {
      Object.defineProperty(input, 'files', { value: [new dom.window.File(['a,b\n1,2'], 'data.csv')] });
    }
    document.getElementById('upload-form').dispatchEvent(new dom.window.Event('submit', { cancelable: true }));
    for (let i = 0; i < 50 && !requests.includes('/analyze-session'); i++) {
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    assert.equal(requests.filter(p => p === '/upload-chunk').length, 7);
    assert.ok(requests.includes('/analyze-session'));
    assert.ok(requests.includes('/api/saved-sessions'));
    assert.equal(document.body.textContent.includes("Error: Failed to construct 'URL'"), false);
  } finally { dom.window.close(); }
});
