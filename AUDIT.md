# Studio Pulse — Full Application Audit

> **Date:** September 2026  
> **Repo:** `monthly-reports-template`  
> **Stack:** Node.js 20 + Express + Socket.io + Multer · Python 3 (analysis + HTML generation) · EJS · GPT-4o · Puppeteer (PDF)

---

## Executive Summary

Studio Pulse is a fitness-studio performance reporting platform. Users upload 7 CSV exports (sales, sessions, check-ins, leads, new trials, lapsed, active members), the Python engine analyzes the data, and a rich HTML report is generated per studio × month with AI-powered strategic insights. Reports are editable in-browser, exportable as PDF, and presentable in live collaborative sessions.

**What's genuinely impressive:**
- The AI insight engine with randomized analytical angles and industry benchmarks is unusually sophisticated for this space
- Live presenter mode with scroll/click sync and annotation tools (highlight, pen, tooltips) is production-quality
- Smart CSV auto-detection by filename keyword matching is excellent UX
- The report HTML output is beautiful — editorial-grade design with KPI cards, heatmaps, data tables
- Chunked upload architecture handles large exports gracefully

**Where the biggest gaps are:**
- Architecture is monolithic (1,182-line `server.js` with inline HTML/CSS/JS)
- Zero authentication, authorization, or rate limiting
- No interactive charts, goal tracking, or comparative analytics
- No tests, no CI, no data validation layer
- Reports are static HTML — no drill-down, filtering, or search

---

## 1. Architecture & Code Quality

### 1.1 Monolithic Server File
`server.js` is 1,182 lines containing route handlers, session management, file I/O, Socket.io event handlers, inline HTML template literals (the `/july-report/:studio` route has ~200 lines of inline CSS and JS), and business logic all in one file.

**Recommendation:** Break into modules:
```
server.js              → App bootstrap only
routes/upload.js       → Upload + chunk handling
routes/reports.js      → Generate, view, download, save
routes/presenter.js    → Socket.io presenter rooms
routes/july.js         → Static July report routes
middleware/session.js  → Session store + manifest
middleware/auth.js     → (new) Authentication
services/analysis.js   → Python script runner
services/pdf.js        → Puppeteer wrapper
services/ai.js         → OpenAI integration
```

### 1.2 Duplicated Python Functions
`gen_report_v2.py` defines `build_location_meta()` and `build_month_meta()` **twice** (lines ~50 and ~180). The second definitions silently override the first. Also `build_context()` has a duplicate `return ctx` statement at the end — dead code.

**Recommendation:** Delete the duplicates and the dead return statement.

### 1.3 No Build Process for CSS
CSS lives in `full_css.txt` (loaded as a raw string) and inline `<style>` blocks scattered across Python and JS. There's no CSS preprocessor, no build step, and no way to share variables across the upload UI, report templates, and client scripts.

**Recommendation:** Adopt Tailwind CSS or CSS Modules with a build step. Alternatively, use PostCSS with `@import` and CSS custom properties defined in a single `tokens.css`.

### 1.4 Custom .env Parser
The app has a hand-rolled `.env` parser (lines 12–22 of `server.js`) instead of using the standard `dotenv` package.

**Recommendation:** Replace with `require('dotenv').config()`.

### 1.5 Session Store Has No TTL or Cleanup
The `sessions` Map grows unbounded. The manifest file caps at 30 entries but the underlying disk directories are never cleaned up.

**Recommendation:** Add a TTL (e.g., 30 days) with periodic cleanup, or use a proper session store (Redis, SQLite).

---

## 2. Security

### 2.1 No Authentication or Authorization ⚠️ Critical
Every endpoint — upload, analyze, generate, save, AI insights, PDF download — is completely open. Anyone with the URL can:
- Upload arbitrary files to consume server resources
- Trigger unlimited GPT-4o API calls (expensive)
- Read/overwrite any saved report by guessing session IDs
- Access other users' data

**Recommendation:** Implement at minimum:
- API key or JWT authentication for all endpoints
- Session-scoped access (users can only access their own sessions)
- Rate limiting on `/ai-insights` and `/upload-chunk`

### 2.2 No Security Headers
No Helmet.js, no CSP, no X-Frame-Options, no rate limiting.

**Recommendation:**
```js
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
app.use(helmet({ contentSecurityPolicy: false })); // Reports use inline styles
app.use('/ai-insights', rateLimit({ windowMs: 60000, max: 10 }));
app.use('/upload-chunk', rateLimit({ windowMs: 60000, max: 100 }));
```

