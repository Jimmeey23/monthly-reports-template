/* =============================================================================
   llm_providers.js — one chat-completions call, three providers behind it
   -----------------------------------------------------------------------------
   OpenAI is tried first. When it is out of credits (or its key is missing,
   revoked, or the API is down) the same request is replayed against DeepSeek,
   and if that fails too, against the Nemotron free endpoint.

   Every provider speaks the OpenAI /chat/completions wire format, so the
   request body is built once by the caller and reused verbatim — only the
   `model` field and the endpoint change per provider.

   Configure with env vars (defaults in brackets):

     OPENAI_API_KEY          OPENAI_BASE_URL   [https://api.openai.com/v1]
     OPENAI_MODEL            [gpt-4o]          OPENAI_FAST_MODEL [gpt-4o-mini]

     DEEPSEEK_API_KEY        DEEPSEEK_BASE_URL [https://api.deepseek.com]
     DEEPSEEK_MODEL          [deepseek-v4-pro]
     DEEPSEEK_FAST_MODEL     [deepseek-v4-flash]

     FALLBACK_API_KEY (or OPENROUTER_API_KEY)
     FALLBACK_BASE_URL       [https://openrouter.ai/api/v1]
     FALLBACK_MODEL          [nvidia/nemotron-3-ultra-550b-a55b:free]

   A provider with no key is skipped rather than failing the chain, so adding
   a DeepSeek key is the only step needed to arm the fallback.
   ========================================================================== */
'use strict';

const MAX_RETRY_DELAY_MS = 10000;

function provider(spec) {
  return Object.assign({ jsonMode: true, retries: 3 }, spec);
}

