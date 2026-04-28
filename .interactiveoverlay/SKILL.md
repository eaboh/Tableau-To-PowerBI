---
description: "Guided, conversational Tableau → Power BI migration. Walks users through 22 hook points across 6 phases with review and override at every step. USE FOR: migrate tableau, interactive migration, guided migration, step-by-step migration, tableau to power bi walkthrough. DO NOT USE FOR: batch migration, automated migration (use `python migrate.py` directly)."
applyTo: "**"
---

# Interactive Migration Skill

Guided, conversational Tableau → Power BI migration with 22 hook points.

## Overview

This skill transforms the automated migration into a **conversational workflow** where Copilot pauses at each stage to present results, ask for user review, and accept overrides before proceeding.

**Runner script**: `.interactiveoverlay/interactive_runner.py`
**Session state**: `.migration_session.json` in the output directory
**Reference docs**: `.interactiveoverlay/references/`

---

## How to Run Hooks

Every hook is a subcommand of the runner script. Run in terminal:

```
python .interactiveoverlay/interactive_runner.py <hook> [args] --output-dir <dir>
```

All hooks emit structured JSON with `{ "hook": "...", "status": "ok"|"error", "result": {...} }`.

---

## Conversational Workflow — 6 Phases, 22 Hooks

Follow this sequence. At each hook, run the command, present the results conversationally, and ask the user the decision question before proceeding.

### Phase 1: Source & Readiness

**Hook 1: `load`** — Load the workbook

```
python ".interactiveoverlay/interactive_runner.py" load "<path_to_twbx>" --output-dir <dir>
```

Present: Object counts for all 17 extracted types (worksheets, dashboards, datasources, calculations, parameters, filters, stories, actions, sets, groups, bins, hierarchies, sort_orders, aliases, custom_sql, user_filters, hyper_files).

Ask the user:
- "I found {N} worksheets, {N} datasources, {N} calculations, ... Does this look correct?"
- "Any objects you want to exclude from migration?"

---

**Hook 2: `assess`** — Readiness assessment

```
python ".interactiveoverlay/interactive_runner.py" assess --output-dir <dir>
```

Present: Overall grade (GREEN/YELLOW/RED), per-category scores (datasource, calculation, visual, filter, data model, interactivity, extract, scope), specific findings with severity.

Ask the user:
- "Overall readiness is {GRADE}. {N} warnings, {N} failures found."
- Show top 3 most critical findings.
- "Should we proceed, or address the warnings first?"

---

**Hook 3: `strategy`** — Data mode recommendation

```
python ".interactiveoverlay/interactive_runner.py" strategy --output-dir <dir>
```

Present: Recommended mode (Import/DirectQuery/Composite) with signal breakdown.

Ask the user:
- "Recommended mode: **{mode}** based on {signals}."
- "Accept this recommendation, or override to a different mode?"

If user overrides, run:
```
python ".interactiveoverlay/interactive_runner.py" calendar --culture <culture> --output-dir <dir>
```
to update the config mode (the `configure` API handles this).

---

### Phase 2: Extraction Review

**Hook 4: `datasources`** — Connections & tables

```
python ".interactiveoverlay/interactive_runner.py" datasources --output-dir <dir>
```

Present: For each datasource — connection type, table names, column counts, relationship counts.

Ask: "These are the {N} datasource connections. Any connector mappings to adjust?"

---

**Hook 5: `calculations`** — Formulas & classification

```
python ".interactiveoverlay/interactive_runner.py" calculations --output-dir <dir>
```

Present: Each calculation with name, Tableau formula, role (measure/calc column), and data type.

Ask: "Found {N} calculations. Any that should be reclassified (measure ↔ calculated column)? Any to flag for manual review?"

---

**Hook 6: `parameters`** — Parameters & defaults

```
python ".interactiveoverlay/interactive_runner.py" parameters --output-dir <dir>
```

Present: Parameter name, type (range/list/any), current value, allowable values.

Ask: "Found {N} parameters. Any default values to change?"

---

**Hook 7: `filters`** — Global & extract filters

```
python ".interactiveoverlay/interactive_runner.py" filters --output-dir <dir>
```

Present: Filter field, type, values.

Ask: "Found {N} filters. Should all be migrated, or exclude any?"

---

**Hook 8: `worksheets`** — Sheets & mark types

```
python ".interactiveoverlay/interactive_runner.py" worksheets --output-dir <dir>
```

Present: Worksheet name, Tableau mark type, field count, filter count.

Ask: "These are the {N} worksheets with their mark types. The visual mapping step (Phase 3) will show the Power BI equivalents."

---

**Hook 9: `dashboards`** — Layout objects

```
python ".interactiveoverlay/interactive_runner.py" dashboards --output-dir <dir>
```

Present: Dashboard name, object breakdown (worksheets, text boxes, images, filter controls).

Ask: "Found {N} dashboards. These will become Power BI report pages. Any page structure changes needed?"

---

**Hook 10: `security`** — RLS & user filters

```
python ".interactiveoverlay/interactive_runner.py" security --output-dir <dir>
```

Present: User filter rules, RLS role candidates.

Ask: "Found {N} user filter rules for RLS migration. Review the role mappings — any corrections?"

---

### Phase 3: Conversion

**Hook 11: `dax-preview`** — DAX conversions

```
python ".interactiveoverlay/interactive_runner.py" dax-preview --output-dir <dir>
```

Present: For each calculation — Tableau formula → DAX formula, with status (exact/approximated/overridden).

**Critical hook** — this is where users spend the most time. Highlight:
1. **Exact** conversions (green) — auto-converted with high confidence
2. **Approximated** conversions (yellow) — may need manual review
3. **Overridden** conversions (blue) — user has already edited