### 2.3 CORS Wildcard
Both Express and Socket.io use `origin: '*'`. This allows any website to make authenticated requests.

**Recommendation:** Restrict to known origins via environment variable.

### 2.4 No CSRF Protection
All POST endpoints lack CSRF tokens. The `save-report` endpoint is especially vulnerable — a malicious page could overwrite reports.

**Recommendation:** Add `csurf` middleware or use SameSite cookies with session tokens.

### 2.5 Path Traversal — Partially Mitigated
The `startsWith(session.dir)` check exists but doesn't normalize paths first. On some platforms, `/uploads/abc/../def/report.html` could bypass it.

**Recommendation:** Always `path.resolve()` before checking:
```js
const resolved = path.resolve(session.dir, req.params.filename);
if (!resolved.startsWith(path.resolve(session.dir))) return res.status(400)...;
```

### 2.6 No Input Sanitization
- CSV filenames are not sanitized before use as filesystem paths
- The `save-report` endpoint writes arbitrary HTML to disk without sanitization
- User-provided text in annotations and tooltips is injected into DOM without escaping in some paths

---

## 3. Missing Features — High Impact

### 3.1 Interactive Data Visualization 📊
Reports currently use static HTML tables and tiny SVG sparklines. There are **no interactive charts** — no line charts for revenue trends, no bar charts for trainer comparisons, no pie charts for category breakdown, no interactive heatmaps.

**Recommendation:** Integrate Chart.js, ApexCharts, or Observable Plot. Each section should have:
- Revenue trend line (multi-month) with hover tooltips
- Category/product breakdown bar charts
- Trainer performance comparison bars
- Funnel visualization for lead → trial → conversion
- Interactive day/hour heatmap for class scheduling

This is the single highest-impact visual upgrade.

### 3.2 Goal & Target Tracking 🎯
There's no way to set targets (e.g., "₹30L net revenue target", "5% churn max", "70% fill rate goal") and show progress visually.

**Recommendation:** Add a `targets.json` config per studio that the report generator reads. KPI cards should show:
- Progress bar toward monthly/quarterly target
- "On track" / "At risk" / "Behind" status indicators
- Projected end-of-quarter based on current velocity

### 3.3 Comparative Analytics ⚖️
Currently reports are siloed per studio × month. There's no side-by-side comparison view.

**Recommendation:** Add a "Compare" mode that lets users:
- Select 2 studios or 2 months and see a diff view
- Overlay revenue trends for all studios on one chart
- See "Studio A outperforms Studio B by X% on fill rate but trails by Y% on conversion"
- Auto-generate comparative AI narrative

### 3.4 Data Source Integration (API Connectors) 🔌
The only input method is manual CSV upload. This is the biggest friction point in the workflow.

**Recommendation:** Build direct integrations:
- **Momence API** connector (the platform the CSVs are exported from) — auto-pull data on schedule
- **Stripe/payment gateway** integration for real-time revenue data
- **Webhook endpoints** that accept data pushes from studio management software
- Scheduled auto-generation: "Every 1st of the month, pull last month's data and generate reports"

### 3.5 Email Delivery & Scheduling 📧
Reports can only be viewed in-browser or downloaded. There's no way to email them to stakeholders.

**Recommendation:**
- "Share via email" button that sends a branded email with the report as attachment or link
- Scheduled delivery: "Send Kwality House report to management@studio.com on the 3rd of every month"
- Digest emails with key metric changes vs. previous month

### 3.6 Report Versioning & History 📜
Saving a report overwrites the previous version. There's no version history, no diff view, no way to revert.

**Recommendation:**
- Store each save as a versioned snapshot (e.g., `report_v1.html`, `report_v2.html`)
- Show a version history sidebar with timestamps
- Allow reverting to any previous version
- Show diff between versions (what changed in the AI insights or manual edits)

### 3.7 Multi-Tenancy & User Management 👥
There's no concept of users, organizations, or roles. The app is effectively single-user.

**Recommendation:**
- User accounts with email/password or OAuth
- Organizations/workspaces that own sessions and reports
- Role-based access: Admin, Manager, Viewer
- Per-studio access controls (e.g., Kemps Corner manager can only see KW reports)

---

## 4. Missing Features — Medium Impact

### 4.1 Search & Navigation Within Reports
Reports are long (7 sections, 150K+ characters). There's no search, no table of contents with scroll-to-section, and no keyboard shortcuts.

