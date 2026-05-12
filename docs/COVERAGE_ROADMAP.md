# Coverage Roadmap (v31.3 → v31.6)

## Current baseline (post-Sprint 139, v31.2.0)

- **Overall coverage:** 93.83 % (25,889 statements / 1,597 missed)
- **Tests:** 7,542 passing, 55 skipped, 1 xfailed
- **Floor enforced in CI:** `--cov-fail-under=80`

The headline number is healthy, but it masks a long tail of under-covered
modules — most of them in user-facing entry points (`api_server`,
`notebook_api`) and observability/reporting (`monitoring`,
`prep_lineage_report`, `comparison_report`). These are exactly the surfaces
that will fail in production but never in CI today.

## Coverage hotspots — biggest "missed-line" debts

| Module | Cover | Missed | Why it matters |
|--------|-------|--------|----------------|
| `api_server.py` | **58.8 %** | 119 | REST endpoints (`/migrate`, `/status`, `/download`) are untested. Untested HTTP error paths = 5xx in prod. |
| `notebook_api.py` | **71.0 %** | 51 | Interactive Jupyter `MigrationSession` API — only happy path covered; `edit_dax`, `override_visual_type`, `deploy` paths missing. |
| `monitoring.py` | **74.1 %** | 44 | Azure Monitor / Prometheus / JSON backends — only one backend exercised. |
| `prep_lineage_report.py` | **84.9 %** | 73 | HTML rendering branches for empty/single-flow lineage. |
| `preceptor.py` | **86.8 %** | 71 | DRAFT→REVIEW→COACH cycle escalation paths. |
| `dataflow_generator.py` | **86.2 %** | 23 | Lakehouse destination edge-cases. |
| `comparison_report.py` | **85.6 %** | 30 | HTML diff branches. |
| `validator.py` | **92.2 %** | 90 | Many small dead branches across 1,154-line file (high absolute miss). |
| `tmdl_generator.py` | **94.9 %** | 169 | Largest module — many late-added healers, Calendar/RLS edge cases. |
| `pbip_generator.py` | **95.8 %** | 94 | Drill-through, tooltip, sync-group edge cases. |
| `shared_model.py` | **94.2 %** | 106 | Cross-workbook conflict resolution edge cases. |
| `extract_tableau_data.py` | **94.9 %** | 96 | Defensive XML branches for malformed TWB. |
| `dax_converter.py` | **96.4 %** | 56 | Rare table-calc / window-function branches. |
| `self_healing_v3.py` | **91.8 %** | 71 | All 40 healers covered, but recovery-report-not-set branches missing. |

## Goal

**Lift overall coverage from 93.83 % → ≥ 98 %** over 4 sprints, with
**no module under 90 %** and **no critical path under 95 %**.

Raise the CI floor from 80 % → **95 %** at the end of Sprint 143.

---

## Sprint 140 (v31.3.0) — Public-API & user-entry-point coverage  ✅ SHIPPED

Target: lift `api_server`, `notebook_api`, `monitoring` to ≥ 90 %.

| Module | From | After Sprint 140 | Δ |
|--------|------|------------------|---|
| `api_server.py` | 58.8 % | **66.8 %** | +8.0 pts |
| `monitoring.py` | 74.1 % | **87.1 %** | +13.0 pts |
| `notebook_api.py` | 71.0 % | 71.0 % | _gated on real workbook fixture; deferred to Sprint 141_ |
| **`self_healing_report.py`** (new module) | — | **92.5 %** | new |

**Delivered:** 86 new tests across `tests/test_self_healing_report.py` (43)
and `tests/test_coverage_sprint140.py` (43). Net suite **7,628 passing
(+86)**. Overall coverage **93.83 % → 94.0 %**. Plus a new module
(`self_healing_report.py`, 11 healers) wired into `pbip_generator`.

**Carry-over to Sprint 141:** `notebook_api.py` lifecycle methods that
require a real workbook (load/assess/generate/deploy) — needs a tiny
fixture .twbx checked in.

---

## Sprint 141 (v31.4.0) — Reporting & observability coverage

Target: lift HTML/report generators to ≥ 95 %.

| Module | From | To | Tests to add |
|--------|------|----|---------------|
| `prep_lineage_report.py` | 84.9 % | 96 % | Empty graph, single-flow graph, no-merge-recommendations, all 5 rec types, Mermaid diagram size limits, JSON export round-trip |
| `comparison_report.py` | 85.6 % | 96 % | All diff categories (added / removed / modified), empty-vs-empty, large-vs-large, HTML escaping of special chars |
| `merge_report_html.py` | 93.7 % | 97 % | RLS conflict table empty/non-empty, relationship suggestions, fidelity-bar branches |
| `preceptor.py` | 86.8 % | 95 % | All 3 quality gates (DRAFT→REVIEW→APPROVE, COACH→REVIEW retry, escalation after 3 cycles), all 6 dimension scorers, SSIM low-score branch |
| `visual_diff.py` | 91.9 % | 97 % | Per-field coverage gap detection, encoding gap detection, empty-vs-empty |

