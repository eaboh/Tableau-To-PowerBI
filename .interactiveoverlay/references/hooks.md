# Hook Reference — Interactive Migration

Detailed specification for all 22 hooks across 6 phases.

---

## Phase 1: Source & Readiness

### hook:load

| Field | Value |
|-------|-------|
| **Subcommand** | `load <path>` |
| **Inputs** | Path to `.twb` or `.twbx` file |
| **Outputs** | Object counts for 17 extracted types |
| **Session effect** | Creates session, stores workbook path |
| **Decision prompt** | Confirm source file, review object counts |
| **Prerequisite** | None (first hook) |

**Output fields:**
- `workbook`: Filename
- `object_counts`: Dict of type → count (worksheets, dashboards, datasources, calculations, parameters, filters, stories, actions, sets, groups, bins, hierarchies, sort_orders, aliases, custom_sql, user_filters, hyper_files)
- `total_objects`: Sum of all counts

---

### hook:assess

| Field | Value |
|-------|-------|
| **Subcommand** | `assess` |
| **Inputs** | None (uses loaded session) |
| **Outputs** | 9-category readiness report with overall grade |
| **Session effect** | Stores assessment results |
| **Decision prompt** | Go/no-go decision based on grade and findings |
| **Prerequisite** | `load` |

**Assessment categories:**
1. Datasource compatibility
2. Calculation complexity
3. Visual type coverage
4. Filter migration support
5. Data model complexity
6. Interactivity (actions, parameters)
7. Extract/data considerations
8. Scope (size, complexity)
9. Connection string audit

**Severity levels:** pass, info, warn, fail

---

### hook:strategy

| Field | Value |
|-------|-------|
| **Subcommand** | `strategy` |
| **Inputs** | None (uses loaded session) |
| **Outputs** | Recommended mode + signal breakdown |
| **Session effect** | None |
| **Decision prompt** | Accept or override data mode |
| **Prerequisite** | `load` |

**Decision signals (7):**
- Connector type (PQ-friendly vs DQ-friendly)
- Table count (≤5 → Import, >5 → DQ)
- Column count (≤50 → Import, >50 → DQ)
- Custom SQL presence
- Formula complexity (LOD, table calcs)
- Calculated column count
- Prep flow transforms

**Modes:** Import, DirectQuery, Composite

---

## Phase 2: Extraction Review

### hook:datasources

| Field | Value |
|-------|-------|
| **Subcommand** | `datasources` |
| **Outputs** | Per-datasource: name, connection type, tables with column/relationship counts |
| **Decision prompt** | Confirm connector mappings |
| **Prerequisite** | `load` |

---

### hook:calculations

| Field | Value |
|-------|-------|
| **Subcommand** | `calculations` |
| **Outputs** | Per-calc: name, Tableau formula, role (measure/dimension), type, datatype |
| **Decision prompt** | Reclassify measure ↔ calc column, flag for manual review |
| **Prerequisite** | `load` |

**Classification rules:**
- Has aggregation (SUM, COUNT...) → measure
- No aggregation + has column references → calculated column
- No aggregation + no column refs → measure (formula-only)

---

### hook:parameters

| Field | Value |
|-------|-------|
| **Subcommand** | `parameters` |
| **Outputs** | Per-parameter: name, domain_type (range/list/any), current value, allowable values |
| **Decision prompt** | Adjust parameter handling or default values |
| **Prerequisite** | `load` |

---

### hook:filters

| Field | Value |
|-------|-------|
| **Subcommand** | `filters` |
| **Outputs** | Per-filter: field, type, values |
| **Decision prompt** | Include/exclude filters from migration |
| **Prerequisite** | `load` |

---

### hook:worksheets

| Field | Value |
|-------|-------|
| **Subcommand** | `worksheets` |
| **Outputs** | Per-worksheet: name, mark_type, field_count, filter_count |
| **Decision prompt** | Preview which visual types will be mapped |
| **Prerequisite** | `load` |

---

### hook:dashboards

| Field | Value |
|-------|-------|
| **Subcommand** | `dashboards` |
| **Outputs** | Per-dashboard: name, object count, object types |
| **Decision prompt** | Confirm page structure |
| **Prerequisite** | `load` |

---

### hook:security

| Field | Value |
|-------|-------|
| **Subcommand** | `security` |
| **Outputs** | User filter rules and RLS role candidates |
| **Decision prompt** | Approve/edit role mappings |
| **Prerequisite** | `load` |

---

## Phase 3: Conversion

### hook:dax-preview

| Field | Value |
|-------|-------|
| **Subcommand** | `dax-preview` |
| **Outputs** | Per-calc: Tableau formula, DAX formula, status (exact/approximated/overridden) |
| **Decision prompt** | Edit approximated formulas |
| **Prerequisite** | `load` |