**Recommendation:** Add:
- Cmd+K search palette that searches all text, metrics, and AI insights
- Sticky table of contents sidebar with active-section highlighting
- Keyboard shortcuts: `1-7` to jump to sections, `n/p` for next/previous

### 4.2 Interactive Tables (Sort, Filter, Drill-Down)
All data tables are static HTML. Users can't sort columns, filter rows, or click a row to see detail.

**Recommendation:**
- Client-side sorting on all table columns (click header to sort)
- Filter inputs above tables (e.g., "show only trainers with >20 sessions")
- Click a trainer row → expand to show their class-level breakdown
- Click a product row → show monthly sales trend for that product

### 4.3 Collaboration & Review Workflow 💬
Multiple stakeholders review these reports but there's no way to:
- Add comments to specific sections or metrics
- Tag colleagues for review
- Approve/reject AI-generated insights
- Track who made what edits

**Recommendation:**
- Comment threads anchored to specific report sections
- @-mentions with email notifications
- "Request review" workflow: Draft → In Review → Approved
- Change tracking (who edited what, when)

### 4.4 White-Label / Brand Customization 🎨
Reports always show "Studio Pulse" branding. Studios can't customize:
- Logo and brand colors
- Report cover page
- Footer disclaimer text
- Email template branding

**Recommendation:** Add a `branding` config per organization:
```json
{
  "logo_url": "...",
  "primary_color": "#005fef",
  "report_title": "Kwality House Monthly Review",
  "footer_disclaimer": "Confidential — For internal use only",
  "email_template": "..."
}
```

### 4.5 Anomaly Alerts & Proactive Notifications 🔔
The AI detects anomalies (revenue spikes, unusual churn) but these are only visible inside the report. There are no proactive alerts.

**Recommendation:**
- After analysis, auto-detect anomalies and surface them as alerts on the dashboard
- Email/Slack notifications: "⚠️ Kwality House July churn rate is 8.2% — significantly above 3-month avg of 4.1%"
- Configurable alert thresholds per studio

### 4.6 Export to More Formats
Currently: HTML + PDF only.

**Recommendation:**
- **PowerPoint/Google Slides** — auto-generate a slide deck from the report (one slide per section, key metrics as charts)
- **Excel** — export all underlying data tables as a multi-sheet workbook
- **Notion/Confluence** — push report content to a wiki page
- **WhatsApp/Telegram** — send a summary card with key metrics

### 4.7 AI Insights Caching & Customization
Every "Generate AI Insights" click hits the GPT-4o API fresh. For the same studio × month × section, this wastes money and time.

**Recommendation:**
- Cache AI responses per `locKey|month|section|data_hash`
- Show "Last generated: 2 hours ago" with a "Regenerate" button
- Allow users to customize the AI prompt tone/style per organization
- Add a "Brief" mode (2-paragraph summary) vs "Detailed" mode (current)
- Let users provide context: "We launched a new pricing tier this month" → AI incorporates this

### 4.8 Historical Trend Dashboard
Outside of individual reports, there's no standalone dashboard showing multi-month trends across all studios.

**Recommendation:** A `/dashboard` route that shows:
- Revenue trend line for all studios overlaid
- Member growth chart (new joins vs. lapsed over time)
- Class utilization trends
- Conversion funnel trends
- Quick-glance "health score" per studio

---

## 5. Missing Features — Sophisticated Upgrades

### 5.1 Predictive Analytics & Forecasting 🔮
The current "predictions" section relies on AI-generated text. Add actual statistical forecasting:

- **Revenue forecasting** — ARIMA or exponential smoothing on historical revenue
- **Churn prediction** — identify members at risk of lapsing based on check-in frequency decline
- **Capacity planning** — predict when fill rates will hit ceiling at current growth rate
- **Seasonal decomposition** — separate trend, seasonal, and noise components
- **What-if scenarios** — "If conversion rate improves by 5pp, projected revenue increase = ₹X"

### 5.2 Member Cohort Analysis 👥
The data has member IDs but the analysis doesn't use them for cohort tracking.

**Recommendation:**
- Track cohorts by join month: "Members who joined in Jan — how many are still active in Jul?"
- Cohort retention curves (the classic triangle chart)
- Identify "power user" cohorts vs "at-risk" cohorts
- Calculate LTV (lifetime value) per cohort
- "Members who attend PowerCycle have 40% lower churn than Barre-only members"

### 5.3 Natural Language Query Interface 🗣️
Instead of static reports, let users ask questions:

