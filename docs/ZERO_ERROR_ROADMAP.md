# Zero-Error Migration Roadmap

**Goal:** Reach the state where any `.twbx` we accept produces a `.pbip` that
opens cleanly in Power BI Desktop **on the first try**, with **zero manual
fixes** and **zero silent data loss**.

**Baseline (post Sprint 140 / v31.3.0):**
- 7,628 tests passing, 94.0 % coverage
- 51 self-healing healers (40 model + 11 report)
- Validator catches structural defects post-write
- No formal cross-platform equivalence testing in CI
- No automated rollback on critical defects

**North-star metric:** _Zero-Touch Open Rate_ = % of corpus workbooks that
open in PBI Desktop with **0 errors / 0 warnings / 0 missing visuals**.
Today: estimated **~70 %** on the bug-bash corpus. Target: **≥ 99 %** by end
of Sprint 150.

---

## Strategy

The 10 phases form a **defence-in-depth** stack — each phase catches errors
the previous one missed. Earlier phases prevent; later phases verify and
recover.

```
 INPUT  ──▶  Phase 1: Pre-flight reject
            Phase 2: Extraction guards
            Phase 3: Conversion guards
       ──▶  Phase 4: Self-Healing v3.5 (model)
            Phase 5: Self-Healing v3.6 (report)
       ──▶  Phase 6: Cross-artifact validator
            Phase 7: Schema validator (PBI 2025 spec)
       ──▶  Phase 8: Equivalence testing in CI
            Phase 9: Auto-rollback + recovery report
            Phase 10: Continuous feedback loop
 OUTPUT ──▶  .pbip  (zero-touch open)
```

---

## Phase 1 — Pre-flight Rejection (Sprint 141 / v31.4.0)

**Owner:** @assessor + @orchestrator
**Goal:** Refuse early when migration would certainly fail.

| Check | Action |
|-------|--------|
| Workbook is encrypted / password-protected | Hard fail with clear message |
| Tableau version > supported (currently 2024.3) | Warn + require `--force` |
| Datasource uses unsupported connector (e.g. Hive 0.x, Splunk legacy) | Mark connector RED, suggest replacement |
| Workbook has corrupt/truncated XML | Hard fail with line-number diagnostic |
| `.twbx` ZIP slip / nested traversal | Hard fail (already in `security_validator`) |
| Workbook references non-existent extracts | Warn + offer `--ignore-missing-extracts` |
| Workbook size > 500 MB or visual count > 1,000 | Warn + suggest `--shared-model` split |

**Module:** new `powerbi_import/preflight.py` returning `PreflightResult`
(blockers, warnings, advisories). Wired into `migrate.py` before extraction.

**Tests:** ~30 unit tests + 5 fixture workbooks for each blocker class.

---

## Phase 2 — Extraction Guards (Sprint 142 / v31.5.0)

**Owner:** @extractor
**Goal:** Make `tableau_export/*` raise no silent `KeyError`/`AttributeError`
on malformed input.

- Wrap every `xml.etree` lookup with safe `_get(elem, attr, default)` helper
- Centralise in `tableau_export/safe_xml.py` — already partially exists in
  `security_validator`, lift its safe-parse helpers
- Add `ExtractionWarning` enum (28 known issues catalogued)
- All 17 extractors return `(data, warnings)` tuple instead of raising
- New regression: `tests/fixtures/malformed/` with 50 broken `.twb` snippets

**Coverage target:** `extract_tableau_data.py` 94.9 % → **97 %**

---

## Phase 3 — Conversion Guards (Sprint 143 / v31.6.0)

**Owner:** @dax + @wiring
**Goal:** Every Tableau→DAX and Tableau→M conversion either returns a valid
expression or returns `None` + a categorised warning. **Never a syntactically
broken string.**

- Add `dax_validator.validate_expression(expr) -> List[Issue]` that uses a
  small DAX grammar (already shipped in `dax_optimizer.parser`) to assert
  bracket balance, function arity, and known function names
- Same for M via `m_validator.py` (already exists — lift to mandatory pass)
- Every `dax_converter.convert_*` call wrapped in
  `try / except / fallback to TODO measure with note`
- New `ConversionRecovery` event type for telemetry

**Tests:** ~60 new tests covering every conversion that today silently
emits `[Foo]` without a table prefix or unbalanced parens.

---

## Phase 4 — Self-Healing v3.5 (model-side, Sprint 144 / v31.7.0)

**Owner:** @semantic
**Goal:** +10 healers covering model issues we keep seeing in bug-bash.

| Healer | Catches |
|--------|---------|
| `dax_unbalanced_brackets` | `[Col]` count ≠ closing `]` |
| `dax_unknown_function` | calls to `MAKEPOINT`, `SCRIPT_*` (post-conversion) |
| `dax_circular_dependency` | measure A ↔ B references |
| `relationship_orphan_table` | table never referenced and not a fact |
| `relationship_self_loop` | from-table = to-table |
| `column_duplicate_name_case` | `Date` and `date` collide in PBI |
| `column_invalid_datatype` | datatype not in {string,int,double,decimal,boolean,dateTime,binary} |
| `partition_empty_m` | M expression is `""` or `null` |
| `parameter_default_out_of_domain` | default value not in allowable list |
| `rls_missing_principal` | RLS role with no `tablePermissions` entry |

Wired into `_V3_HEALERS` (becomes 50 model healers).

---

## Phase 5 — Self-Healing v3.6 (report-side, Sprint 145 / v31.8.0)

**Owner:** @visual
**Goal:** +10 PBIR healers extending `self_healing_report.py` (becomes 21).

| Healer | Catches |
|--------|---------|
| `visual_overlap_full` | two visuals 100 % overlapping → stagger by 32 px |
| `visual_filter_unknown_field` | filter references column not in model |
| `visual_query_unknown_measure` | query projects measure not in model |
| `slicer_targets_missing_field` | slicer column was renamed/removed |
| `bookmark_targets_missing_visual` | bookmark visual states reference deleted visual |
| `theme_dataColors_empty` | `RegisteredResources/*.json` has empty palette |
| `page_no_visuals` | empty page → drop or add placeholder textbox |
| `pagesmeta_duplicate_pageorder` | same page listed twice |
| `tooltip_page_oversized` | tooltip page > 480×320 → resize |
| `mobile_layout_orphan_visual` | mobile layout references deleted visual |