**Estimate:** ~70 new tests, ~250 lines covered. **Net coverage +0.6 pp → ~96.0 %.**

---

## Sprint 142 (v31.5.0) — Core generator long-tail coverage

Target: kill the long tail of dead branches in the 3 biggest modules.

| Module | From | To | Strategy |
|--------|------|----|----------|
| `tmdl_generator.py` | 94.9 % | 97.5 % | Branch tests for every `if not …: return` early-exit; Calendar table without dates; RLS with cross-table refs; calc-group with single measure; field-parameter with single field |
| `pbip_generator.py` | 95.8 % | 97.5 % | Drill-through with no targets; tooltip with no fields; slicer sync-group across pages; bookmark with no display name; mobile layout fallback |
| `validator.py` | 92.2 % | 96 % | All `*_validate_*` failure messages; corrupted JSON; missing TMDL files; circular references |
| `shared_model.py` | 94.2 % | 96 % | Conflict resolution: same-name-different-formula measures; same-fingerprint-different-data tables; RLS conflicts; cross-workbook relationship suggestions with fuzzy match |
| `extract_tableau_data.py` | 94.9 % | 97 % | Malformed TWB elements (missing attributes, invalid XML inside CDATA); empty `.twbx` archives; password-protected workbooks |

**Estimate:** ~120 new tests, ~430 lines covered. **Net coverage +1.6 pp → ~97.6 %.**

---

## Sprint 143 (v31.6.0) — Defensive paths & coverage floor

Target: clean up the remaining sub-95 % modules and **raise CI floor to 95 %**.

| Module | From | To | Notes |
|--------|------|----|-------|
| `self_healing_v3.py` | 91.8 % | 97 % | Add `recovery=None` paths for all 40 healers; severity-`error` branches |
| `datasource_extractor.py` | 88.7 % | 95 % | Connections without server attr; calculations without datatype; relationships without join clause |
| `hyper_reader.py` | 89.4 % | 95 % | All 3 reader-tier fallbacks (tableauhyperapi missing, sqlite3 fails, binary scan); CSV export edge cases; type mapping for all 28 types |
| `prep_flow_analyzer.py` | 89.2 % | 95 % | All 18 Clean operation types; flow with 0 inputs / 0 outputs / 0 transforms |
| `server_client.py` | 88.0 % | 95 % | All 9 paginated endpoints; auth failure (401, 403); rate-limit retry (429) |
| `geo_passthrough.py` | 86.7 % | 95 % | ZIP slip attempts, malformed GeoJSON, missing files |
| `security_validator.py` | 88.4 % | 96 % | All 10 credential patterns; null-byte rejection; XXE in nested entities; ZIP slip in nested archives |
| `marketplace.py` | 90.2 % | 96 % | Pattern not found; semver mismatch; corrupted catalog JSON |

**Final action:** bump `pyproject.toml` `--cov-fail-under` from 80 → **95**.

**Estimate:** ~100 new tests, ~290 lines covered. **Net coverage +1.0 pp → ≥ 98.0 %.**

---

## Acceptance gates

| Sprint | Coverage target | Floor | Tests added | Cumulative tests |
|--------|-----------------|-------|-------------|------------------|
| 140 (v31.3) | ≥ 95 % | 80 % | ~80 | ~7,620 |
| 141 (v31.4) | ≥ 96 % | 80 % | ~70 | ~7,690 |
| 142 (v31.5) | ≥ 97.5 % | 90 % | ~120 | ~7,810 |
| 143 (v31.6) | ≥ 98 % | **95 %** | ~100 | ~7,910 |

## Out of scope (deferred)

- **`self_healing_report.py` (v3.4 visual healers)** — orthogonal effort, will
  be sequenced alongside Sprint 142 since it'll generate its own coverage debt.
- **Mutation testing (`mutmut`/`cosmic-ray`)** — to be considered after the
  98 % line-coverage gate is held for one sprint.
- **Branch coverage** — currently CI runs line coverage only. Switch to
  `--cov-branch` proposed for Sprint 144.

## Operating principles

1. **Cover behavior, not lines.** Every new test asserts an observable
   contract (return value, exception class, side effect). No "import-only"
   tests.
2. **No mocks for things we own.** Use real fixtures (`.twbx`, `.tfl`,
   model dicts) from `examples/`. Mocks reserved for HTTP / Azure clients.
3. **Parametrize aggressively.** Many of the missing branches are tier
   selectors (`backend == 'azure'` vs `'prometheus'`) — one parametrized
   test ≫ four copy-pasted tests.
4. **Snapshot tests for HTML.** For `*_report.py` modules, add golden-file
   snapshots in `tests/fixtures/golden/` to catch silent regressions.
