#!/usr/bin/env python3
"""Interactive migration runner — CLI tool with subcommands for each hook.

Wraps the MigrationSession API with structured JSON output and session
persistence so that Copilot can drive the migration conversationally.

Usage::

    python ".interactive overlay/interactive_runner.py" load path/to/workbook.twbx
    python ".interactive overlay/interactive_runner.py" assess
    python ".interactive overlay/interactive_runner.py" dax-preview
    python ".interactive overlay/interactive_runner.py" edit-dax "Total Sales" "SUM(Sales[Amount])"
    python ".interactive overlay/interactive_runner.py" generate --output-dir /tmp/pbi_output
"""

import argparse
import json
import logging
import os
import sys
import traceback

# Add project root to path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logger = logging.getLogger(__name__)

# Session persistence file — stored in the output directory
_SESSION_FILE = '.migration_session.json'
_DEFAULT_SESSION_DIR = os.path.join(_PROJECT_ROOT, 'artifacts', 'interactive')


# ════════════════════════════════════════════════════════════════════
#  SESSION PERSISTENCE
# ════════════════════════════════════════════════════════════════════

def _session_path(output_dir=None):
    """Return the path to the session persistence file."""
    base = output_dir or _DEFAULT_SESSION_DIR
    return os.path.join(base, _SESSION_FILE)


def _save_session(state, output_dir=None):
    """Persist session state to JSON."""
    path = _session_path(output_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _load_session(output_dir=None):
    """Load persisted session state, or return empty state."""
    path = _session_path(output_dir)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _get_session(output_dir=None):
    """Get or create a MigrationSession with persisted overrides."""
    from powerbi_import.notebook_api import MigrationSession

    state = _load_session(output_dir)
    session = MigrationSession()

    # Restore workbook if previously loaded
    workbook = state.get('workbook_path')
    if workbook and os.path.exists(workbook):
        session.load(workbook)

    # Restore DAX overrides
    for name, formula in state.get('dax_overrides', {}).items():
        session.edit_dax(name, formula)

    # Restore visual overrides
    for name, vtype in state.get('visual_overrides', {}).items():
        session.override_visual_type(name, vtype)

    # Restore config
    config = state.get('config', {})
    if config:
        session.configure(**config)

    return session, state


def _update_state(state, session, output_dir=None, **extras):
    """Update and persist session state."""
    state['dax_overrides'] = session.get_dax_overrides()
    state['visual_overrides'] = dict(session._visual_overrides)
    state['config'] = session.get_config()
    state.update(extras)
    _save_session(state, output_dir)


def _emit(result, hook_name, status='ok'):
    """Print structured JSON output for Copilot to parse."""
    output = {
        'hook': hook_name,
        'status': status,
        'result': result,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))