---

## Phase 6 — Cross-artifact Validator (Sprint 146 / v31.9.0)

**Owner:** @semantic + @visual + @reviewer
**Goal:** Today the validator runs on TMDL **or** PBIR; bridge them.

- New `powerbi_import/cross_validator.py`:
  - Every visual query field reference must exist in the semantic model
  - Every relationship must reference real columns
  - Every RLS table must exist
  - Every theme `dataColors` index must be < N for actual data points
- Generates `cross_validation_report.html` + `.json`
- Pipeline: post-self-healing, runs in `--strict` mode (CI default)
- Failure in strict mode → exit code 4, no artifacts shipped

---

## Phase 7 — PBI Desktop Schema Validator (Sprint 147 / v31.10.0)

**Owner:** @visual
**Goal:** Validate every JSON artifact against the **actual** PBI 2025 JSON
schema (not just our internal expectations).

- Pull canonical schemas from
  `https://developer.microsoft.com/json-schemas/fabric/item/report/...` at
  build time (cached in `powerbi_import/schemas/`)
- New `schema_validator.py` using stdlib `jsonschema`-style walker (or vendor
  a tiny implementation; we still want zero deps)
- Run on every `*.json` in `<Report>/definition/` after self-healing
- Schema mismatches → repair where possible, else report

---

## Phase 8 — Equivalence Testing in CI (Sprint 148 / v32.0.0) ✅ Shipped

**Owner:** @tester + @reviewer
**Goal:** Catch silent semantic drift between Tableau and PBI output.

`equivalence_tester.py` already exists; promote to first-class CI gate:

1. **Corpus**: 25 representative `.twbx` (small / medium / complex / RLS /
   LOD / Prep / SCRIPT_*) — checked in under `tests/fixtures/equivalence/`
2. **Per workbook**:
   - Migrate end-to-end
   - Run `validator.full_check()` → must pass
   - Run `equivalence_tester.compare_measures()` against snapshot of expected
     values from a reference Tableau extract dump
   - Render headless PBI screenshots via `tableauhyperapi` + a tiny pbi
     evaluator (DAX-only via Microsoft.AnalysisServices), compare against
     baseline images at SSIM ≥ 0.97
3. **CI gates**: any drift > tolerance fails the build
4. New nightly job `.github/workflows/equivalence.yml`

---

## Phase 9 — Auto-Rollback + Recovery Report (Sprint 149 / v32.1.0) ✅ Shipped

**Owner:** @orchestrator + @reviewer
**Goal:** When a critical defect survives all healers, **don't ship** — back
off and emit a triage package.

- Severity ladder:
  - INFO → log only
  - WARNING → record in `RecoveryReport`, ship anyway
  - ERROR → ship to `<output>/_FAILED/` with `triage.html`
  - CRITICAL → roll back, leave only `triage_package.zip` (input + extraction
    JSONs + partial output + logs + recovery report)
- New `migrate.py --strict` exit codes:
  - 0 = clean
  - 1 = warnings only
  - 2 = errors (triage package emitted)
  - 3 = critical (rollback)
- Triage package auto-attaches to GitHub issue template

---

## Phase 10 — Continuous Feedback Loop ✅ Shipped

**Owner:** @assessor + @deployer
**Goal:** Every real-world failure becomes a regression test within 24 h.

- `--report-issue` CLI flag: creates redacted issue package ZIP
- `IssueCollector`: gathers verdict, extraction JSONs, QA report, fixture hint; redacts credentials
- `RegressionFixtureGenerator`: derives minimal regression fixture → `tests/fixtures/regressions/`
- `ZeroTouchTracker`: per-workbook success/failure tracking, Zero-Touch Open Rate computation
- Dashboard: `docs/zero_error_dashboard.html` — rate %, top failure modes, recent migrations
- `.github/workflows/regression_triage.yml` — weekly Monday triage bot
- 30 tests, 7,925 passed, 0 failed

---

## Per-Phase Exit Criteria

Every sprint must:
1. Add ≥ 30 unit tests, ≥ 95 % coverage on new code
2. Add ≥ 1 fixture workbook exercising the bug class end-to-end
3. Update Zero-Touch Open Rate metric in `docs/zero_error_dashboard.html`
4. Pass full suite with **0 regressions**
5. Bump CHANGELOG and the `ZERO_ERROR_ROADMAP.md` progress table

---

## Progress Tracker

| Phase | Sprint | Version | Status | Zero-Touch % |
|-------|--------|---------|--------|--------------|
| 1 — Pre-flight | 141 | v31.4.0 | ✅ Shipped | _baseline ~70 %_ |
| 2 — Extraction guards | 142 | v31.5.0 | ✅ Shipped | — |
| 3 — Conversion guards | 143 | v31.6.0 | ✅ Shipped | — |
| 4 — Self-Healing v3.5 | 144 | v31.7.0 | ✅ Shipped | — |
| 5 — Self-Healing v3.6 | 145 | v31.8.0 | ✅ Shipped | — |
| 6 — Cross-artifact validator | 146 | v31.9.0 | ✅ Shipped | — |
| 7 — Schema validator | 147 | v31.10.0 | ✅ Shipped | — |
| 8 — Equivalence in CI | 148 | v32.0.0 | ✅ Shipped | — |
| 9 — Auto-rollback | 149 | v32.1.0 | ✅ Shipped | — |
| 10 — Feedback loop | 150 | v32.2.0 | ✅ Shipped | **Target ≥ 99 %** |

---

## Risks

- **Headless PBI rendering** (Phase 8) is hard — may need a small AS-engine
  Docker image. Fallback: skip screenshot SSIM, keep measure-value drift.
- **Schema drift** at Microsoft's end (Phase 7) — pin to `2.5.0` family,
  re-pin manually each PBI Desktop release.
- **Telemetry privacy** (Phase 10) — must redact every connection string,
  PAT, sample data row before shipping. `security_validator` already has
  the redaction primitives; lift them.