**Status meanings:**
- **exact**: High-confidence auto-conversion, no action needed
- **approximated**: Placeholder or best-effort conversion, review recommended
- **overridden**: User has manually edited this formula

---

### hook:dax-optimize

| Field | Value |
|-------|-------|
| **Subcommand** | `dax-optimize` |
| **Outputs** | Per-optimization: name, original, optimized, rules applied |
| **Decision prompt** | Accept/reject each optimization rule |
| **Prerequisite** | `dax-preview` |

**Optimization rules:**
- `isblank_coalesce`: IF(ISBLANK(x), 0, x) → COALESCE(x, 0)
- `nested_if_to_switch`: Nested IF chains → SWITCH
- `redundant_calculate`: CALCULATE(CALCULATE(...)) → single CALCULATE
- `constant_fold`: Constant expression evaluation
- `simplify_sumx`: Single-column SUMX → SUM
- `trim_whitespace`: Clean up formatting

---

### hook:edit-dax

| Field | Value |
|-------|-------|
| **Subcommand** | `edit-dax <name> <formula>` |
| **Inputs** | Measure name, new DAX formula |
| **Outputs** | Confirmation + all active overrides |
| **Decision prompt** | None (action hook) |
| **Prerequisite** | `load` |

Can be called multiple times. Each call persists in the session.

---

### hook:m-query

| Field | Value |
|-------|-------|
| **Subcommand** | `m-query` |
| **Outputs** | Per-table: table name, datasource name, connection type, M expression |
| **Decision prompt** | Review connection strings and transforms |
| **Prerequisite** | `load` |

---

### hook:visual-mapping

| Field | Value |
|-------|-------|
| **Subcommand** | `visual-mapping` |
| **Outputs** | Per-worksheet: Tableau mark → PBI visual type, field count, override status |
| **Decision prompt** | Override visual types |
| **Prerequisite** | `load` |

See `references/visual-type-catalog.md` for the full 118-type mapping table.

---

### hook:calendar

| Field | Value |
|-------|-------|
| **Subcommand** | `calendar --start-year N --end-year N --culture X --languages X` |
| **Inputs** | Calendar config values |
| **Outputs** | Updated config |
| **Decision prompt** | Adjust date range, locale, languages |
| **Prerequisite** | `load` |

---

## Phase 4: Generation

### hook:semantic-model

| Field | Value |
|-------|-------|
| **Subcommand** | `semantic-model` |
| **Outputs** | Model summary: tables, measures, calc columns, parameters, hierarchies, RLS, overrides |
| **Decision prompt** | Final review before write |
| **Prerequisite** | `load` |

---

### hook:report-layout

| Field | Value |
|-------|-------|
| **Subcommand** | `report-layout` |
| **Outputs** | Per-page: visuals, slicers, text boxes, images; orphan worksheets |
| **Decision prompt** | Adjust page order |
| **Prerequisite** | `load` |

---

### hook:generate

| Field | Value |
|-------|-------|
| **Subcommand** | `generate` |
| **Outputs** | Generation summary: output_dir, tables, measures, pages |
| **Decision prompt** | Confirm output dir and format |
| **Prerequisite** | `load` + all desired overrides applied |

---

## Phase 5: Validation

### hook:validate

| Field | Value |
|-------|-------|
| **Subcommand** | `validate` |
| **Outputs** | Validation errors, warnings, passes |
| **Decision prompt** | Fix errors, accept warnings |
| **Prerequisite** | `generate` |

---

### hook:compare

| Field | Value |
|-------|-------|
| **Subcommand** | `compare` |
| **Outputs** | Source vs generated object counts, fidelity notes |
| **Decision prompt** | Review gaps |
| **Prerequisite** | `generate` |

---

## Phase 6: Deploy

### hook:deploy-config

| Field | Value |
|-------|-------|
| **Subcommand** | `deploy-config --workspace-id <id>` |
| **Outputs** | Deploy config |
| **Decision prompt** | Set workspace ID, auth, gateway |
| **Prerequisite** | `generate` |

---

### hook:deploy-execute

| Field | Value |
|-------|-------|
| **Subcommand** | `deploy-execute` |
| **Outputs** | Deployment result |
| **Decision prompt** | Confirm deployment, trigger refresh |
| **Prerequisite** | `deploy-config` |

---

## Session Management Hooks

### status

| Field | Value |
|-------|-------|
| **Subcommand** | `status` |
| **Outputs** | Current phase, completed hooks, override counts, config |

### reset

| Field | Value |
|-------|-------|
| **Subcommand** | `reset` |
| **Outputs** | Confirmation message |
| **Effect** | Deletes `.migration_session.json` |