def _emit_error(hook_name, error):
    """Print structured error output."""
    output = {
        'hook': hook_name,
        'status': 'error',
        'error': str(error),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


# ════════════════════════════════════════════════════════════════════
#  HOOK IMPLEMENTATIONS — Phase 1: Source & Readiness
# ════════════════════════════════════════════════════════════════════

def hook_load(args):
    """hook:load — Load workbook, show 17 object counts."""
    from powerbi_import.notebook_api import MigrationSession

    workbook_path = args.workbook
    if not os.path.exists(workbook_path):
        _emit_error('load', f'File not found: {workbook_path}')
        return

    session = MigrationSession()
    summary = session.load(workbook_path)

    state = {
        'workbook_path': os.path.abspath(workbook_path),
        'phase': 'loaded',
        'completed_hooks': ['load'],
    }
    _update_state(state, session, args.output_dir)

    _emit({
        'workbook': os.path.basename(workbook_path),
        'object_counts': summary,
        'total_objects': sum(summary.values()),
    }, 'load')


def hook_assess(args):
    """hook:assess — Run 9-category readiness assessment."""
    session, state = _get_session(args.output_dir)

    assessment = session.assess()
    state['phase'] = 'assessed'
    state.setdefault('completed_hooks', []).append('assess')
    _update_state(state, session, args.output_dir)

    _emit(assessment, 'assess')


def hook_strategy(args):
    """hook:strategy — Recommend Import/DirectQuery/Composite."""
    session, state = _get_session(args.output_dir)

    from powerbi_import.strategy_advisor import recommend_strategy
    extracted = session._extracted
    if extracted is None:
        _emit_error('strategy', 'No workbook loaded — run load first')
        return

    rec = recommend_strategy(extracted)
    result = {
        'recommended_mode': rec.mode if hasattr(rec, 'mode') else str(rec),
        'summary': rec.summary if hasattr(rec, 'summary') else str(rec),
        'signals': rec.signals if hasattr(rec, 'signals') else [],
    }
    state.setdefault('completed_hooks', []).append('strategy')
    _update_state(state, session, args.output_dir)

    _emit(result, 'strategy')


# ════════════════════════════════════════════════════════════════════
#  HOOK IMPLEMENTATIONS — Phase 2: Extraction Review
# ════════════════════════════════════════════════════════════════════

def hook_datasources(args):
    """hook:datasources — Show connections, tables, columns, relationships."""
    session, state = _get_session(args.output_dir)
    extracted = session._extracted
    if extracted is None:
        _emit_error('datasources', 'No workbook loaded')
        return

    datasources = extracted.get('datasources', [])
    result = []
    for ds in datasources:
        tables = ds.get('tables', [])
        conn = ds.get('connection', ds.get('connection_map', {}))
        result.append({
            'name': ds.get('name', ''),
            'connection_type': conn.get('class', conn.get('type', 'unknown')),
            'table_count': len(tables),
            'tables': [
                {
                    'name': t.get('name', ''),
                    'column_count': len(t.get('columns', [])),
                    'relationship_count': len(t.get('relationships', [])),
                }
                for t in tables
            ],
        })

    state.setdefault('completed_hooks', []).append('datasources')
    _update_state(state, session, args.output_dir)
    _emit(result, 'datasources')


def hook_calculations(args):
    """hook:calculations — List formulas, role classification."""
    session, state = _get_session(args.output_dir)
    extracted = session._extracted
    if extracted is None:
        _emit_error('calculations', 'No workbook loaded')
        return

    calculations = extracted.get('calculations', [])
    result = []
    for calc in calculations:
        result.append({
            'name': calc.get('name', calc.get('caption', '')),
            'formula': calc.get('formula', ''),
            'role': calc.get('role', ''),
            'type': calc.get('type', ''),
            'datatype': calc.get('datatype', ''),
        })

    state.setdefault('completed_hooks', []).append('calculations')
    _update_state(state, session, args.output_dir)
    _emit({'count': len(result), 'calculations': result}, 'calculations')


def hook_parameters(args):
    """hook:parameters — Show range/list/any parameters with defaults."""
    session, state = _get_session(args.output_dir)
    extracted = session._extracted
    if extracted is None:
        _emit_error('parameters', 'No workbook loaded')
        return

    parameters = extracted.get('parameters', [])
    state.setdefault('completed_hooks', []).append('parameters')
    _update_state(state, session, args.output_dir)
    _emit({'count': len(parameters), 'parameters': parameters}, 'parameters')


def hook_filters(args):
    """hook:filters — Show global + datasource + extract filters."""
    session, state = _get_session(args.output_dir)
    extracted = session._extracted
    if extracted is None:
        _emit_error('filters', 'No workbook loaded')
        return

    filters = extracted.get('filters', [])
    state.setdefault('completed_hooks', []).append('filters')
    _update_state(state, session, args.output_dir)
    _emit({'count': len(filters), 'filters': filters}, 'filters')


def hook_worksheets(args):
    """hook:worksheets — Show sheets, mark types, field counts."""
    session, state = _get_session(args.output_dir)
    extracted = session._extracted
    if extracted is None:
        _emit_error('worksheets', 'No workbook loaded')
        return

    worksheets = extracted.get('worksheets', [])
    result = []
    for ws in worksheets:
        result.append({
            'name': ws.get('name', ''),
            'mark_type': ws.get('mark_type', ws.get('type', 'automatic')),
            'field_count': len(ws.get('fields', [])),
            'filter_count': len(ws.get('filters', [])),
        })

    state.setdefault('completed_hooks', []).append('worksheets')
    _update_state(state, session, args.output_dir)
    _emit({'count': len(result), 'worksheets': result}, 'worksheets')


def hook_dashboards(args):
    """hook:dashboards — Show layout objects."""
    session, state = _get_session(args.output_dir)
    extracted = session._extracted
    if extracted is None:
        _emit_error('dashboards', 'No workbook loaded')
        return

    dashboards = extracted.get('dashboards', [])
    result = []
    for db in dashboards:
        objects = db.get('objects', [])
        result.append({
            'name': db.get('name', ''),
            'object_count': len(objects),
            'object_types': list({o.get('type', 'unknown') for o in objects}),
        })

    state.setdefault('completed_hooks', []).append('dashboards')
    _update_state(state, session, args.output_dir)
    _emit({'count': len(result), 'dashboards': result}, 'dashboards')


def hook_security(args):
    """hook:security — Show user filters, RLS candidates."""
    session, state = _get_session(args.output_dir)
    extracted = session._extracted
    if extracted is None:
        _emit_error('security', 'No workbook loaded')
        return

    user_filters = extracted.get('user_filters', [])
    state.setdefault('completed_hooks', []).append('security')
    _update_state(state, session, args.output_dir)
    _emit({'count': len(user_filters), 'user_filters': user_filters}, 'security')


# ════════════════════════════════════════════════════════════════════
#  HOOK IMPLEMENTATIONS — Phase 3: Conversion
# ════════════════════════════════════════════════════════════════════

def hook_dax_preview(args):
    """hook:dax-preview — Show DAX conversions with status."""
    session, state = _get_session(args.output_dir)

    previews = session.preview_dax()
    exact = sum(1 for p in previews if p['status'] == 'exact')
    approx = sum(1 for p in previews if p['status'] == 'approximated')
    overridden = sum(1 for p in previews if p['status'] == 'overridden')

    state.setdefault('completed_hooks', []).append('dax-preview')
    _update_state(state, session, args.output_dir)

    _emit({
        'total': len(previews),
        'exact': exact,
        'approximated': approx,
        'overridden': overridden,
        'conversions': previews,
    }, 'dax-preview')


def hook_dax_optimize(args):
    """hook:dax-optimize — Run optimizer rules."""
    session, state = _get_session(args.output_dir)

    from powerbi_import.dax_optimizer import optimize_dax

    previews = session.preview_dax()
    optimizations = []
    for p in previews:
        original = p['dax_formula']
        optimized, rules = optimize_dax(original)
        if rules:
            optimizations.append({
                'name': p['name'],
                'original': original,
                'optimized': optimized,
                'rules_applied': rules,
            })

    state.setdefault('completed_hooks', []).append('dax-optimize')
    _update_state(state, session, args.output_dir)

    _emit({
        'total_optimized': len(optimizations),
        'optimizations': optimizations,
    }, 'dax-optimize')


def hook_edit_dax(args):
    """hook:edit-dax — Override a DAX formula."""
    session, state = _get_session(args.output_dir)

    session.edit_dax(args.measure_name, args.formula)
    _update_state(state, session, args.output_dir)

    _emit({
        'measure': args.measure_name,
        'new_formula': args.formula,
        'all_overrides': session.get_dax_overrides(),
    }, 'edit-dax')


def hook_m_query(args):
    """hook:m-query — Show Power Query M per table."""
    session, state = _get_session(args.output_dir)

    m_previews = session.preview_m()
    state.setdefault('completed_hooks', []).append('m-query')
    _update_state(state, session, args.output_dir)

    _emit({
        'total': len(m_previews),
        'queries': m_previews,
    }, 'm-query')


def hook_visual_mapping(args):
    """hook:visual-mapping — Show visual type mappings."""
    session, state = _get_session(args.output_dir)

    visuals = session.preview_visuals()
    state.setdefault('completed_hooks', []).append('visual-mapping')
    _update_state(state, session, args.output_dir)

    _emit({
        'total': len(visuals),
        'mappings': visuals,
    }, 'visual-mapping')


def hook_override_visual(args):
    """Override a visual type mapping."""
    session, state = _get_session(args.output_dir)

    session.override_visual_type(args.visual_name, args.visual_type)
    _update_state(state, session, args.output_dir)

    _emit({
        'visual': args.visual_name,
        'new_type': args.visual_type,
        'all_overrides': dict(session._visual_overrides),
    }, 'override-visual')


def hook_calendar(args):
    """hook:calendar — Configure calendar table."""
    session, state = _get_session(args.output_dir)

    config_updates = {}
    if args.start_year:
        config_updates['calendar_start'] = int(args.start_year)
    if args.end_year:
        config_updates['calendar_end'] = int(args.end_year)
    if args.culture:
        config_updates['culture'] = args.culture
    if args.languages:
        config_updates['languages'] = [l.strip() for l in args.languages.split(',')]

    updated = session.configure(**config_updates)
    state.setdefault('completed_hooks', []).append('calendar')
    _update_state(state, session, args.output_dir)

    _emit({
        'config': updated,
    }, 'calendar')


# ════════════════════════════════════════════════════════════════════
#  HOOK IMPLEMENTATIONS — Phase 4: Generation
# ════════════════════════════════════════════════════════════════════

def hook_semantic_model(args):
    """hook:semantic-model — Preview TMDL structure."""
    session, state = _get_session(args.output_dir)
    extracted = session._extracted
    if extracted is None:
        _emit_error('semantic-model', 'No workbook loaded')
        return

    datasources = extracted.get('datasources', [])
    calculations = extracted.get('calculations', [])
    parameters = extracted.get('parameters', [])
    user_filters = extracted.get('user_filters', [])
    hierarchies = extracted.get('hierarchies', [])

    tables = []
    for ds in datasources:
        for t in ds.get('tables', []):
            tables.append({
                'name': t.get('name', ''),
                'columns': len(t.get('columns', [])),
                'relationships': len(t.get('relationships', [])),
            })

    measures = [c for c in calculations if c.get('role', '') != 'dimension']
    calc_cols = [c for c in calculations if c.get('role', '') == 'dimension']

    state.setdefault('completed_hooks', []).append('semantic-model')
    _update_state(state, session, args.output_dir)

    _emit({
        'tables': len(tables),
        'table_details': tables,
        'measures': len(measures),
        'calculated_columns': len(calc_cols),
        'parameters': len(parameters),
        'hierarchies': len(hierarchies),
        'rls_rules': len(user_filters),
        'dax_overrides': len(session.get_dax_overrides()),
    }, 'semantic-model')


def hook_report_layout(args):
    """hook:report-layout — Preview pages and visual placement."""
    session, state = _get_session(args.output_dir)
    extracted = session._extracted
    if extracted is None:
        _emit_error('report-layout', 'No workbook loaded')
        return

    dashboards = extracted.get('dashboards', [])
    worksheets = extracted.get('worksheets', [])

    pages = []
    for db in dashboards:
        objects = db.get('objects', [])
        pages.append({
            'name': db.get('name', ''),
            'visuals': len([o for o in objects if o.get('type') == 'worksheet']),
            'slicers': len([o for o in objects if o.get('type') == 'filter_control']),
            'text_boxes': len([o for o in objects if o.get('type') == 'text']),
            'images': len([o for o in objects if o.get('type') == 'image']),
        })

    # Orphan worksheets (not in any dashboard) become standalone pages
    dashboard_sheets = set()
    for db in dashboards:
        for obj in db.get('objects', []):
            if obj.get('type') == 'worksheet':
                dashboard_sheets.add(obj.get('name', ''))

    orphans = [ws.get('name', '') for ws in worksheets
               if ws.get('name', '') not in dashboard_sheets]

    state.setdefault('completed_hooks', []).append('report-layout')
    _update_state(state, session, args.output_dir)

    _emit({
        'dashboard_pages': len(pages),
        'pages': pages,
        'orphan_worksheets': orphans,
    }, 'report-layout')


def hook_generate(args):
    """hook:generate — Execute .pbip generation."""
    session, state = _get_session(args.output_dir)

    output_dir = args.output_dir or _DEFAULT_SESSION_DIR
    result = session.generate(output_dir=output_dir)

    state['phase'] = 'generated'
    state['generated_path'] = output_dir
    state.setdefault('completed_hooks', []).append('generate')
    _update_state(state, session, args.output_dir)

    _emit(result, 'generate')


# ════════════════════════════════════════════════════════════════════
#  HOOK IMPLEMENTATIONS — Phase 5: Validation
# ════════════════════════════════════════════════════════════════════

def hook_validate(args):
    """hook:validate — Run artifact validator."""
    session, state = _get_session(args.output_dir)

    result = session.validate()
    state.setdefault('completed_hooks', []).append('validate')
    _update_state(state, session, args.output_dir)

    _emit(result, 'validate')


def hook_compare(args):
    """hook:compare — Run fidelity comparison."""
    session, state = _get_session(args.output_dir)
    extracted = session._extracted
    if extracted is None:
        _emit_error('compare', 'No workbook loaded')
        return

    # Basic fidelity comparison: count extracted vs generated objects
    generated_path = state.get('generated_path')
    if not generated_path:
        _emit_error('compare', 'No project generated yet — run generate first')
        return

    worksheets = extracted.get('worksheets', [])
    calculations = extracted.get('calculations', [])
    datasources = extracted.get('datasources', [])

    source_tables = sum(len(ds.get('tables', [])) for ds in datasources)
    source_measures = len([c for c in calculations
                          if c.get('role', '') != 'dimension'])

    # Count generated TMDL files
    tmdl_tables = 0
    tmdl_measures = 0
    for root, dirs, files in os.walk(generated_path):
        for f in files:
            if f.endswith('.tmdl') and f != 'model.tmdl':
                tmdl_tables += 1
            if f == 'model.tmdl':
                # Count measure refs in model.tmdl
                model_path = os.path.join(root, f)
                try:
                    with open(model_path, 'r', encoding='utf-8') as mf:
                        content = mf.read()
                    tmdl_measures = content.count('ref measure')
                except OSError:
                    pass

    result = {
        'source': {
            'worksheets': len(worksheets),
            'tables': source_tables,
            'calculations': len(calculations),
        },
        'generated': {
            'tmdl_files': tmdl_tables,
            'measures_referenced': tmdl_measures,
        },
        'fidelity_notes': [],
    }

    state.setdefault('completed_hooks', []).append('compare')
    _update_state(state, session, args.output_dir)
    _emit(result, 'compare')


# ════════════════════════════════════════════════════════════════════
#  HOOK IMPLEMENTATIONS — Phase 6: Deploy
# ════════════════════════════════════════════════════════════════════

def hook_deploy_config(args):
    """hook:deploy-config — Configure workspace, auth, gateway."""
    session, state = _get_session(args.output_dir)

    deploy_config = {
        'workspace_id': args.workspace_id or '',
        'refresh': args.refresh if hasattr(args, 'refresh') else False,
    }
    state['deploy_config'] = deploy_config
    state.setdefault('completed_hooks', []).append('deploy-config')
    _update_state(state, session, args.output_dir)

    _emit(deploy_config, 'deploy-config')


def hook_deploy_execute(args):
    """hook:deploy-execute — Deploy to PBI Service/Fabric."""
    session, state = _get_session(args.output_dir)

    deploy_config = state.get('deploy_config', {})
    workspace_id = deploy_config.get('workspace_id') or args.workspace_id
    if not workspace_id:
        _emit_error('deploy-execute', 'No workspace ID configured — run deploy-config first')
        return

    refresh = deploy_config.get('refresh', False)
    result = session.deploy(workspace_id, refresh=refresh)

    state['phase'] = 'deployed'
    state.setdefault('completed_hooks', []).append('deploy-execute')
    _update_state(state, session, args.output_dir)

    _emit(result, 'deploy-execute')


# ════════════════════════════════════════════════════════════════════
#  SESSION STATUS
# ════════════════════════════════════════════════════════════════════

def hook_status(args):
    """Show current session state and completed hooks."""
    state = _load_session(args.output_dir)
    if not state:
        _emit({'message': 'No active session. Run `load` to start.'}, 'status')
        return

    _emit({
        'workbook': os.path.basename(state.get('workbook_path', '')),
        'phase': state.get('phase', 'none'),
        'completed_hooks': state.get('completed_hooks', []),
        'dax_overrides': len(state.get('dax_overrides', {})),
        'visual_overrides': len(state.get('visual_overrides', {})),
        'config': state.get('config', {}),
    }, 'status')


def hook_reset(args):
    """Reset the session — clear all state."""
    path = _session_path(args.output_dir)
    if os.path.exists(path):
        os.remove(path)
    _emit({'message': 'Session reset.'}, 'reset')


# ════════════════════════════════════════════════════════════════════
#  CLI PARSER
# ════════════════════════════════════════════════════════════════════

def build_parser():
    """Build the argument parser with all hook subcommands."""
    parser = argparse.ArgumentParser(
        description='Interactive migration runner — Copilot-driven hooks',
        prog='interactive_runner',
    )
    parser.add_argument(
        '--output-dir', '-o',
        default=None,
        help='Output directory for session state and generated artifacts',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging',
    )

    subs = parser.add_subparsers(dest='hook', required=True)

    # Phase 1: Source & Readiness
    p_load = subs.add_parser('load', help='Load a Tableau workbook')
    p_load.add_argument('workbook', help='Path to .twb or .twbx file')
    p_load.set_defaults(func=hook_load)

    p_assess = subs.add_parser('assess', help='Run readiness assessment')
    p_assess.set_defaults(func=hook_assess)

    p_strategy = subs.add_parser('strategy', help='Recommend data mode')
    p_strategy.set_defaults(func=hook_strategy)

    # Phase 2: Extraction Review
    p_ds = subs.add_parser('datasources', help='Show datasource connections')
    p_ds.set_defaults(func=hook_datasources)

    p_calc = subs.add_parser('calculations', help='List calculations')
    p_calc.set_defaults(func=hook_calculations)

    p_param = subs.add_parser('parameters', help='Show parameters')
    p_param.set_defaults(func=hook_parameters)

    p_filt = subs.add_parser('filters', help='Show filters')
    p_filt.set_defaults(func=hook_filters)

    p_ws = subs.add_parser('worksheets', help='Show worksheets')
    p_ws.set_defaults(func=hook_worksheets)

    p_db = subs.add_parser('dashboards', help='Show dashboards')
    p_db.set_defaults(func=hook_dashboards)

    p_sec = subs.add_parser('security', help='Show RLS / user filters')
    p_sec.set_defaults(func=hook_security)

    # Phase 3: Conversion
    p_dax = subs.add_parser('dax-preview', help='Preview DAX conversions')
    p_dax.set_defaults(func=hook_dax_preview)

    p_daxopt = subs.add_parser('dax-optimize', help='Run DAX optimizer')
    p_daxopt.set_defaults(func=hook_dax_optimize)

    p_edit = subs.add_parser('edit-dax', help='Override a DAX formula')
    p_edit.add_argument('measure_name', help='Measure or calc name')
    p_edit.add_argument('formula', help='New DAX formula')
    p_edit.set_defaults(func=hook_edit_dax)

    p_mq = subs.add_parser('m-query', help='Preview M queries')
    p_mq.set_defaults(func=hook_m_query)

    p_vis = subs.add_parser('visual-mapping', help='Preview visual mappings')
    p_vis.set_defaults(func=hook_visual_mapping)

    p_vov = subs.add_parser('override-visual', help='Override a visual type')
    p_vov.add_argument('visual_name', help='Worksheet/visual name')
    p_vov.add_argument('visual_type', help='PBI visual type')
    p_vov.set_defaults(func=hook_override_visual)

    p_cal = subs.add_parser('calendar', help='Configure calendar table')
    p_cal.add_argument('--start-year', help='Calendar start year')
    p_cal.add_argument('--end-year', help='Calendar end year')
    p_cal.add_argument('--culture', help='Culture code (e.g. en-US)')
    p_cal.add_argument('--languages', help='Comma-separated language codes')
    p_cal.set_defaults(func=hook_calendar)

    # Phase 4: Generation
    p_sm = subs.add_parser('semantic-model', help='Preview TMDL model')
    p_sm.set_defaults(func=hook_semantic_model)

    p_rl = subs.add_parser('report-layout', help='Preview report pages')
    p_rl.set_defaults(func=hook_report_layout)

    p_gen = subs.add_parser('generate', help='Generate .pbip project')
    p_gen.set_defaults(func=hook_generate)

    # Phase 5: Validation
    p_val = subs.add_parser('validate', help='Validate generated project')
    p_val.set_defaults(func=hook_validate)

    p_cmp = subs.add_parser('compare', help='Fidelity comparison')
    p_cmp.set_defaults(func=hook_compare)

    # Phase 6: Deploy
    p_dc = subs.add_parser('deploy-config', help='Configure deployment')
    p_dc.add_argument('--workspace-id', help='PBI workspace ID')
    p_dc.add_argument('--refresh', action='store_true', help='Trigger refresh')
    p_dc.set_defaults(func=hook_deploy_config)

    p_de = subs.add_parser('deploy-execute', help='Deploy to PBI/Fabric')
    p_de.add_argument('--workspace-id', help='PBI workspace ID (override)')
    p_de.set_defaults(func=hook_deploy_execute)

    # Session management
    p_st = subs.add_parser('status', help='Show session status')
    p_st.set_defaults(func=hook_status)

    p_rs = subs.add_parser('reset', help='Reset session')
    p_rs.set_defaults(func=hook_reset)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING)

    try:
        args.func(args)
    except Exception as exc:
        hook_name = args.hook if hasattr(args, 'hook') else 'unknown'
        _emit_error(hook_name, f'{type(exc).__name__}: {exc}')
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