---
---

# v33.0.0 — Full-Spectrum Migration Roadmap

**Goal:** Close every remaining gap between "what Tableau can do" and "what
the migrator produces" — covering **visual fidelity**, **datasource/connector
breadth**, **DAX conversion completeness**, **Tableau Server/Cloud depth**,
and **test coverage hardening**. Every sprint ships code, tests, and docs.

**Baseline (post v32.2.0 / Sprint 150):**
- 8,008+ tests, 96%+ coverage
- 118 visual type mappings, 33 connectors, 180+ DAX conversions
- Zero-Error infrastructure (10-phase defence stack) fully operational
- Fabric-native output operational (Lakehouse + Dataflow + Notebook + Pipeline)

**North-star metric:** _Migration Completeness Score_ — weighted coverage
across 5 axes. Target: **≥ 98 %** by end of Sprint 170.

| Axis | Weight | Baseline | Target |
|------|--------|----------|--------|
| Visual type coverage | 25 % | 118/125 known types (94 %) | ≥ 99 % |
| Datasource/connector coverage | 20 % | 33/50 enterprise connectors (66 %) | ≥ 90 % |
| DAX/formula conversion | 25 % | 180/195 Tableau functions (92 %) | ≥ 97 % |
| Tableau Server/Cloud integration | 15 % | 18 endpoints, batch, PAT auth (75 %) | ≥ 95 % |
| Test coverage depth | 15 % | 8,008 tests, 96 % line coverage | ≥ 9,500 tests, 97 % |

---

## Stream A — Visual Fidelity & Mapping Completeness

### Sprint 151 — Advanced Visual Types (v33.1.0)

**Owner:** @visual + @extractor
**Goal:** Close the remaining 7 unmapped or approximated visual types.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 151.1 | **Violin plot native** | @visual | `visual_generator.py` | Map Tableau violin → PBI `ViolinPlot1.0.0` custom visual with proper distribution encoding (median, quartiles, kernel density). Include AppSource GUID + fallback to `boxAndWhisker`. |
| 151.2 | **Parallel coordinates native** | @visual | `visual_generator.py` | Map → `ParallelCoordinates1.0.0` custom visual with proper axis config per dimension. Fallback to multi-series `lineChart`. |
| 151.3 | **Radial/Gauge chart depth** | @visual | `visual_generator.py` | Full gauge config: target line, range bands (green/yellow/red), min/max, callout value formatting. Currently maps to basic `gauge` without bands. |
| 151.4 | **Histogram binning config** | @visual | `visual_generator.py`, `tmdl_generator.py` | Extract Tableau bin size + range → PBI `clusteredColumnChart` with auto-generated bin column (M-based `Number.RoundDown` step) and proper axis labels. |
| 151.5 | **Box-and-whisker encoding depth** | @visual | `visual_generator.py` | Extract quartile/median/outlier encoding from Tableau mark → PBI `boxAndWhisker` with proper Whisker/Median/Outlier data roles. Today falls back to scatter. |
| 151.6 | **Custom shape migration** | @extractor, @visual | `extract_tableau_data.py`, `pbip_generator.py` | Extract custom shape image files from `.twbx` ZIP → copy to `RegisteredResources/shapes/` → wire into `imageVisual` or `scatterChart` with `image` encoding. |
| 151.7 | **Tests** | @tester | `tests/test_advanced_visuals.py` | 40+ tests for each new visual type, encoding depth, fallback paths. |

---

### Sprint 152 — Map & Spatial Intelligence (v33.2.0)

**Owner:** @visual + @extractor + @wiring
**Goal:** Rich map visual migration — layers, zoom, center, base map style,
spatial data passthrough.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 152.1 | **Map zoom/center/base style** | @visual | `visual_generator.py` | Extract `<map-options>` zoom level, center lat/lon, base map style (normal/dark/satellite/streets) → PBI `map`/`filledMap` `mapControl` properties. |
| 152.2 | **Multi-layer map support** | @visual | `visual_generator.py` | Tableau mark layers (bubble, density, polygon overlay) → PBI `azureMap` with multiple layers config or `shapeMap` + `map` composite page. |
| 152.3 | **GeoJSON/TopoJSON passthrough** | @extractor | `geo_passthrough.py` | ✅ Already exists — extend to auto-register in `RegisteredResources/` and wire into `shapeMap` visual `shape.url` config. |
| 152.4 | **Spatial function migration notes** | @dax | `dax_converter.py` | MAKEPOINT/DISTANCE/BUFFER → structured migration note (not just `0`): include Python visual alternative template with geopy, suggest ArcGIS/Azure Maps visual. |
| 152.5 | **Custom geocoding passthrough** | @extractor | `extract_tableau_data.py` | Extract `<geocoding>` custom lat/lon/region mappings → emit as CSV lookup table + M query for PBI. |
| 152.6 | **Tests** | @tester | `tests/test_map_spatial.py` | 35+ tests: map config extraction, layer mapping, GeoJSON registration, geocoding lookup. |

---

### Sprint 153 — Rich Formatting & Interactivity (v33.3.0)

**Owner:** @visual + @extractor
**Goal:** Close formatting gaps — rich tooltips, animation, sparkline depth,
dynamic zone visibility completeness.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 153.1 | **Rich tooltip migration** | @visual | `pbip_generator.py` | Tableau HTML tooltip templates → PBI report page tooltips with multi-visual layouts. Extract tooltip worksheet refs, reconstruct as tooltip page with formatted textbox + mini-chart. |
| 153.2 | **Sparkline depth (area/bar)** | @visual | `visual_generator.py` | Extend sparkline config beyond lineChart: area sparklines (fill:true), bar sparklines (barChart micro-visual). Auto-detect sparkline type from Tableau mark encoding. |
| 153.3 | **Dynamic zone visibility** | @visual | `pbip_generator.py` | Complete dynamic zone visibility → PBI bookmark toggle groups. Map Tableau parameter-driven show/hide → PBI bookmark states with `objectVisibility` toggles + button actions. |
| 153.4 | **Animation/motion fallback** | @visual | `pbip_generator.py` | Tableau play-axis → PBI bookmark carousel with auto-advance suggestion. Generate N bookmarks (1 per time step) + navigation buttons + migration note. |
| 153.5 | **Legend position depth** | @visual | `visual_generator.py` | Handle all 8 Tableau legend positions → PBI legend position enum. Add legend title formatting (font, size, color) passthrough. |
| 153.6 | **Tests** | @tester | `tests/test_rich_formatting.py` | 35+ tests: tooltip pages, sparkline types, zone visibility bookmarks, animation bookmarks, legend formatting. |

