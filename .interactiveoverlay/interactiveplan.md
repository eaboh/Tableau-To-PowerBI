# Plan: Interactive Migration Skill with Conversational Hooks

Transform the automated Tableau→Power BI migration into a guided, conversational Copilot workflow. A new skill (`.github/skills/interactive-migration/`) defines 22 hook points across 6 phases where Copilot pauses, presents results, and asks for user review/correction before proceeding. A thin runner script wraps the existing `MigrationSession` API so each hook is a terminal subcommand returning JSON that Copilot interprets conversationally.

---

## Steps

**Phase A: Runner Script** (`scripts/interactive_runner.py`) — *new file*
1. Build a CLI tool with subcommands for each hook (`load`, `assess`, `datasources`, `dax-preview`, `edit-dax`, `generate`, etc.), backed by `MigrationSession` from `powerbi_import/notebook_api.py`
2. Add session persistence via `.migration_session.json` so state (overrides, config, current phase) survives across independent terminal calls
3. Each subcommand outputs structured JSON that Copilot parses and presents conversationally

**Phase B: SKILL.md** (`.github/skills/interactive-migration/SKILL.md`) — *new file*
4. Define the conversational workflow with 22 hooks across 6 phases (see hook table below)
5. For each hook, specify: what to run in terminal, how to present results, what to ask the user, and how to handle overrides
6. Include skip/fast-forward instructions so users can jump to any phase

**Phase C: Reference Docs** — *new files, parallel with Phase B*
7. `references/hooks.md` — Detailed hook reference with inputs, outputs, and decision prompts
8. `references/dax-common-edits.md` — Common DAX corrections Copilot can suggest at `hook:dax-preview`
9. `references/visual-type-catalog.md` — All 118 visual type mappings for override guidance

---

## Hook Map (22 hooks, 6 phases)

| Phase | Hook | Action | User Decision |
|-------|------|--------|---------------|
| **1: Source & Readiness** | `hook:load` | Load workbook, show 17 object counts | Confirm source, set hyper row limit |
| | `hook:assess` | Run 9-category readiness assessment | Review scores, decide go/no-go |
| | `hook:strategy` | Recommend Import/DirectQuery/Composite | Accept or override data mode |
| **2: Extraction Review** | `hook:datasources` | Show connections, tables, columns, relationships | Confirm connector mappings |
| | `hook:calculations` | List formulas, role classification (measure/calc column) | Reclassify, flag for manual review |
| | `hook:parameters` | Show range/list/any parameters with defaults | Adjust handling, set values |
| | `hook:filters` | Show global + datasource + extract filters | Confirm migration scope |
| | `hook:worksheets` | Show sheets, mark types, field counts | Preview visual mapping candidates |
| | `hook:dashboards` | Show layout objects (sheet/text/image/filter control) | Confirm page structure |
| | `hook:security` | Show user filters, RLS candidates | Approve role mappings |
| **3: Conversion** | `hook:dax-preview` | Show DAX conversions (exact/approximated/unsupported) | Edit formulas, approve approximations |
| | `hook:dax-optimize` | Run optimizer (IF→SWITCH, ISBLANK→COALESCE, etc.) | Accept/reject each rule |
| | `hook:m-query` | Show Power Query M per table | Review connection strings, transforms |
| | `hook:visual-mapping` | Show 118 mark→visual type mappings | Override visual types |
| | `hook:calendar` | Configure calendar table (date range, culture, languages) | Set years, locale |
| **4: Generation** | `hook:semantic-model` | Preview TMDL (tables, measures, relationships, RLS) | Final review before write |
| | `hook:report-layout` | Preview pages, visual placement, filters | Adjust page order |
| | `hook:generate` | Execute .pbip generation | Confirm output dir and format |
| **5: Validation** | `hook:validate` | Run artifact validator | Fix errors, accept warnings |
| | `hook:compare` | Run fidelity comparison (Tableau vs PBI) | Review gaps |
| **6: Deploy** | `hook:deploy-config` | Configure workspace, auth, gateway | Set workspace ID |
| | `hook:deploy-execute` | Deploy to PBI Service/Fabric | Confirm, trigger refresh |

---

## Relevant Files

**Existing (reuse/reference):**
- `powerbi_import/notebook_api.py` — `MigrationSession` class (load, assess, preview_dax, edit_dax, preview_m, preview_visuals, override_visual_type, configure, generate, validate)
- `powerbi_import/plugins.py` — `PluginBase` hook architecture to align with
- `powerbi_import/assessment.py` — `run_assessment()` for hook:assess
- `powerbi_import/dax_optimizer.py` — `optimize_dax()` for hook:dax-optimize
- `powerbi_import/strategy_advisor.py` — `recommend_strategy()` for hook:strategy
- `powerbi_import/wizard.py` — Existing 7-step wizard pattern as reference
- `examples/plugins/` — Plugin examples showing hook usage patterns

**New files:**
- `scripts/interactive_runner.py` — Runner script with 22 subcommands + session persistence
- `.github/skills/interactive-migration/SKILL.md` — Skill definition with conversational workflow
- `.github/skills/interactive-migration/references/hooks.md` — Hook reference
- `.github/skills/interactive-migration/references/dax-common-edits.md` — DAX edit guide
- `.github/skills/interactive-migration/references/visual-type-catalog.md` — Visual type catalog

---

## Verification

1. **Runner smoke test** — Run each subcommand against a sample .twbx, verify valid JSON output
2. **End-to-end walkthrough** — Invoke `/interactive-migration` in Copilot chat, step through all 22 hooks
3. **Override round-trip** — Edit DAX at `hook:dax-preview`, confirm it appears in generated .pbip at `hook:generate`
4. **Session resume** — Close/reopen Copilot mid-migration, resume from last completed hook
5. **Skill discovery** — Type `/` in chat, confirm `interactive-migration` appears; test auto-loading on "migrate tableau" queries

---

## Decisions

- **Runner script approach** over raw `migrate.py` flags — enables stateful overrides and structured JSON output per hook
- **22 hooks** — balanced granularity; users can skip ahead with "skip to phase N"
- **Single-workbook scope for v1** — shared model merge + batch mode hooks deferred to v2
- **No external dependencies** — stdlib only, consistent with project rules
- **Session file** (`.migration_session.json`) in output dir for state persistence across terminal calls

## Further Considerations

1. **LLM-assisted DAX refinement** — At `hook:dax-preview`, Copilot could use its own reasoning + `dax-common-edits.md` to suggest DAX improvements for approximated formulas. *Recommended: yes.*
2. **Batch mode (v2)** — Extend hooks for multi-workbook workflows with aggregate review points (e.g., review all DAX across a batch). *Recommended: defer.*
3. **Custom hook ordering** — Some users may want a different phase sequence (e.g., DAX review before extraction review). Should the skill support arbitrary hook ordering? *Recommended: support skip/jump but keep default sequence fixed.*
