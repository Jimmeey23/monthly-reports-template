# Kwality House & Supreme HQ Performance Reports — June & July 2026

## Phase 1: Data Analysis (4 reports × all metrics)
- [x] Examine revised sales file (15) — understand column changes, location filtering, discount column
- [x] Validate sales methodology: Gross = Sale Total Paid (dedup by Sale ID), Net = Mrp-PreTax, Disc = Sale Item Unit Discount Value
- [x] Verify May 2026 reference numbers still match (Gross ₹24.28L ✓, Net ₹23.11L ✓, Members 193 ✓)
- [x] Build comprehensive analysis script for 4 combos (KW-Jun, KW-Jul, Supreme-Jun, Supreme-Jul)
- [x] Compute all metrics: sales, sessions, funnel, lapsed, checkins, active, MoM comparators, baselines
- [x] Export to JSON for report generation (analysis_v2.json - 936KB)

## Phase 2: Report Generation (4 HTML reports)
- [x] Create report generator template (parameterized by location + month)
- [x] Fix TypeError in build_section_01_kpi_table (pct_change receiving strings)
- [x] Fix heatmap TypeError (dict vs int comparison)
- [x] Generate KW June 2026 report (160,003 chars)
- [x] Generate KW July 2026 report (161,005 chars)
- [x] Generate Supreme HQ June 2026 report (149,903 chars)
- [x] Generate Supreme HQ July 2026 report (153,513 chars)

## Phase 3: Validation & Delivery
- [x] Verify all 4 reports have correct HTML structure (balanced divs, 7 sections, no errors)
- [x] Verify all 4 reports render correctly in browser (dark theme, KPIs, sections)
- [x] Deploy all 4 reports to public URLs
- [x] All 4 deployed URLs return HTTP 200