---

### Sprint 154 — Table & Matrix Visual Depth (v33.4.0)

**Owner:** @visual + @semantic
**Goal:** Tables are the most-used Tableau visual — make them pixel-perfect.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 154.1 | **Column width preservation** | @visual | `visual_generator.py` | Extract Tableau column width from `<style-rule>` → PBI `tableEx` column width properties. |
| 154.2 | **Row banding depth** | @visual | `visual_generator.py` | Full banding config: alternating row color, header background, total row formatting, sub-total formatting. Currently basic `rowStyle.altBackColor`. |
| 154.3 | **Totals & subtotals** | @visual, @semantic | `visual_generator.py`, `tmdl_generator.py` | Extract `<totals>` (grand total, subtotal per dimension) → PBI matrix `subTotals` properties + `showTotals`/`showGrandTotal` config. |
| 154.4 | **Conditional icons in tables** | @visual | `visual_generator.py` | Tableau shape encoding in text marks → PBI conditional formatting icon sets. Map Tableau shape types (arrow, circle, triangle) to PBI icon set families. |
| 154.5 | **URL actions in tables** | @visual | `visual_generator.py` | Tableau URL actions on table cells → PBI `webUrl` column formatting with `[URL]` field binding. |
| 154.6 | **Tests** | @tester | `tests/test_table_matrix_depth.py` | 30+ tests: column widths, banding, totals, conditional icons, URL columns. |

---

## Stream B — Datasource & Connector Breadth

### Sprint 155 — Cloud & SaaS Connectors (v33.5.0)

**Owner:** @wiring + @extractor
**Goal:** Add 8 high-demand enterprise connectors that are currently missing
or have placeholder M queries.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 155.1 | **ServiceNow** | @wiring | `m_query_builder.py` | `OData.Feed("https://instance.service-now.com/api/now/table/TABLE")` with token auth placeholder. ServiceNow is top-5 Tableau connector by enterprise usage. |
| 155.2 | **SAP HANA depth** | @wiring | `m_query_builder.py` | Full `SapHana.Database()` with schema/view navigation, MDX passthrough for BW cubes, column type mapping (NVARCHAR→Text, DECIMAL→Decimal). |
| 155.3 | **Databricks Unity Catalog** | @wiring | `m_query_builder.py` | `Databricks.Catalogs()` with catalog/schema/table navigation. Currently basic `Databricks.Query()` — extend with Unity Catalog hierarchy. |
| 155.4 | **Amazon Redshift depth** | @wiring | `m_query_builder.py` | `AmazonRedshift.Database()` with schema navigation, Spectrum external tables. Currently basic connection. |
| 155.5 | **Denodo / Data Virtualization** | @wiring | `m_query_builder.py` | ODBC-based connector template with `Odbc.DataSource()` and Denodo-specific connection string format. |
| 155.6 | **Essbase / Hyperion** | @wiring | `m_query_builder.py` | XMLA/ODBC bridge template. Mark as YELLOW in assessment (requires gateway + XMLA provider). |
| 155.7 | **Splunk** | @wiring | `m_query_builder.py` | `Web.Contents()` REST API template hitting Splunk search endpoint with SPL query passthrough. |
| 155.8 | **Connector assessment integration** | @assessor | `assessment.py` | Update connector RED/YELLOW/GREEN classification for all new connectors. |
| 155.9 | **Tests** | @tester | `tests/test_cloud_connectors.py` | 40+ tests: one per new connector + edge cases (auth templates, custom SQL, schema navigation). |

---

### Sprint 156 — Connection String Intelligence (v33.6.0)

**Owner:** @wiring + @semantic + @deployer
**Goal:** Smart connection string rewriting for migration (Tableau connection
metadata → PBI M query parameters + gateway config).

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 156.1 | **Connection string parser** | @wiring | new `powerbi_import/connection_rewriter.py` | Parse Tableau connection XML → structured `ConnectionInfo` (server, port, database, schema, auth_type, ssl, warehouse for Snowflake, project for BigQuery). Support all 42 connectors. |
| 156.2 | **Environment-based rewriting** | @wiring | `connection_rewriter.py` | Config-driven server name replacement: `--connection-map mapping.json` → rewrite `prod-tableau-db.corp` to `prod-pbi-db.corp` in all M queries. |
| 156.3 | **Gateway config depth** | @deployer | `gateway_config.py` | Full on-premises data gateway config: connection type, server, database, auth method, encrypted credential placeholder. Generate PowerShell for `Set-DataGatewayCluster` binding. |
| 156.4 | **OAuth template generation** | @deployer | `gateway_config.py` | Per-connector OAuth redirect template: Google Sheets (GCS OAuth), Salesforce (SF OAuth), Snowflake (SSO), Databricks (PAT/OAuth). |
| 156.5 | **Connection drift reporting** | @assessor | `schema_drift.py` | Extend `detect_connection_drift()` to cover all 42 connector types with connector-specific field comparison (e.g., Snowflake warehouse/role, BigQuery billing project). |
| 156.6 | **Tests** | @tester | `tests/test_connection_rewriter.py` | 45+ tests: parse all connector types, rewriting rules, gateway scripts, OAuth templates, drift detection. |

---

### Sprint 157 — Hyper & Extract Data Completeness (v33.7.0)