Ask: "Found {exact} exact, {approx} approximated, {overridden} overridden DAX conversions."
- For each approximated formula, suggest corrections using `.interactiveoverlay/references/dax-common-edits.md`
- "Would you like to edit any DAX formulas? Use `edit-dax` with the measure name and new formula."

---

**Hook 12: `dax-optimize`** — DAX optimization

```
python ".interactiveoverlay/interactive_runner.py" dax-optimize --output-dir <dir>
```

Present: Optimizations found (IF→SWITCH, ISBLANK→COALESCE, redundant CALCULATE, etc.) with before/after.

Ask: "Found {N} optimization opportunities. Accept all, or review individually?"

---

**Hook 13: `edit-dax`** — Manual DAX override (repeatable)

```
python ".interactiveoverlay/interactive_runner.py" edit-dax "<measure_name>" "<new_dax>" --output-dir <dir>
```

Use this whenever the user wants to change a DAX formula. Can be called multiple times.

---

**Hook 14: `m-query`** — Power Query M preview

```
python ".interactiveoverlay/interactive_runner.py" m-query --output-dir <dir>
```

Present: Per-table M expression with connection type and datasource name.

Ask: "Here are the Power Query M expressions for {N} tables. Any connection strings or transforms to adjust?"

---

**Hook 15: `visual-mapping`** — Visual type mappings

```
python ".interactiveoverlay/interactive_runner.py" visual-mapping --output-dir <dir>
```

Present: For each worksheet — Tableau mark type → PBI visual type, field count, override status.

Ask: "Here are the visual type mappings. Any to override?"
- Reference `.interactiveoverlay/references/visual-type-catalog.md` for the full mapping table.

To override:
```
python ".interactiveoverlay/interactive_runner.py" override-visual "<worksheet>" "<pbi_type>" --output-dir <dir>
```

---

**Hook 16: `calendar`** — Calendar configuration

```
python ".interactiveoverlay/interactive_runner.py" calendar --start-year 2020 --end-year 2030 --culture en-US --output-dir <dir>
```

Present: Current calendar config (start year, end year, culture, languages).

Ask: "Calendar table will span {start}–{end} with culture {culture}. Adjust?"

---

### Phase 4: Generation

**Hook 17: `semantic-model`** — TMDL preview

```
python ".interactiveoverlay/interactive_runner.py" semantic-model --output-dir <dir>
```

Present: Table count, measure count, calc column count, parameter count, hierarchy count, RLS rules, active DAX overrides.

Ask: "The semantic model will have {N} tables, {N} measures, {N} relationships. Ready to generate?"

---

**Hook 18: `report-layout`** — Page preview

```
python ".interactiveoverlay/interactive_runner.py" report-layout --output-dir <dir>
```

Present: Dashboard pages (visuals, slicers, text boxes, images per page), orphan worksheets that become standalone pages.

Ask: "The report will have {N} pages. Any page ordering changes?"

---

**Hook 19: `generate`** — Execute generation

```
python ".interactiveoverlay/interactive_runner.py" generate --output-dir <dir>
```

Present: Generation summary (output path, table count, measure count, page count).

Confirm: "The .pbip project has been generated at {path}."

---

### Phase 5: Validation

**Hook 20: `validate`** — Artifact validation

```
python ".interactiveoverlay/interactive_runner.py" validate --output-dir <dir>
```

Present: Validation results — errors, warnings, passes.

Ask: "Validation found {N} errors, {N} warnings. Fix errors before opening in Power BI Desktop?"

---

**Hook 21: `compare`** — Fidelity comparison

```
python ".interactiveoverlay/interactive_runner.py" compare --output-dir <dir>
```

Present: Source vs generated object counts, coverage gaps.

Ask: "Fidelity comparison complete. Any gaps to investigate?"

---

### Phase 6: Deploy (Optional)

**Hook 22a: `deploy-config`** — Configure deployment

```
python ".interactiveoverlay/interactive_runner.py" deploy-config --workspace-id <id> --output-dir <dir>
```

Ask: "What Power BI workspace should I deploy to?"

---

**Hook 22b: `deploy-execute`** — Execute deployment

```
python ".interactiveoverlay/interactive_runner.py" deploy-execute --output-dir <dir>
```

Present: Deployment result.

Confirm: "Deployed successfully to workspace {id}."

---

## Session Management

**Check status** — see current phase and completed hooks:
```
python ".interactiveoverlay/interactive_runner.py" status --output-dir <dir>
```

**Reset session** — start over:
```
python ".interactiveoverlay/interactive_runner.py" reset --output-dir <dir>
```

---

## Skip / Fast-Forward

Users can jump to any phase by saying:
- "Skip to Phase 3" → run hooks 11–16
- "Skip to generation" → run hooks 17–19
- "Just generate everything" → run load → generate (skip all review hooks)

When skipping, inform the user: "Skipping review hooks — using default conversions and mappings. You can always re-run individual hooks later."

---

## Handling User Overrides

When users request changes at any hook:

1. **DAX edits**: Use `edit-dax` hook with measure name and new formula
2. **Visual type overrides**: Use `override-visual` hook with worksheet name and PBI type
3. **Config changes**: Use `calendar` hook with new config values
4. **Reclassification**: Note the request and inform user this will be reflected in generation

All overrides persist in the session file and survive across terminal calls.

---

## Error Recovery

If any hook returns `"status": "error"`:
1. Show the error message to the user
2. Suggest corrective action based on the hook
3. Allow re-running the same hook after fixes

Common errors:
- `"No workbook loaded"` → Run `load` first
- `"No project generated"` → Run `generate` before `validate` or `compare`
- File not found → Check workbook path