/* Order is the fallback order. */
function providers() {
  const env = process.env;
  return [
    provider({
      name: 'openai',
      baseUrl: (env.OPENAI_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, ''),
      apiKey: env.OPENAI_API_KEY,
      model: env.OPENAI_MODEL || 'gpt-4o',
      fastModel: env.OPENAI_FAST_MODEL || 'gpt-4o-mini',
    }),
    provider({
      name: 'deepseek',
      baseUrl: (env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com').replace(/\/$/, ''),
      apiKey: env.DEEPSEEK_API_KEY,
      model: env.DEEPSEEK_MODEL || 'deepseek-v4-pro',
      fastModel: env.DEEPSEEK_FAST_MODEL || 'deepseek-v4-flash',
    }),
    provider({
      name: 'nemotron',
      baseUrl: (env.FALLBACK_BASE_URL || 'https://openrouter.ai/api/v1').replace(/\/$/, ''),
      apiKey: env.FALLBACK_API_KEY || env.OPENROUTER_API_KEY,
      model: env.FALLBACK_MODEL || 'nvidia/nemotron-3-ultra-550b-a55b:free',
      // The free endpoint does not reliably honour response_format, so the
      // caller's fence-stripping JSON parse is what keeps the output usable.
      jsonMode: false,
      retries: 2,
    }),
  ];
}

function configuredProviders() {
  return providers().filter(p => p.apiKey);
}

/** Names of the providers that can actually be called, in fallback order. */
function availableProviders() {
  return configuredProviders().map(p => p.name);
}

/** True when at least one provider has a key — the old `!!OPENAI_API_KEY` check. */
function hasAnyProvider() {
  return configuredProviders().length > 0;
}

/* A failure of the provider itself (out of credits, bad key, outage) — replay
   the request on the next provider. A 400/404/422 is our own bad request and
   would fail identically everywhere, so it is not retried elsewhere. */
function isProviderFailure(status) {
  if (status === 401 || status === 402 || status === 403 || status === 429) return true;
  return status >= 500;
}

/* Rate limits are worth waiting out on the same provider; being out of credits
   is not — the body says which one it is. */
function isExhausted(status, bodyText) {
  if (status === 402) return true;
  return /insufficient[_ ]quota|exceeded your current quota|billing|credit|payment required|no credits/i
    .test(String(bodyText || ''));
}

function retryDelayMs(res, attempt) {
  const retryAfter = Number(res.headers.get('retry-after'));
  const ms = Number.isFinite(retryAfter) && retryAfter > 0
    ? Math.ceil(retryAfter * 1000)
    : 1000 * Math.pow(3, attempt);
  return Math.min(ms, MAX_RETRY_DELAY_MS);
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Run one chat completion against the provider chain.
 *
 * @param {object}   opts
 * @param {object}   opts.body       OpenAI-shaped request body, minus `model`.
 * @param {boolean}  opts.fast       Use each provider's cheaper model.
 * @param {function} opts.parse      (content, json) => value. Throw to reject
 *                                   the answer and retry / fall through.
 * @param {function} opts.onFallback ({from, to, reason}) => void, for logging.
 * @returns {Promise<{value:*, provider:string, model:string}>}
 */
async function chatCompletion({ body, fast = false, parse, onFallback } = {}) {
  const chain = configuredProviders();
  if (!chain.length) {
    const err = new Error(
      'No LLM provider is configured. Set OPENAI_API_KEY, DEEPSEEK_API_KEY or '
      + 'FALLBACK_API_KEY in your .env file or environment.');
    err.code = 'NO_API_KEY';
    throw err;
  }

  let lastError;
  for (let i = 0; i < chain.length; i += 1) {
    const p = chain[i];
    const model = (fast && p.fastModel) || p.model;
    const payload = Object.assign({}, body, { model });
    if (!p.jsonMode) delete payload.response_format;
    const requestBody = JSON.stringify(payload);

    let fellThrough = null;
    for (let attempt = 0; attempt < p.retries; attempt += 1) {
      let res;
      try {
        res = await fetch(`${p.baseUrl}/chat/completions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${p.apiKey}`,
          },
          body: requestBody,
        });
      } catch (netErr) {
        // Unreachable host: no point retrying the same one hard.
        lastError = new Error(`${p.name} request failed: ${netErr.message}`);
        fellThrough = netErr.message;
        break;
      }

      if (!res.ok) {
        const errText = await res.text().catch(() => res.statusText);
        lastError = new Error(`${p.name} API error ${res.status}: ${errText}`);
        if (!isProviderFailure(res.status)) throw lastError;   // our bug, not theirs
        const outOfCredits = isExhausted(res.status, errText);
        const lastAttempt = attempt === p.retries - 1;
        if (outOfCredits || res.status === 401 || res.status === 403 || lastAttempt) {
          fellThrough = `${res.status}${outOfCredits ? ' (out of credits)' : ''}`;
          break;
        }
        await sleep(retryDelayMs(res, attempt));
        continue;
      }

      const json = await res.json().catch(() => null);
      const content = json && json.choices && json.choices[0]
        && json.choices[0].message && json.choices[0].message.content;
      if (!content) {
        lastError = new Error(`${p.name} returned no content`);
      } else {
        try {
          return { value: parse ? parse(content, json) : content, provider: p.name, model };
        } catch (parseErr) {
          lastError = new Error(`${p.name} returned unusable output: ${parseErr.message}`);
        }
      }
      if (attempt < p.retries - 1) await sleep(750 * (attempt + 1));
      else fellThrough = 'unusable output';
    }

    const next = chain[i + 1];
    if (next && onFallback) {
      onFallback({ from: p.name, to: next.name, reason: fellThrough || 'failed' });
    }
  }

  throw lastError || new Error('every LLM provider failed');
}

/** Strip ``` fences and parse — every provider gets the same treatment. */
function parseJsonContent(content) {
  const cleaned = String(content).trim()
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/\s*```$/, '');
  return JSON.parse(cleaned);
}

module.exports = {
  chatCompletion,
  parseJsonContent,
  availableProviders,
  hasAnyProvider,
};
