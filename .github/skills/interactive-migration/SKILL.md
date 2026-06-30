---
description: "Guided, conversational Tableau → Power BI migration with 22 hook points across 6 phases. Walks users through extraction, conversion, generation, validation, and deployment with review and override at every step. Every action is logged to a migration summary. USE FOR: interactive migration, guided migration, step-by-step migration, tableau to power bi walkthrough, conversational migration, migrate with review."
applyTo: "**"
---

# Interactive Migration Skill

Conversational Tableau → Power BI migration with full agentic logging.

## Quick Start

```
@interactive-migration migrate path/to/workbook.twbx
```

Or step by step:
```
@interactive-migration load path/to/workbook.twbx --output-dir artifacts/interactive
@interactive-migration assess
@interactive-migration dax-preview
```

## Overview

This skill wraps the existing migration engine (`interactive_runner.py`) in a guided, conversational experience. The orchestrator agent (`@interactive-migration`) walks you through 6 phases and 22 hooks, pausing at each step for your review and approval.

**Key features:**
- 🎯 **22 decision points** — review and override at every step
- 📋 **Agentic migration log** — every hook execution documented
- 🔄 **Session persistence** — overrides survive across chat turns
- ⏩ **Skip/fast-forward** — jump to any phase if you're confident
- ↩️ **Backtrack** — re-run any hook after changes

## Phases

| Phase | Hooks | Agent | Focus |
|-------|-------|-------|-------|
| 1. Source & Readiness | 1–3 | @interactive-source | Load, assess, strategy |
| 2. Extraction Review | 4–10 | @interactive-extraction | Datasources, calcs, params, filters, sheets, dashboards, security |
| 3. Conversion | 11–16 | @interactive-conversion | DAX, M queries, visual mapping, calendar |
| 4. Generation | 17–19 | @interactive-generation | Semantic model, report layout, generate |
| 5. Validation | 20–21 | @interactive-validation | Validate, compare fidelity |
| 6. Deploy | 22 | @interactive-deployment | Configure, deploy to workspace |

## Commands

| Command | Purpose |
|---------|---------|
| `migrate <path>` | Start full guided migration |
| `load <path>` | Load workbook (Phase 1) |
| `assess` | Run readiness assessment |
| `strategy` | Get data mode recommendation |
| `dax-preview` | Preview DAX conversions |
| `edit-dax "<name>" "<formula>"` | Override a DAX formula |
| `visual-mapping` | Preview visual type mappings |
| `generate` | Generate .pbip project |
| `validate` | Validate output artifacts |
| `compare` | Compare fidelity vs source |
| `deploy` | Deploy to Power BI Service |
| `status` | Show current progress |
| `skip to Phase N` | Fast-forward to phase N |

## Migration Summary Log

Every hook execution is documented in `{output_dir}/migration_log.md`:

```markdown
### [2026-06-19T15:30:00Z] Hook: load — Phase 1: Source & Readiness

**Status:** ok
**Duration:** 2.3s
**User Decision:** Confirmed — no exclusions
**Overrides Applied:** None
**Key Findings:**
- 12 worksheets, 3 datasources, 45 calculations
- Total: 127 objects extracted
```

## Execution Requirements

Before the first hook runs, the orchestrator verifies:

| Check | Passes When |
|-------|-------------|
| Python 3.12+ | `python --version` returns 3.12+ |
| Project root | `migrate.py` + `.interactiveoverlay/interactive_runner.py` exist |
| Runner accessible | `python interactive_runner.py --help` exits 0 |
| Output dir writable | Can create files in the output directory |

Each hook also has **per-hook prerequisites** (which hooks must complete first) and **required user inputs** (collected via structured prompts before execution). The orchestrator **never runs a hook until prerequisites are met AND inputs are collected**.

### Hard Gates (always require user confirmation)

- **Hook 1 (load)** — must confirm workbook path
- **Hook 19 (generate)** — must confirm before writing files
- **Hook 22b (deploy-execute)** — must confirm + verify auth before pushing

### Input Collection

At every decision point, the agent presents structured choices:
```
🔹 Decision needed: {question}

Choose:
  1. {primary action} (Recommended)
  2. {alternative}
  3. {skip option}
```

The user's choice is logged in `migration_log.md` alongside the hook result.

## Architecture

```
User ←→ @interactive-migration (orchestrator)
              ├── @interactive-source      (Phase 1)
              ├── @interactive-extraction   (Phase 2)
              ├── @interactive-conversion   (Phase 3)
              ├── @interactive-generation   (Phase 4)
              ├── @interactive-validation   (Phase 5)
              └── @interactive-deployment   (Phase 6)
              
All agents invoke: interactive_runner.py → MigrationSession API → migration engine (read-only)
```

## Zero-Repo-Impact Guarantee

This suite:
- ✅ Installs to user profile (`~/.github/agents/`, `~/.copilot/skills/`)
- ✅ Reads the migration engine without modifying it
- ✅ Writes output only to the specified `--output-dir`
- ❌ Never modifies source code, tests, CI, or any repo file