**Owner:** @extractor + @wiring
**Goal:** Make `.hyper` data extraction production-grade for all edge cases.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 157.1 | **Multi-table Hyper** | @extractor | `hyper_reader.py` | Handle `.hyper` files with multiple tables across schemas (`Extract`, `public`, `stg`). Generate one M partition per table with proper schema-qualified names. |
| 157.2 | **Large Hyper streaming** | @extractor | `hyper_reader.py` | Stream rows in chunks for `.hyper` > 100MB. Emit CSV + `Csv.Document()` instead of `#table()` for files > 10,000 rows. |
| 157.3 | **Hyper type completeness** | @extractor | `hyper_reader.py` | Map all 28 Hyper SQL types to PBI types. Add: INTERVAL, GEOGRAPHY, OID, BYTES, SMALL_INT. Currently 20/28 mapped. |
| 157.4 | **TDE → Hyper upgrade path** | @extractor | `extract_tableau_data.py` | Detect `.tde` in `.twbx` → structured error with exact steps to upgrade (open in Tableau Desktop → re-extract → re-save). Include assessment category. |
| 157.5 | **Extract filter preservation** | @wiring | `m_query_builder.py` | Tableau extract filters (date range, top-N, dimension filter) → M `Table.SelectRows()` step injected into partition query. Currently only datasource-level filters; extract-level filters are lost. |
| 157.6 | **Tests** | @tester | `tests/test_hyper_extract_depth.py` | 35+ tests: multi-table, streaming, type mapping, TDE detection, extract filters. |

---

## Stream C — DAX & Formula Conversion Completeness

### Sprint 158 — Spatial & Regex Gap Closure (v33.8.0)

**Owner:** @dax + @visual
**Goal:** Replace every `0` / `BLANK()` placeholder with actionable output.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 158.1 | **Spatial → Python visual** | @dax, @visual | `dax_converter.py`, `visual_generator.py` | MAKEPOINT/DISTANCE/BUFFER → generate complete Python `scriptVisual` with `matplotlib` + `geopy` template (not just `0`). Include `import geopy; ...` script body, bind lat/lon input columns. |
| 158.2 | **HEXBINX/HEXBINY → M column** | @dax, @wiring | `dax_converter.py`, `calc_column_utils.py` | Hex-binning formula → M calculated column with `Number.RoundDown` + hex offset math. Approximation documented. |
| 158.3 | **COLLECT → aggregation note** | @dax | `dax_converter.py` | COLLECT → `CONCATENATEX('Table', [Field], ", ")` as string aggregation approximation (loses geometry semantics but preserves the value list). |
| 158.4 | **REGEXP deep patterns** | @dax | `dax_converter.py` | Extend REGEXP_EXTRACT/REPLACE for 10 common regex patterns: email extraction, phone number, URL parsing, date extraction, IP address. Pattern library with pre-built DAX equivalents. |
| 158.5 | **SPLIT full support** | @dax | `dax_converter.py` | SPLIT(string, delim, N) → `PATHITEM(SUBSTITUTE(string, delim, "\|"), N)` for all argument counts. Handle edge cases: negative index (PATHITEMREVERSE), 2-arg default. |
| 158.6 | **Tests** | @tester | `tests/test_spatial_regex_dax.py` | 40+ tests: spatial Python visuals, hex-bin M columns, COLLECT approximation, regex pattern library, SPLIT edge cases. |

---

### Sprint 159 — Table Calculation Depth (v33.9.0)

**Owner:** @dax + @semantic
**Goal:** Perfect table calculation conversion — the #1 source of semantic
drift in real-world migrations.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 159.1 | **WINDOW_PERCENTILE** | @dax | `dax_converter.py` | `WINDOW_PERCENTILE(expr, N)` → `PERCENTILEX.INC` with `CALCULATE` + `ALLEXCEPT` window context. |
| 159.2 | **RUNNING with partitions** | @dax | `dax_converter.py` | `RUNNING_SUM` partitioned by dimension → `CALCULATE(SUM, FILTER(ALLSELECTED(dim)))` with proper partition field resolution. Verify `compute_using` parameter handling for all RUNNING_* variants. |
| 159.3 | **FIRST/LAST/INDEX depth** | @dax | `dax_converter.py` | `FIRST()` → `ROWNUMBER() - 1` (0-based offset from current row). `LAST()` → `COUNTROWS(ALLSELECTED()) - ROWNUMBER()`. Verify with nested addressing (Across/Down). |
| 159.4 | **Table calc addressing** | @dax | `dax_converter.py` | Complete addressing direction extraction: `compute-using` (Across) → ALLEXCEPT on non-compute dims; `addressing` (Down) → explicit dimension list in CALCULATE filter. Test with `Table (across)` and `Pane (down then across)` scenarios. |
| 159.5 | **Nested table calculations** | @dax | `dax_converter.py` | Handle `RUNNING_SUM(RANK(...))` → nested CALCULATE with proper window context inheritance. Detect and warn on unsupported nesting depth (>2 levels). |
| 159.6 | **Tests** | @tester | `tests/test_table_calc_depth.py` | 45+ tests: WINDOW_PERCENTILE, partitioned RUNNING, FIRST/LAST, addressing modes, nested table calcs. |

---

### Sprint 160 — LOD & Security Expression Hardening (v33.10.0)

**Owner:** @dax + @semantic
**Goal:** LOD expressions are the second-highest source of semantic drift —
make every variant correct.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 160.1 | **Nested LOD** | @dax | `dax_converter.py` | `{FIXED [A] : SUM({FIXED [A],[B] : COUNT([C])})}` → nested CALCULATE with correct ALLEXCEPT nesting. Currently inner LOD is flattened. |
| 160.2 | **LOD with INCLUDE + dimension** | @dax | `dax_converter.py` | `{INCLUDE [Dim] : AGG}` must add the dimension to filter context (not remove it). Verify CALCULATE generates the correct pattern. |
| 160.3 | **LOD with EXCLUDE + multiple dims** | @dax | `dax_converter.py` | `{EXCLUDE [D1],[D2] : AGG}` → CALCULATE(AGG, REMOVEFILTERS('T'[D1], 'T'[D2])). Currently only handles single-dim EXCLUDE. |
| 160.4 | **LOD with date truncation** | @dax | `dax_converter.py` | `{FIXED DATETRUNC('month',[Date]) : SUM([Sales])}` → CALCULATE with STARTOFMONTH context. Detect DATETRUNC inside LOD dimension and transform. |
| 160.5 | **ISMEMBEROF expansion** | @dax, @semantic | `dax_converter.py`, `tmdl_generator.py` | `ISMEMBEROF("Managers")` → RLS role `Managers` with `tablePermission` on the security table. Currently generates `TRUE()` — needs actual role wiring. |
| 160.6 | **USERDOMAIN alternative** | @dax | `dax_converter.py` | `USERDOMAIN()` → `LEFT(USERPRINCIPALNAME(), SEARCH("@", USERPRINCIPALNAME()) - 1)` — extract domain prefix from UPN. Better than current empty string. |
| 160.7 | **Tests** | @tester | `tests/test_lod_security_depth.py` | 40+ tests: nested LOD, multi-dim EXCLUDE, LOD+DATETRUNC, ISMEMBEROF RLS, USERDOMAIN. |

