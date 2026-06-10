"""One-shot diagnostic audit for issues:
  A. Visuals with no field / data role attached (empty visual)
  B. Filter clauses with empty In.Values, %null% literals, or untyped literals

Walks every .pbip project under artifacts/ and prints a per-project + global
summary.
"""
from __future__ import annotations
import json
import os
import sys
from collections import defaultdict
from typing import Any


ROOT = os.path.join(os.path.dirname(__file__), 'artifacts')

# ---------------------------------------------------------------------------
# A. Empty-visual detection
# ---------------------------------------------------------------------------

# Visual types that legitimately have no data (decoration / navigation)
NO_DATA_VISUALS = {
    'textbox', 'image', 'shape', 'actionButton', 'pageNavigator',
    'bookmarkNavigator', 'basicShape',
}


def _has_field_in_query(visual: dict) -> bool:
    """Return True if visual.visual.query.queryState has at least one
    populated data role (a non-empty projections list)."""
    v = visual.get('visual') or {}
    q = v.get('query') or {}
    qs = q.get('queryState') or {}
    if not isinstance(qs, dict):
        return False
    for role_name, role_def in qs.items():
        if not isinstance(role_def, dict):
            continue
        projections = role_def.get('projections') or []
        if isinstance(projections, list) and projections:
            return True
    return False


def _visual_type(visual: dict) -> str:
    v = visual.get('visual') or {}
    return v.get('visualType') or '(unknown)'


def _visual_title(visual: dict) -> str:
    # Try the standard "title" object → "text" property → value
    v = visual.get('visual') or {}
    objs = v.get('objects') or {}
    title_arr = objs.get('title') or []
    if isinstance(title_arr, list) and title_arr:
        first = title_arr[0] or {}
        props = first.get('properties') or {}
        text = props.get('text') or {}
        expr = text.get('expr') or {}
        lit = expr.get('Literal') or {}
        val = lit.get('Value')
        if isinstance(val, str):
            return val.strip("'")
    return ''


# ---------------------------------------------------------------------------
# B. Filter health
# ---------------------------------------------------------------------------

def _walk(obj: Any, callback):
    """Recursively walk arbitrary JSON, calling callback(node, path) on dicts."""
    def go(node, path):
        if isinstance(node, dict):
            callback(node, path)
            for k, v in node.items():
                go(v, path + [str(k)])
        elif isinstance(node, list):
            for i, v in enumerate(node):
                go(v, path + [f'[{i}]'])
    go(obj, [])


def _analyze_filter(filter_obj: dict, issues: list, where_path: str):
    """Inspect a single filter object's filter.Where and find suspect literals."""
    f = filter_obj.get('filter') or {}
    where = f.get('Where') or []
    if not isinstance(where, list):
        return
    for clause in where:
        cond = (clause or {}).get('Condition') or {}
        # Drill into In clauses (including Not -> In)
        in_clauses = []

        def collect(node):
            if isinstance(node, dict):
                if 'In' in node and isinstance(node['In'], dict):
                    in_clauses.append(node['In'])
                for v in node.values():
                    collect(v)
            elif isinstance(node, list):
                for v in node:
                    collect(v)

        collect(cond)

        for in_node in in_clauses:
            values = in_node.get('Values')
            if not values:
                issues.append((where_path, 'empty_In_Values', None))
                continue
            if not isinstance(values, list):
                continue
            for row in values:
                if not isinstance(row, list):
                    continue
                for v in row:
                    if not isinstance(v, dict):
                        continue
                    lit = v.get('Literal') or {}
                    val = lit.get('Value')
                    if isinstance(val, str):
                        # %null% placeholder
                        if '%null%' in val.lower():
                            issues.append((where_path, '%null%_literal', val))
                        # Mixed-type heuristic: '1L' or quoted-number on string col
                        # (we can't easily know col type from filter alone here)


# ---------------------------------------------------------------------------
# Project walk
# ---------------------------------------------------------------------------