- "Which trainer had the best fill rate in July?"
- "How does Kwality House compare to Supreme HQ on lead conversion?"
- "What was our best-selling product category last quarter?"
- "Show me the trend in late cancellations over the last 6 months"

Use GPT-4o with function calling against the analysis JSON to answer these interactively.

### 5.4 Automated Action Items & Task Management ✅
AI recommendations currently appear as text in the report. Make them actionable:

- Each recommendation becomes a trackable task with assignee, deadline, status
- Integration with project management tools (Notion, Asana, Trello, Linear)
- Weekly digest email: "3 action items from last month's report are overdue"
- Next month's report auto-references: "Last month recommended X — here's the impact"

### 5.5 Smart Report Narration (Audio) 🎙️
The app already has audio infrastructure (section-audio.js, sfx-soundboard.js). Extend it:

- Auto-generate a 5-minute audio summary of each report using TTS
- "Podcast mode" — two AI voices discussing the report findings conversationally
- Embed audio player in the report header: "Listen to this report (4:32)"
- Useful for executives who prefer audio over reading

### 5.6 Data Pipeline Automation 🔄
Replace the manual CSV upload workflow entirely:

```
Momence/CRM API → Scheduled ETL (cron) → Analysis Engine → Report Generation → Email Delivery
```

- Configurable data sources per studio
- Automatic data quality checks before report generation
- Slack notification when report is ready: "📊 Kwality House August report is ready — [View] [PDF] [Slides]"

### 5.7 Benchmarking Network 📈
If multiple studios use the platform (anonymized):

- "Your fill rate of 72% puts you in the top quartile of boutique studios in your city"
- Anonymous benchmarking across the platform's user base
- Industry reports: "Average churn for premium fitness studios in Mumbai: 5.2%"

---

## 6. Developer Experience & DevOps

### 6.1 No Tests
Zero test files, no test framework, no CI pipeline.

**Recommendation:**
- Add Jest for server-side unit tests
- Add Playwright for E2E tests (upload → analyze → generate → verify report)
- Add Python pytest for `analyze_v2.py` and `gen_report_v2.py`
- Set up GitHub Actions CI: lint → test → build → deploy

### 6.2 No TypeScript
The entire Node.js codebase is plain JavaScript with no type safety. Given the complexity of the data structures (nested `analysis.json` with locations × months × metrics), TypeScript would catch many bugs.

**Recommendation:** Migrate to TypeScript incrementally:
1. Define interfaces for `Analysis`, `Session`, `ReportContext`, etc.
2. Convert `openai_insights.js` → `.ts` first (most complex logic)
3. Convert route handlers next

### 6.3 No Docker Configuration
Deployment relies on platform-specific configs (Vercel, Railway, Nixpacks). No Dockerfile for consistent local/cloud parity.

**Recommendation:** Add a `Dockerfile` + `docker-compose.yml` that bundles Node.js + Python + Chrome (for Puppeteer):
```dockerfile
FROM node:20-slim
RUN apt-get update && apt-get install -y python3 chromium
ENV CHROME_PATH=/usr/bin/chromium
COPY . /app
WORKDIR /app
RUN npm ci
EXPOSE 3000
CMD ["node", "server.js"]
```

### 6.4 No Logging Framework
All logging uses `console.log` / `console.error`. No structured logging, no log levels, no request correlation IDs.

**Recommendation:** Use `pino` or `winston` with structured JSON logging:
```js
const logger = require('pino')();
logger.info({ sessionId, locKeys, months }, 'Report generated');
```

### 6.5 Error Handling Inconsistency
Some errors return JSON, some return plain text, some render EJS templates. Client-side error handling varies between `alert()` and inline error boxes.

**Recommendation:**
- Centralized error handler middleware
- Consistent error response format: `{ error: { code, message, details } }`
- Client-side toast notification system instead of alerts

---

## 7. Performance

### 7.1 AI Insights Generated Serially per Section
The `/generate` route fires all AI insight requests concurrently (`Promise.all`) but each one independently calls the GPT-4o API. For a 2-studio × 2-month bundle with 7 sections, that's 28 API calls.

**Recommendation:**
- Batch all sections into a single GPT-4o call with structured output
- Cache results aggressively (see 4.7)
- Show progressive loading: sections render as their AI insights arrive

### 7.2 Report HTML is Huge (150K+ chars)
Every report embeds the full CSS (~40K), all data tables, and all formatting. The same CSS is duplicated across every report.