---

## Stream D — Tableau Server & Cloud Integration

### Sprint 161 — Server Discovery & Metadata (v34.1.0)

**Owner:** @extractor + @assessor
**Goal:** Deep server-level metadata extraction for enterprise migration
planning — go beyond "list & download" to full inventory with dependencies.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 161.1 | **Workbook dependency graph** | @extractor | `server_client.py` | New `get_workbook_downstream_views()` and `get_datasource_workbooks()` endpoints → build dependency graph: datasource → workbook → view. Output as `server_dependency_graph.json`. |
| 161.2 | **Published datasource resolution** | @extractor | `server_client.py`, `extract_tableau_data.py` | When a workbook references a published datasource, auto-download the `.tdsx` and merge its schema into the extraction. Currently left as an unresolved reference. |
| 161.3 | **Usage statistics** | @extractor | `server_client.py` | New `get_view_usage_stats()` endpoint → extract view count, last accessed date, user count per workbook. Feed into server assessment for migration prioritization. |
| 161.4 | **Site permissions inventory** | @extractor | `server_client.py` | New `get_workbook_permissions()`, `get_project_permissions()` → extract permission ACLs for RLS/workspace mapping in PBI. |
| 161.5 | **Data quality warnings** | @extractor | `server_client.py` | New `get_data_quality_warnings()` → extract certification status, data quality warnings, sensitivity labels. Map to PBI endorsement (`promoted`/`certified`). |
| 161.6 | **Server metadata HTML report** | @assessor | `server_assessment.py` | New "Server Inventory" tab in portfolio assessment: dependency graph visualization, usage heatmap, permission summary, certification status. |
| 161.7 | **Tests** | @tester | `tests/test_server_discovery.py` | 35+ tests: dependency graph, published DS resolution, usage stats, permissions, quality warnings. |

---

### Sprint 162 — Tableau Cloud & OAuth Depth (v34.2.0)

**Owner:** @extractor + @deployer
**Goal:** Full Tableau Cloud support — OAuth, SSO, embedded credentials,
and cloud-specific API features.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 162.1 | **OAuth / JWT auth** | @extractor | `server_client.py` | Add `auth_method='jwt'` using Connected App JWT tokens (Tableau Cloud). Currently PAT + password only. |
| 162.2 | **Tableau Cloud site discovery** | @extractor | `server_client.py` | Auto-detect Tableau Cloud vs Server from URL pattern (`*.online.tableau.com`). Adjust API version to latest Cloud-supported (`3.21+`). |
| 162.3 | **Embedded credentials mapping** | @deployer | `gateway_config.py` | Extract embedded credential types from Tableau Server → generate PBI credential template per datasource (OAuth redirect, username/password, service account, API key). |
| 162.4 | **Tableau Cloud metadata API** | @extractor | `server_client.py` | New `get_metadata_graphql()` → query Tableau Metadata API (GraphQL) for table lineage, column-level lineage, database connections. Richer than REST. |
| 162.5 | **Tableau Cloud content migration** | @extractor | `server_client.py` | `migrate_from_cloud()` orchestrator: site scan → prioritize by usage → batch download → migrate → deploy to Fabric/PBI Service. CLI: `--cloud-migrate`. |
| 162.6 | **Tests** | @tester | `tests/test_tableau_cloud.py` | 30+ tests: JWT auth, Cloud detection, embedded credentials, GraphQL metadata, cloud migration flow. |

---

### Sprint 163 — Schedule & Subscription Migration (v34.3.0)

**Owner:** @extractor + @deployer
**Goal:** Migrate Tableau Server schedules, subscriptions, and alerts to
PBI Service equivalents.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 163.1 | **Extract refresh → PBI refresh** | @deployer | `refresh_generator.py` | ✅ Partially exists — extend to cover all Tableau schedule types: hourly/daily/weekly/monthly cron expressions → PBI refresh schedule API format. Handle timezone conversion. |
| 163.2 | **Subscriptions → PBI alerts** | @deployer | new `powerbi_import/subscription_migrator.py` | Tableau subscriptions (email on refresh/failure) → PBI dataset refresh failure alerts + email notification rules. Map subscriber list to Azure AD UPNs. |
| 163.3 | **Tableau alerts → PBI data alerts** | @deployer | `alerts_generator.py` | ✅ Partially exists — extend for Tableau Server alert conditions (threshold on measure, email on trigger) → PBI data-driven alert rules with tile binding. |
| 163.4 | **Schedule conflict detection** | @assessor | `server_assessment.py` | Detect refresh schedule conflicts during batch migration: overlapping schedules, gateway capacity limits, PBI Pro vs Premium refresh limits. |
| 163.5 | **Subscription mapping report** | @deployer | `subscription_migrator.py` | HTML report showing Tableau subscription → PBI alert mapping, unmapped subscribers (no Azure AD match), schedule conflicts. |
| 163.6 | **Tests** | @tester | `tests/test_schedule_subscription.py` | 35+ tests: cron conversion, timezone handling, subscriber mapping, alert migration, conflict detection. |

---

## Stream E — Test Coverage & Quality Depth

### Sprint 164 — Negative & Edge-Case Test Suite (v34.4.0)

