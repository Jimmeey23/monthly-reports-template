/* =============================================================================
   agent/loop.js — the conversation
   -----------------------------------------------------------------------------
   One turn is: send the thread to the provider chain, run whatever tools the
   model asks for, feed the results back, repeat until it answers in prose or
   hits the step ceiling. Every step is pushed to the dock as it happens, so the
   user watches the query run rather than a spinner.

   Threads are held in memory per report and trimmed, because the interesting
   context (the data, the report structure) is re-derived each turn by
   agent/context.js rather than carried in the history.
   ========================================================================== */
'use strict';

const { chatCompletion, hasAnyProvider } = require('../llm_providers');
const context = require('./context');
const tools = require('./tools');

const MAX_STEPS = Number(process.env.AGENT_MAX_STEPS) || 12;
const MAX_TOOL_RESULT_CHARS = 20000;
const MAX_HISTORY_MESSAGES = 40;

const threads = new Map();   // `${sessionId}|${filename}` -> messages[]

function threadKey(sessionId, filename) {
  return `${sessionId}|${filename}`;
}

function getThread(sessionId, filename) {
  const key = threadKey(sessionId, filename);
  if (!threads.has(key)) threads.set(key, []);
  return threads.get(key);
}

function resetThread(sessionId, filename) {
  threads.delete(threadKey(sessionId, filename));
}

/* The system prompt is rebuilt every turn from the live session, so a report
   the agent just changed is described as it is now, not as it was at boot. */
function systemPrompt(ctx) {
  const outline = context.renderOutline(context.reportOutline(ctx.reportPath));
  const schema = context.dataSchema(ctx.analysisPath) || '(analysis.json unavailable)';
  const csvs = context.csvSchema(ctx.csvDir);

  return `You are the analyst embedded in a Physique 57 studio performance report. You are looking at
the same page the user is: ${ctx.locName || ctx.locKey || 'this studio'}, ${ctx.monthLabel || ctx.monthKey || 'the reported month'}.

You do three things:
1. Answer questions about the studio's performance — accurately, with reasoning, from the real data.
2. Build new tables, charts, lists and cards into the report, WHEN ASKED TO.
3. Change the report's styling, layout and positioning, WHEN ASKED TO.

A question is a question. "What drove revenue?" wants an explanation, not a new section in the
report. Only call propose_component or propose_style_patch when the user actually asked for
something to be added to or changed in the report ("add", "build", "put a table in", "make it
wider", "move that"). If a component would genuinely help an answer, offer it in one line and wait
for a yes.

HOW TO BE ACCURATE
- Every number you state must come from a run_query result in this conversation. Never do arithmetic
  in your head, never recall a figure from the report text, never estimate. If you have not queried
  it, query it.
- Prefer one query that returns everything you need over several round trips.
- When a question is comparative ("is that good?"), query the comparison period too — the data holds
  several months, including the same month last year, so trend and YoY are always available.
- Reason about what the numbers mean, and say it in prose: name the driver, and query it rather than
  asserting it. If revenue moved, decompose it — transaction count against average value, category
  mix, discounting — and say which explains most of the move. A bare figure is a weak answer; a
  figure with its driver quantified is a good one.
- Answer the question that was asked, fully, before offering anything else.
- If the data cannot answer something, say so plainly and say what would be needed. Never invent.
- Short answers for short questions. Markdown tables for comparisons. Currency as ₹ with Indian
  formatting (₹17.99L style) to match the report.

BUILDING COMPONENTS
- Query the numbers first, then call propose_component with them written into the HTML literally.
- You MUST call inspect_html on a comparable block already in the target section before proposing,
  and reuse the classes you find there. Never invent a class name — an invented class has no styling
  in this report and the component will look broken. A table, for instance, copies the wrapper,
  table, thead and cell classes of an existing report table.
- Call report_outline first if you are unsure where the component belongs.
- The component renders instantly for review but is NOT saved. Tell the user it is a preview and ask
  them to confirm the section and placement; the dock gives them Keep and Discard buttons.

STYLING AND LAYOUT
- Use propose_style_patch with precise selectors from report_outline / inspect_html.
- Group related ops into one patch. Never restyle broadly when a scoped selector will do.
- These also apply live and stay pending until kept, and every kept change is revertible by id.

THE DATA — analysis.json, available in run_query as \`analysis\`:
${schema}

UPLOADED CSVs — available as csv("<name>"), row dicts:
${csvs}

THIS REPORT'S STRUCTURE:
${outline}

Current studio key: ${ctx.locKey || '(unknown)'} · month key: ${ctx.monthKey || '(unknown)'}
${ctx.canEdit ? '' : 'This viewer is READ-ONLY: answer questions, but say editing is disabled if asked to change the report.'}`;
}

