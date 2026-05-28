# Light UI & Quality Roadmap (Post-v38.2)

Date: 2026-05-28  
Scope: End-user experience, migration correctness, dashboard metric precision

---

## 1) Current Baseline (Completed)

Recent evolutions already implemented:

1. Lightweight end-user UI (Tkinter, zero extra dependencies)
- File: `web/light_ui.py`
- Single workbook mode and batch folder mode
- Live log console and command preview
- Run/Stop controls

2. Advanced UI options
- `--assess` (single workbook)
- `--global-assess` (batch)
- `--prep-lineage` (batch)
- Option conflict handling by mode

3. UI progress indicator
- Determinate progress bar and percent display
- Batch progress parsing (`[n/total]`)
- Step progress parsing (`[Step x/y]`)

4. Correctness fix: `Number of Records` collision
- Prevent measure creation when same-named column exists
- Remove conflicting `Number of Records` measure if column already exists
- Target fix file: `powerbi_import/tmdl_generator.py`

5. Reporting precision: DAX-only metric
- Replaced ambiguous "Visuals With Measure" with DAX-specific counting
- Added metadata fields for explicit DAX measure tracking
- Target files: `generate_report.py`, `powerbi_import/pbip_generator.py`

6. PowerShell-first launcher
- Added `run_light_ui.ps1` at repo root
- Supports venv bootstrap, syntax precheck, and launch flow
- Supports `-DryRun` for validation without opening UI

---

## 2) Problem Statements to Solve Next

1. End-user launch friction
- Users should not need terminal commands to start UI.

2. Trust & explainability in KPI cards
- UI/report should clearly explain what counts as "DAX measure".

3. Error-to-action guidance
- When migration fails, users need direct remediation hints (not raw logs only).

4. Repeatability for non-technical users
- Common workflows should be available as presets.

---

## 3) Roadmap by Phase

## Phase A (v38.3.0) — End-User Usability Hardening

Goal: Make the light UI immediately usable by non-technical users.

1. One-click launchers
- ✅ Done: `run_light_ui.ps1` at repo root with venv bootstrap.

2. Preset-driven workflows
- Add presets in UI:
  - Standard Migration
  - Assessment Only
  - Prep Lineage
  - Batch + Global Assess

3. Better status UX
- Add current stage line (Extract / Generate / Report / Validate).
- Add elapsed time and completion summary panel.

4. Output shortcuts
- Add "Open Output Folder" and "Open Dashboard" buttons after completion.

Acceptance criteria:
- New user can run first migration without typing CLI commands.
- Preset run requires <= 3 clicks after selecting source/output.
- Completion screen always shows output path and dashboard path.

---

## Phase B (v38.4.0) — Quality & Diagnostics for End Users

Goal: Convert errors into actionable guidance and improve confidence.

1. Structured error hints
- Parse common failures and display plain-language actions.
- Include known class: measure/column naming collisions.

2. Safety checks before run
- Validate source type against selected mode before launch.
- Warn when output path likely to be locked/readonly.

3. "DAX Measure" definition in UI and report
- Tooltip/help text:
  - DAX measure = model measure in semantic model
  - excludes visual auto-aggregations

4. Health panel for generated artifacts
- Quick checks:
  - TMDL parse status
  - report pages count
  - visuals count
  - visuals with DAX measure count

Acceptance criteria:
- Top 5 frequent migration errors have explicit remediation text.
- KPI wording is unambiguous in both UI and generated report.
- Post-run health panel appears for every successful run.

---

## Phase C (v38.5.0) — Batch Operations & Operator Productivity

Goal: Improve throughput and observability for repeated migrations.

1. Batch queue mode
- Select multiple sources/folders and run sequentially.
- Per-item status list with pass/fail badges.

2. Cancellation and resume behavior
- Stop current item safely.
- Keep completed outputs.
- Allow resume from next item.

3. Session export
- Save UI session report as JSON/CSV:
  - source
  - options
  - duration
  - status
  - key metrics

4. Optional lightweight notifications
- System tray/toast notification on completion/failure.

Acceptance criteria:
- Queue run supports at least 10 items with per-item summaries.
- Stop does not corrupt already completed artifacts.
- Session export includes all executed items.

---

## 4) Technical Work Breakdown

1. UI layer
- `web/light_ui.py`
- Add presets, stage labels, output actions, health panel, queue controls.

2. Migration metadata enrichment
- `powerbi_import/pbip_generator.py`
- Keep `dax_measure_names` and `visual_details[].dax_measures` stable contract.

3. Reporting contract
- `generate_report.py`
- Maintain `visuals_with_dax_measures_count` in CSV/HTML outputs.

4. Semantic model safety
- `powerbi_import/tmdl_generator.py`
- Keep collision prevention logic for same-name measure/column.

5. Test coverage
- `tests/test_automation.py`
- Add UI-facing integration tests for naming and KPI consistency.

---

## 5) Risks & Mitigations

1. Risk: Log format drift breaks progress parsing
- Mitigation: prefer explicit progress events when available; keep regex fallback.

2. Risk: UI complexity grows beyond "light"
- Mitigation: keep zero extra dependencies; gate advanced features behind simple presets.

3. Risk: Metric regressions in dashboard exports
- Mitigation: contract tests for CSV headers and DAX-only counting rules.

4. Risk: filesystem permission issues (OneDrive/locks)
- Mitigation: preflight path checks + user-facing retry guidance.

---

## 6) Suggested Milestone Plan

1. Milestone M1 (1 week)
- Phase A complete
- Launcher + presets + output shortcuts

2. Milestone M2 (1 week)
- Phase B complete
- Error hints + health panel + KPI definitions