**Owner:** @tester
**Goal:** Harden the test suite with negative paths, boundary conditions,
and adversarial inputs.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 164.1 | **Malformed XML corpus** | @tester | `tests/fixtures/malformed/` | 30 malformed `.twb` snippets: truncated XML, invalid UTF-8, circular references, missing required elements, 10MB+ single element, null bytes in field names. |
| 164.2 | **DAX boundary tests** | @tester | `tests/test_dax_boundary.py` | 50+ tests: empty strings, 10,000-char formulas, 20-level nested IF, every operator with NULL operands, Unicode function names, reserved word conflicts. |
| 164.3 | **M query boundary tests** | @tester | `tests/test_m_boundary.py` | 40+ tests: 1,000-column tables, column names with every special char, empty partitions, circular step references, 50-step chains. |
| 164.4 | **Connector auth failure paths** | @tester | `tests/test_connector_failures.py` | 25+ tests: connection timeout, invalid credentials, expired tokens, SSL cert errors, DNS resolution failure — verify graceful degradation. |
| 164.5 | **Large workbook stress** | @tester | `tests/test_stress.py` | 1,000-measure, 50-page, 200-visual workbook stress test. Assert: <5min, <4GB RAM, no OOM, all visuals generated. |
| 164.6 | **Tests** | @tester | various | Target: **+200 tests** in this sprint alone. |

---

### Sprint 165 — Property-Based & Fuzzing Expansion (v34.5.0)

**Owner:** @tester + @dax
**Goal:** Expand property-based testing to catch regressions that example-based
tests miss.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 165.1 | **DAX round-trip property** | @tester | `tests/test_dax_properties.py` | For every Tableau formula: `convert(formula)` always returns balanced brackets, valid function names, no empty `CALCULATE()` calls. 500 iterations. |
| 165.2 | **M query well-formedness** | @tester | `tests/test_m_properties.py` | Every generated M partition: balanced `let/in`, no dangling `{prev}`, all step names unique, `Source` step exists. 500 iterations. |
| 165.3 | **TMDL structural invariants** | @tester | `tests/test_tmdl_properties.py` | Every generated model: no duplicate table names, no duplicate column names within table, all relationship endpoints exist, no circular relationships. 200 iterations. |
| 165.4 | **PBIR structural invariants** | @tester | `tests/test_pbir_properties.py` | Every generated report: all visual query fields exist in model, no duplicate visual names on page, all bookmark targets exist, page order is unique. 200 iterations. |
| 165.5 | **Fuzzing harness** | @tester | `tests/test_fuzz.py` | Extend existing fuzz tests: randomized XML element injection, randomized DAX formula mutation, randomized M step permutation. Assert no crash (only graceful warnings). |
| 165.6 | **Tests** | @tester | various | Target: **+150 tests** (property-based + fuzz). |

---

### Sprint 166 — Real-World Corpus Expansion (v34.6.0)

**Owner:** @tester + @assessor
**Goal:** Expand the real-world test corpus from 26 to 50+ workbooks covering
every major industry pattern.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 166.1 | **Industry workbook fixtures** | @tester | `tests/fixtures/real_world/` | Add 25 new fixture workbooks: Healthcare (HL7 dashboard), Finance (P&L waterfall), Retail (market basket), Manufacturing (OEE), Logistics (route map), Education (enrollment), Government (budget), Media (audience), Telecom (network), Energy (smart grid). |
| 166.2 | **Golden file baselines** | @tester | `tests/fixtures/golden/` | Per-workbook golden output: expected tables, measures, relationships, visual count, page count. Regression tests compare against golden files. |
| 166.3 | **Migration fidelity scoring** | @assessor | `assessment.py` | Per-workbook fidelity score: (migrated fields / total fields) × weight. Track trend across versions. |
| 166.4 | **Corpus coverage report** | @assessor | `docs/CORPUS_COVERAGE.md` | Auto-generated doc: per-workbook status (GREEN/YELLOW/RED), feature coverage matrix, regression trend. |
| 166.5 | **Tests** | @tester | `tests/test_real_world_e2e.py` | Extend E2E suite to 50+ workbooks. Target: **+250 tests**. |

---

## Stream F — Cross-Cutting & Infrastructure

### Sprint 167 — Migration Planner (v34.7.0)

**Owner:** @assessor + @deployer
**Goal:** Enterprise migration planner — from Tableau Server inventory to
PBI workspace structure with effort estimates and wave assignments.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 167.1 | **Migration plan generator** | @assessor | new `powerbi_import/migration_planner.py` | Input: server inventory JSON. Output: migration plan with wave assignments (by complexity), effort estimates (by visual/measure/connector count), workspace mapping (Tableau project → PBI workspace). |
| 167.2 | **Dependency-aware wave planning** | @assessor | `migration_planner.py` | Workbooks sharing published datasources must be in same wave. Dependency graph from Sprint 161 feeds wave assignment. |
| 167.3 | **RLS/permission mapping** | @deployer | `migration_planner.py` | Tableau project permissions → PBI workspace roles. Tableau user/group → Azure AD security group mapping template. |
| 167.4 | **Effort estimation model** | @assessor | `migration_planner.py` | Weighted formula: `effort = (visuals × 0.3) + (measures × 0.4) + (connectors × 0.2) + (RLS_roles × 0.1)`. Calibrated against actual migration times from telemetry. |
| 167.5 | **Migration plan HTML dashboard** | @assessor | `migration_planner.py` | Interactive HTML: wave timeline (Gantt), workbook cards with effort bars, dependency graph (Mermaid), permission mapping table. |
| 167.6 | **Tests** | @tester | `tests/test_migration_planner.py` | 35+ tests: wave assignment, effort estimation, permission mapping, dependency resolution, HTML generation. |

---

### Sprint 168 — Incremental & Live Sync Depth (v34.8.0)