function toolResultText(result) {
  let text;
  try { text = JSON.stringify(result); } catch (e) { text = String(result); }
  if (text.length > MAX_TOOL_RESULT_CHARS) {
    text = `${text.slice(0, MAX_TOOL_RESULT_CHARS)}… [truncated — return less data]`;
  }
  return text;
}

function trim(messages) {
  if (messages.length <= MAX_HISTORY_MESSAGES) return messages;
  /* Drop from the front, but never cut a tool result loose from the assistant
     message that requested it — providers reject an orphaned tool message. */
  let cut = messages.length - MAX_HISTORY_MESSAGES;
  while (cut < messages.length && messages[cut].role === 'tool') cut += 1;
  messages.splice(0, cut);
  return messages;
}

/**
 * Run one user turn to completion.
 *
 * @param {object}   opts
 * @param {string}   opts.message  what the user typed
 * @param {object}   opts.ctx      { sessionId, filename, sessionDir, analysisPath, csvDir,
 *                                   reportPath, locKey, monthKey, locName, monthLabel, canEdit }
 * @param {function} opts.emit     (event) => void — 'status' | 'tool' | 'tool_result' |
 *                                   'proposal' | 'message' | 'error' | 'done'
 */
async function runTurn({ message, ctx, emit = () => {} } = {}) {
  if (!hasAnyProvider()) {
    const err = new Error('No LLM provider is configured. Set OPENAI_API_KEY or DEEPSEEK_API_KEY.');
    err.code = 'NO_API_KEY';
    throw err;
  }

  const history = getThread(ctx.sessionId, ctx.filename);
  history.push({ role: 'user', content: message });

  const proposals = [];
  let answer = '';

  for (let step = 0; step < MAX_STEPS; step += 1) {
    const body = {
      messages: [{ role: 'system', content: systemPrompt(ctx) }, ...trim(history)],
      tools: tools.definitions,
      tool_choice: 'auto',
      temperature: 0.15,
    };

    emit({ type: 'status', text: step === 0 ? 'Thinking…' : 'Working…' });

    const { value: assistant } = await chatCompletion({
      body,
      wantMessage: true,
      parse: m => m,
      onFallback: info => emit({ type: 'status', text: `${info.from} unavailable — trying ${info.to}` }),
    });

    const calls = assistant.tool_calls || [];
    history.push({
      role: 'assistant',
      content: assistant.content || '',
      ...(calls.length ? { tool_calls: calls } : {}),
    });

    if (!calls.length) {
      answer = assistant.content || '';
      break;
    }

    for (const call of calls) {
      const name = call.function && call.function.name;
      let args = {};
      try {
        args = JSON.parse((call.function && call.function.arguments) || '{}');
      } catch (e) {
        history.push({
          role: 'tool', tool_call_id: call.id, name,
          content: JSON.stringify({ ok: false, error: `arguments were not valid JSON: ${e.message}` }),
        });
        continue;
      }

      emit({ type: 'tool', name, args });

      let result;
      try {
        result = await tools.runTool(name, args, ctx);
      } catch (e) {
        result = { ok: false, error: e.message };
      }

      if (result && result.proposal) {
        const proposal = Object.assign({ proposalId: call.id }, result.proposal);
        proposals.push(proposal);
        emit({ type: 'proposal', proposal });
        // The dock needs the payload; the model only needs to know it landed.
        result = { ok: true, pending: true, message: result.message, proposalId: call.id };
      }

      emit({ type: 'tool_result', name, result });
      history.push({
        role: 'tool', tool_call_id: call.id, name, content: toolResultText(result),
      });
    }
  }

  if (!answer) answer = 'I ran out of steps on that one. Ask me again, more narrowly.';
  emit({ type: 'message', text: answer });
  emit({ type: 'done', proposals });
  return { answer, proposals };
}

module.exports = { runTurn, resetThread, getThread, systemPrompt, MAX_STEPS };