3. Milestone M3 (1-2 weeks)
- Phase C complete
- Queue mode + session export + cancel/resume

---

## 7) Definition of Done (for this roadmap)

1. End user can run, monitor, and retrieve output without terminal knowledge.
2. "Visuals With DAX Measure" is consistently defined and enforced in UI + reports.
3. Known measure/column name collisions do not produce invalid Power BI model output.
4. Batch execution is observable, cancellable, and auditable.

---

## 8) Developer Backlog (All Tickets)

Priority legend: `P0` critical, `P1` important, `P2` enhancement.

### Phase A Tickets (v38.3.0)

1. `A-01` (`P0`) PowerShell launcher hardening
- Scope: finalize `run_light_ui.ps1` behavior (`-DryRun`, `-NoVenvCreate`, path checks)
- Files: `run_light_ui.ps1`, `README.md`
- Done when: launcher works from clean clone on Windows with one command

2. `A-02` (`P0`) Preset selector in UI
- Status: ✅ Completed
- Scope: presets (`Standard`, `Assessment`, `Prep Lineage`, `Batch + Global Assess`)
- Files: `web/light_ui.py`
- Done when: selecting preset updates all related options/mode safely

3. `A-03` (`P1`) Runtime status panel
- Status: ✅ Completed
- Scope: stage line + elapsed timer + end summary card
- Files: `web/light_ui.py`
- Done when: user can see current stage and elapsed time throughout run

4. `A-04` (`P1`) Output shortcuts
- Status: ✅ Completed
- Scope: add buttons `Open Output Folder`, `Open Dashboard`
- Files: `web/light_ui.py`
- Done when: buttons are enabled only when corresponding files/folders exist

### Phase B Tickets (v38.4.0)

1. `B-01` (`P0`) Error hint engine
- Status: 🟡 Partial (initial rule set implemented)
- Scope: map known errors to plain-language remediation
- Files: `web/light_ui.py`, optional helper module under `powerbi_import/`
- Seed cases:
  - measure/column same-name collisions
  - malformed slicer/render payload
  - missing datasource files
  - locked output path
  - missing Python/venv

2. `B-02` (`P0`) Preflight guardrails
- Status: 🟡 Partial (output writability + mode/source checks implemented)
- Scope: mode/source mismatch checks, output writability check, warning banners
- Files: `web/light_ui.py`

3. `B-03` (`P1`) DAX metric explainability
- Status: 🟡 Partial (UI definition text implemented; report-side note pending)
- Scope: add help text in UI and report export note
- Files: `web/light_ui.py`, `generate_report.py`
- Rule text: DAX measure = model measure in semantic model, excludes visual auto-aggregations

4. `B-04` (`P1`) Artifact health panel
- Status: ✅ Completed (UI post-run health summary)
- Scope: summarize generated pages/visuals/DAX-measure visuals + validation state
- Files: `web/light_ui.py`, metadata consumption only

### Phase C Tickets (v38.5.0)

1. `C-01` (`P0`) Queue execution mode
- Status: ✅ Completed
- Scope: enqueue multiple jobs (single and batch), per-item status table
- Files: `web/light_ui.py`

2. `C-02` (`P0`) Cancel/resume semantics
- Status: ✅ Completed
- Scope: stop current job safely, keep completed outputs, resume queue
- Files: `web/light_ui.py`

3. `C-03` (`P1`) Session export
- Status: ✅ Completed
- Scope: export run history to JSON and CSV
- Files: `web/light_ui.py`

4. `C-04` (`P2`) Completion notifications
- Status: ✅ Completed (lightweight title+beep notification)
- Scope: optional desktop notification when run completes/fails
- Files: `web/light_ui.py`

---

## 9) Dependency Graph

1. `A-02` depends on current option model in `web/light_ui.py`.
2. `A-03` should be implemented before `C-01` to reuse stage/progress primitives.
3. `B-01` depends on stable parsing of process output from `web/light_ui.py`.
4. `B-04` depends on metadata contract from:
- `powerbi_import/pbip_generator.py`
- `generate_report.py`
5. `C-02` depends on `C-01` queue state model.

---

## 10) Validation Matrix

### Automated

1. Syntax checks
- `python -m py_compile web/light_ui.py`
- `python -m py_compile generate_report.py powerbi_import/pbip_generator.py powerbi_import/tmdl_generator.py`

2. Report metric contract tests
- `python -m pytest tests/test_automation.py -k "summary_csv"`

3. Targeted migration safety checks
- `python migrate.py examples/real_world/SampleWB.twbx --output-dir artifacts/verify_samplewb_clean --verbose`
- Verify no measure/column collision for `Number of Records`

### Manual

1. PowerShell launcher workflow (`run_light_ui.ps1`)
2. Preset switching correctness (single vs batch)
3. Render-open test in Power BI Desktop for at least:
- `SampleWB`
- `nba_player_stats`

---

## 11) Suggested Build Order (Fastest Path)

1. `A-02` presets
2. `A-03` status panel
3. `A-04` output shortcuts
4. `B-01` error hints
5. `B-02` preflight checks
6. `B-03` DAX metric explainability
7. `B-04` health panel
8. `C-01` queue mode
9. `C-02` cancel/resume
10. `C-03` session export
11. `C-04` notifications

---

## 12) Delivery Gates

1. Gate G1 (Phase A complete)
- End user launches via PowerShell script and runs migration with presets.

2. Gate G2 (Phase B complete)
- Error messages become actionable; KPI meaning is explicit and stable.

3. Gate G3 (Phase C complete)
- Queue workflow is production-usable with resume + export.