**Owner:** @orchestrator + @semantic
**Goal:** Make `--incremental` production-grade — preserve user edits while
updating migrated content.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 168.1 | **Three-way merge depth** | @semantic | `incremental.py` | ✅ Exists — extend to handle: new tables added in Tableau, deleted tables, renamed columns, moved measures between tables. Currently handles simple column/measure additions. |
| 168.2 | **User edit fingerprinting** | @semantic | `incremental.py` | Detect which artifacts were manually edited by the user (file hash comparison) → preserve those files, only update auto-generated ones. |
| 168.3 | **Diff report** | @orchestrator | `incremental.py` | Per-file diff report: what changed, what was preserved, what conflicts need manual resolution. HTML format with side-by-side comparison. |
| 168.4 | **Conflict resolution rules** | @semantic | `incremental.py` | Configurable merge strategy: `--incremental-strategy theirs\|ours\|manual`. Default: preserve user edits (`theirs`). |
| 168.5 | **Continuous sync mode** | @orchestrator | `migrate.py` | `--watch` mode: monitor `.twbx` file changes, auto-re-migrate on save. Useful during parallel Tableau/PBI development. |
| 168.6 | **Tests** | @tester | `tests/test_incremental_depth.py` | 35+ tests: three-way merge scenarios, user edit preservation, diff report, conflict resolution, watch mode. |

---

### Sprint 169 — Documentation & Developer Experience (v34.9.0)

**Owner:** @orchestrator
**Goal:** Comprehensive docs refresh for v33-v34. Make the tool self-documenting.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 169.1 | **Connector compatibility matrix** | @orchestrator | `docs/CONNECTOR_MATRIX.md` | Auto-generated matrix: 50 connectors × (supported / auth type / gateway required / known issues). |
| 169.2 | **Visual mapping gallery** | @orchestrator | `docs/VISUAL_GALLERY.md` | Side-by-side screenshots or descriptions: Tableau visual → PBI visual for all 125 types. Include approximation notes. |
| 169.3 | **DAX conversion reference update** | @orchestrator | `docs/TABLEAU_TO_DAX_REFERENCE.md` | Update for all new conversions (spatial, regex depth, table calc depth, LOD nesting). |
| 169.4 | **Enterprise migration playbook** | @orchestrator | `docs/ENTERPRISE_GUIDE.md` | Update with: server discovery workflow, wave planning, permission mapping, schedule migration, post-migration validation checklist. |
| 169.5 | **API reference** | @orchestrator | `docs/API_REFERENCE.md` | Auto-generated from docstrings: every public function with parameters, return types, examples. |
| 169.6 | **Migration checklist v2** | @orchestrator | `docs/MIGRATION_CHECKLIST.md` | Updated pre/during/post migration checklist with all new capabilities (connector rewriting, schedule migration, incremental sync). |

---

### Sprint 170 — v34.0.0 Release & Confidence Score (v34.10.0)

**Owner:** All agents
**Goal:** Release milestone — verify all targets met, compute final
Migration Completeness Score.

| # | Item | Owner | File(s) | Details |
|---|------|-------|---------|---------|
| 170.1 | **Version bump** | @orchestrator | `pyproject.toml`, `CHANGELOG.md` | `32.2.0` → `34.0.0`. Document all 20 sprints (151–170). |
| 170.2 | **Full regression sweep** | @tester | `tests/` | Target: **9,500+ tests**, 0 failures, 97%+ coverage. |
| 170.3 | **Migration Completeness Score** | @assessor | `docs/GAP_ANALYSIS.md` | Recompute all 5 axes. Target: **≥ 98 / 100**. |
| 170.4 | **Real-world corpus validation** | @tester | `tests/test_real_world_e2e.py` | All 50+ workbooks migrate cleanly. Zero-Touch Open Rate: **≥ 99 %**. |
| 170.5 | **ROADMAP update** | @orchestrator | `docs/ZERO_ERROR_ROADMAP.md` | Mark all sprints as shipped, update progress tracker. |

---

## v34.0.0 Success Criteria

| Metric | Target | Weight |
|--------|--------|--------|
| Visual types mapped | ≥ 125 (incl. custom visual GUIDs) | 25 % |
| Connectors supported | ≥ 45 (enterprise + cloud + SaaS) | 20 % |
| DAX conversions | ≥ 195 (incl. spatial Python, deep table calcs) | 25 % |
| Server/Cloud endpoints | ≥ 25 (incl. GraphQL, dependency graph, permissions) | 15 % |
| Tests passing | ≥ 9,500 | 15 % |
| Zero-Touch Open Rate | ≥ 99 % on 50-workbook corpus | — |
| Coverage | ≥ 97 % line coverage | — |

---

## Progress Tracker (Sprints 151–170)

| Sprint | Version | Stream | Theme | Status |
|--------|---------|--------|-------|--------|
| 151 | v33.1.0 | A | Advanced Visual Types | ⬚ Not started |
| 152 | v33.2.0 | A | Map & Spatial Intelligence | ⬚ Not started |
| 153 | v33.3.0 | A | Rich Formatting & Interactivity | ⬚ Not started |
| 154 | v33.4.0 | A | Table & Matrix Depth | ⬚ Not started |
| 155 | v33.5.0 | B | Cloud & SaaS Connectors | ⬚ Not started |
| 156 | v33.6.0 | B | Connection String Intelligence | ⬚ Not started |
| 157 | v33.7.0 | B | Hyper & Extract Completeness | ⬚ Not started |
| 158 | v33.8.0 | C | Spatial & Regex Gap Closure | ⬚ Not started |
| 159 | v33.9.0 | C | Table Calculation Depth | ⬚ Not started |
| 160 | v33.10.0 | C | LOD & Security Hardening | ⬚ Not started |
| 161 | v34.1.0 | D | Server Discovery & Metadata | ⬚ Not started |
| 162 | v34.2.0 | D | Tableau Cloud & OAuth | ⬚ Not started |
| 163 | v34.3.0 | D | Schedule & Subscription Migration | ⬚ Not started |
| 164 | v34.4.0 | E | Negative & Edge-Case Tests | ⬚ Not started |
| 165 | v34.5.0 | E | Property-Based & Fuzzing | ⬚ Not started |
| 166 | v34.6.0 | E | Real-World Corpus (50+) | ⬚ Not started |
| 167 | v34.7.0 | F | Migration Planner | ⬚ Not started |
| 168 | v34.8.0 | F | Incremental & Live Sync | ⬚ Not started |
| 169 | v34.9.0 | F | Documentation & DX | ⬚ Not started |
| 170 | v34.10.0 | — | v34.0.0 Release | ⬚ Not started |