**Recommendation:**
- Serve CSS as an external file with cache headers
- Lazy-load sections as the user scrolls (intersection observer)
- Compress HTML with gzip (already handled by Express but verify)

### 7.3 Python Analysis Reads CSV Multiple Times
`analyze_sales()` reads the sales CSV **twice** — once for aggregations, once for breakdowns. For large exports, this doubles I/O.

**Recommendation:** Read once, build all data structures in a single pass.

### 7.4 Puppeteer Launches Chrome Per PDF Request
Each PDF export spawns a new Chrome instance. This is slow (2-5 seconds startup) and memory-intensive.

**Recommendation:** Use a Chrome pool (launch once, reuse across requests) or a service like Browserless.

---

## 8. Accessibility & Mobile

### 8.1 Reports Are Desktop-First
The report layout assumes wide screens (1560px container). On mobile, tables overflow horizontally and KPI cards stack awkwardly.

**Recommendation:**
- Responsive data tables that collapse to card views on mobile
- Swipeable KPI cards
- Collapsible sections by default on small screens
- Test with real mobile devices, not just DevTools

### 8.2 Accessibility Gaps
- KPI cards have `role="button"` and `tabindex="0"` (good) but flip animation isn't `prefers-reduced-motion` aware in all cases
- Editor toolbar buttons lack `aria-label` in some cases
- No skip-to-content link
- Color-only indicators (green/red badges) without text alternatives
- Screen reader announcements missing for dynamic content (AI insights loading, section changes)

---

## 9. Quick Wins (Implement in < 1 Day Each)

| # | Improvement | Impact | Effort |
|---|---|---|---|
| 1 | Add Helmet.js security headers | Security | 30 min |
| 2 | Add rate limiting on AI + upload endpoints | Security/Cost | 1 hour |
| 3 | Fix duplicate Python functions | Code quality | 15 min |
| 4 | Add `dotenv` package, remove custom parser | Code quality | 15 min |
| 5 | Cache AI insights in a JSON file per session | Cost/Speed | 2 hours |
| 6 | Add keyboard shortcuts (1-7 for sections) | UX | 1 hour |
| 7 | Add sticky table of contents to reports | UX | 2 hours |
| 8 | Normalize paths before `startsWith` check | Security | 15 min |
| 9 | Add gzip compression middleware | Performance | 15 min |
| 10 | Add structured logging with `pino` | DevOps | 1 hour |
| 11 | Add a `/dashboard` route showing saved sessions + key metrics | UX | 3 hours |
| 12 | Add `Content-Disposition: inline` for report viewing | UX | 5 min |
| 13 | Add CSV column validation with user-friendly error messages | UX | 2 hours |
| 14 | Add favicon and meta tags for report sharing | Polish | 30 min |
| 15 | Add "Copy report link" button | UX | 15 min |

---

## 10. Recommended Priority Roadmap

### Phase 1 — Foundation (Week 1-2)
- [ ] Authentication & authorization (JWT or session-based)
- [ ] Rate limiting and security headers
- [ ] Fix code quality issues (duplicates, dead code, monolith split)
- [ ] Add test framework with basic coverage
- [ ] Docker setup for consistent deployment

### Phase 2 — Visual Upgrade (Week 3-4)
- [ ] Interactive charts (Chart.js or ApexCharts) in every section
- [ ] Goal/target tracking with progress visualization
- [ ] Responsive mobile layout for reports
- [ ] Search and sticky table of contents
- [ ] Interactive sortable tables

### Phase 3 — Platform Features (Week 5-8)
- [ ] Multi-tenancy and user management
- [ ] Report versioning and history
- [ ] Email delivery and scheduling
- [ ] Comparative analytics (studio vs. studio, month vs. month)
- [ ] AI insights caching and customization

### Phase 4 — Intelligence (Week 9-12)
- [ ] Predictive analytics and forecasting
- [ ] Cohort analysis and member lifecycle tracking
- [ ] Natural language query interface
- [ ] Automated action items and task tracking
- [ ] Data pipeline automation (API connectors)
- [ ] Audio report narration

---

*This audit was performed by analyzing the full source code of the repository including server.js (1,182 lines), analyze_v2.py (958 lines), gen_report_v2.py (1,053 lines), sections_v2.py (2,861 lines), openai_insights.js (765 lines), report-client.js (1,627 lines), pdf_export.js (60 lines), and all EJS templates, client scripts, and configuration files.*
