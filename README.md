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
| `pdf_export.js` | server-side PDF route |
| `views/` | upload, select, result, reports |
| `scripts/` | tests |