def audit_project(report_dir: str) -> dict:
    """Walk a *.Report directory and count issues."""
    result = {
        'project': os.path.basename(report_dir),
        'empty_visuals': [],     # (page, vid, vtype, title)
        'filter_issues': [],     # (location, kind, value)
        'total_visuals': 0,
        'total_filters_with_issues': 0,
    }

    defn = os.path.join(report_dir, 'definition')
    pages_dir = os.path.join(defn, 'pages')
    if not os.path.isdir(pages_dir):
        return result

    # Walk each page
    for page_name in sorted(os.listdir(pages_dir)):
        page_dir = os.path.join(pages_dir, page_name)
        if not os.path.isdir(page_dir):
            continue

        # Page filters
        page_json = os.path.join(page_dir, 'page.json')
        if os.path.isfile(page_json):
            try:
                with open(page_json, 'r', encoding='utf-8') as fh:
                    pdoc = json.load(fh)
            except Exception:
                pdoc = {}
            page_filters = pdoc.get('filters') or []
            for fil in page_filters:
                issues = []
                _analyze_filter(fil, issues, f'{page_name}:page')
                if issues:
                    result['filter_issues'].extend(issues)
                    result['total_filters_with_issues'] += 1

        # Visuals
        visuals_dir = os.path.join(page_dir, 'visuals')
        if not os.path.isdir(visuals_dir):
            continue
        for vid in sorted(os.listdir(visuals_dir)):
            vdir = os.path.join(visuals_dir, vid)
            vjson = os.path.join(vdir, 'visual.json')
            if not os.path.isfile(vjson):
                continue
            try:
                with open(vjson, 'r', encoding='utf-8') as fh:
                    vdoc = json.load(fh)
            except Exception:
                continue
            result['total_visuals'] += 1
            vtype = _visual_type(vdoc)
            if vtype not in NO_DATA_VISUALS:
                if not _has_field_in_query(vdoc):
                    result['empty_visuals'].append(
                        (page_name, vid, vtype, _visual_title(vdoc))
                    )
            # Visual filters
            vfilters = vdoc.get('filterConfig', {}).get('filters') or []
            for fil in vfilters:
                issues = []
                _analyze_filter(fil, issues, f'{page_name}:{vid}:visual')
                if issues:
                    result['filter_issues'].extend(issues)
                    result['total_filters_with_issues'] += 1

    # Report-level filters
    report_json = os.path.join(defn, 'report.json')
    if os.path.isfile(report_json):
        try:
            with open(report_json, 'r', encoding='utf-8') as fh:
                rdoc = json.load(fh)
        except Exception:
            rdoc = {}
        rfilters = rdoc.get('filterConfig', {}).get('filters') or rdoc.get('filters') or []
        for fil in rfilters:
            issues = []
            _analyze_filter(fil, issues, 'report:report')
            if issues:
                result['filter_issues'].extend(issues)
                result['total_filters_with_issues'] += 1

    return result


def main():
    if not os.path.isdir(ROOT):
        print(f'No artifacts dir: {ROOT}')
        sys.exit(0)

    # Find every *.Report under artifacts/
    report_dirs = []
    for dirpath, dirnames, _ in os.walk(ROOT):
        for d in dirnames:
            if d.endswith('.Report'):
                report_dirs.append(os.path.join(dirpath, d))

    print(f'Found {len(report_dirs)} report packages')

    global_empty_by_type = defaultdict(int)
    global_filter_by_kind = defaultdict(int)
    projects_with_empty = 0
    projects_with_filter_issues = 0
    total_empty = 0
    total_filter_issues = 0

    details_to_show = []
    for rd in report_dirs:
        r = audit_project(rd)
        if r['empty_visuals'] or r['filter_issues']:
            details_to_show.append((rd, r))
        if r['empty_visuals']:
            projects_with_empty += 1
            total_empty += len(r['empty_visuals'])
            for _, _, vtype, _ in r['empty_visuals']:
                global_empty_by_type[vtype] += 1
        if r['filter_issues']:
            projects_with_filter_issues += 1
            total_filter_issues += len(r['filter_issues'])
            for _, kind, _ in r['filter_issues']:
                global_filter_by_kind[kind] += 1

    print('\n=== GLOBAL SUMMARY ===')
    print(f'  Projects with empty visuals       : {projects_with_empty}')
    print(f'  Total empty visuals (no fields)   : {total_empty}')
    print(f'  Projects with filter issues       : {projects_with_filter_issues}')
    print(f'  Total filter issue occurrences    : {total_filter_issues}')

    print('\n  Empty visuals by visualType:')
    for k, v in sorted(global_empty_by_type.items(), key=lambda x: -x[1]):
        print(f'    {v:5d}  {k}')

    print('\n  Filter issues by kind:')
    for k, v in sorted(global_filter_by_kind.items(), key=lambda x: -x[1]):
        print(f'    {v:5d}  {k}')

    # Show top 10 worst projects
    print('\n=== TOP OFFENDERS (first 10) ===')
    worst = sorted(details_to_show,
                   key=lambda x: -(len(x[1]['empty_visuals']) + len(x[1]['filter_issues'])))[:10]
    for rd, r in worst:
        rel = os.path.relpath(rd, ROOT)
        print(f'\n  {rel}')
        print(f'    Empty visuals: {len(r["empty_visuals"])} / {r["total_visuals"]} non-decoration')
        # Show first 5 examples
        for pg, vid, vt, ttl in r['empty_visuals'][:5]:
            print(f'      - page={pg}  vid={vid}  type={vt}  title="{ttl}"')
        if len(r['empty_visuals']) > 5:
            print(f'      ... (+{len(r["empty_visuals"]) - 5} more)')
        if r['filter_issues']:
            print(f'    Filter issues: {len(r["filter_issues"])} occurrences')
            seen = set()
            for loc, kind, val in r['filter_issues']:
                key = (kind, str(val)[:40])
                if key in seen:
                    continue
                seen.add(key)
                print(f'      - {kind}  @  {loc}  val={val!r}')
                if len(seen) >= 5:
                    break


if __name__ == '__main__':
    main()
