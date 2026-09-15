# Studio Pulse — monthly performance reports

Upload a month of studio CSVs, get a single self-contained HTML report per
studio and month. Every report — past or future — is built from one master
template, so they share a structure, a stylesheet and a set of behaviours.

## Running it

```bash
npm install
npm start          # http://localhost:3000
npm test           # jsdom suite over the generated reports
```

Set at least one LLM key in `.env` (see `.env.example`) if you want the written
narratives. Without a key the reports still generate; the narrative slots are
simply empty.

## How a report is built

```
CSV uploads  →  analyze_v2.py   →  analysis.json
                                      │
                openai_insights.js ───┤  (optional narratives, cached)
                                      ↓
                gen_report_v2.py  +  sections_v2.py  +  charts_v2.py
                                      ↓
                            report_shell.py          ← the master template
                                      ↓
                          one self-contained .html
```

**`report_shell.py` is the master template.** It owns the document: the
stylesheet, the chrome, the hero, the footer and every client script. Both the
single-report and the multi-studio bundle paths go through it, so the two cannot
drift apart. Section bodies come from `sections_v2.py`, which renders into that
shell.

Reports are fully self-contained — CSS, scripts, fonts and images are all
inlined, so a downloaded file works with no server behind it. The only runtime
fetch is the optional narration audio the app serves from `/audio/`.

### Template assets

`report_assets/` holds everything the shell inlines:

| path | what it is |
|---|---|
| `report.css` | the report stylesheet, single source of truth |
| `js/` | theme, scroll chrome, KPI charts, heatmap, card flip, carousel, PDF export, MoM panel, section audio, soundboard |
| `vendor/` | html2canvas and jsPDF, for in-browser PDF export |
| `img/` | logo and hero photography |
| `reference/` | the two hand-built July 2026 reports the template was derived from, kept as the visual spec |

## Generated reports

`GET /reports` lists every report the app has produced in one table, with links
to open it, download the HTML, or export a PDF. The index lives in
`uploads/reports_index.json`; rows whose file has gone are dropped on read.

## Retention

Only the **3 most recent upload sessions** are kept (`MAX_SESSIONS`). Older
session directories are deleted from disk, not just hidden — uploads are raw
client data and each session runs to megabytes. A report disappears from the
reports table once its session is pruned.

## LLM cost

Narratives are the only per-report spend, and three things keep it down:

- **One call per rendered section.** The section list comes from
  `AI_SECTIONS` in `openai_insights.js`, which is derived from the same labels
  the report renders.
- **The cheap model on each provider** by default. Set `INSIGHTS_FULL_MODEL=1`
  to opt back into the expensive one.
- **A prompt-keyed cache** in `uploads/.insights-cache/`, outside the session
  directories so it survives pruning. Re-running a report whose figures have not
  moved costs nothing.

Providers are tried in order — OpenAI, DeepSeek, then the free fallback — by
`llm_providers.js`, so a missing key or an exhausted quota degrades instead of
failing.

## The in-report assistant

Every report served from `/report/:sessionId/:file` gets a chat dock in the
corner. It is not a summariser of the page — it holds the session's data:

- **Questions.** It never does arithmetic itself. It writes a Python query,
  which runs in a jailed `python3` subprocess with `analysis` (the parsed
  `analysis.json`) and `csv("sales")`-style access to the seven uploaded CSVs,
  and answers from the returned numbers. Each query is shown in the transcript,
  so any figure can be checked.
- **New components.** Ask for a table, chart, list or card and it queries the
  numbers, copies the classes of a comparable block already in the report, and
  renders it in place, outlined and pending. It is saved only when you press
  Keep. "Keep + reuse monthly" also writes the recipe to
  `report_assets/components/`, and future reports pick it up automatically
  wherever their layout has the same anchor.
- **Styling and layout.** Scoped CSS, hide/show, move, reorder and text edits
  apply to the live page at once, stay pending until kept, and each kept change
  is revertible by id.

Nothing is written into the report file itself: changes live in
`uploads/<session>/report-overrides.json` and are replayed on load, so an edit
is always reversible. **Save** in the dock bakes the current page into the HTML.

Editing is gated on a per-session token that is injected only for the report's
owner — someone who opened the report through a `/join/:code` presentation link
gets the same chat, read-only.

| env var | |
|---|---|
| `AGENT_MAX_STEPS` | tool-call ceiling per turn (default 12) |
| `AGENT_SANDBOX_TIMEOUT_MS` | wall-clock kill for one query (default 45000) |
| `AGENT_SANDBOX_CPU` | CPU-seconds per query (default 30) |
| `AGENT_SANDBOX_MEM_MB` | memory cap per query (default 1024) |

## Layout

| path | |
|---|---|
| `server.js` | Express app: upload, analyse, generate, reports index |
| `analyze_v2.py` | CSVs → `analysis.json` |
| `gen_report_v2.py` | report assembly and all derived figures |
| `sections_v2.py` | the seven chapters |
| `charts_v2.py` | inline SVG charts |
| `report_shell.py` | the master template |
| `openai_insights.js` | narratives, with caching |
| `llm_providers.js` | provider chain and fallback |
| `agent/` | the in-report assistant: loop, tools, sandbox, overrides |
| `public/agent-dock.js` | the chat panel injected into every served report |
| `pdf_export.js` | server-side PDF route |
| `views/` | upload, select, result, reports |
| `scripts/` | tests |
