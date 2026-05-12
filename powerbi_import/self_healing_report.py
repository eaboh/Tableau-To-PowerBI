"""Self-Healing v3.4 — PBIR / report-side healers (Sprint 140).

Companion to ``self_healing_v3.py``. While that module heals the TMDL
**model** dict in-memory before write, this module heals the **report**
side post-write by walking the ``<Name>.Report/`` directory and rewriting
JSON files in place.

Healers operate on a ``ReportState`` snapshot (loaded by ``load_report``)
that holds:

    {
        'def_dir': '.../<Name>.Report/definition',
        'pages_dir': '.../<Name>.Report/definition/pages',
        'report_json': {...},                       # report.json
        'pages_metadata': {...},                    # pages.json
        'pages': [
            {
                'dir': '.../ReportSectionXxx',
                'name': 'ReportSectionXxx',
                'json': {...},                      # page.json
                'visuals': [
                    {
                        'dir': '.../visuals/<vid>',
                        'name': '<vid>',
                        'json': {...},              # visual.json
                    },
                    ...
                ],
            },
            ...
        ],
        '_dirty_files': set[str],   # absolute paths needing re-write
    }

Each healer signature: ``(state, recovery=None) -> int`` returns the
number of repairs applied. Healers never raise — defensive try/except
in ``run_report_healers``.

Wired into ``pbip_generator.create_report_structure`` immediately after
the report directory is assembled. CLI flag-free; identical contract to
the model-side engine.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Default PBI report canvas dimensions (16:9 desktop default)
_DEFAULT_CANVAS_WIDTH = 1280
_DEFAULT_CANVAS_HEIGHT = 720

# Minimum sane dimensions for a visual
_MIN_VISUAL_W = 80
_MIN_VISUAL_H = 60


# ════════════════════════════════════════════════════════════════════
#  Loader / Writer
# ════════════════════════════════════════════════════════════════════

def _safe_load_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _safe_dump_json(path: str, data: Dict[str, Any]) -> bool:
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


def load_report(report_dir: str) -> Optional[Dict[str, Any]]:
    """Load a ``<Name>.Report/`` directory into a healable state dict.

    Returns ``None`` if the directory is missing required files.
    """
    if not os.path.isdir(report_dir):
        return None
    def_dir = os.path.join(report_dir, 'definition')
    pages_dir = os.path.join(def_dir, 'pages')
    if not os.path.isdir(pages_dir):
        return None

    report_json = _safe_load_json(os.path.join(def_dir, 'report.json')) or {}
    pages_metadata = _safe_load_json(os.path.join(pages_dir, 'pages.json')) or {}

    pages: List[Dict[str, Any]] = []
    for entry in sorted(os.listdir(pages_dir)):
        page_path = os.path.join(pages_dir, entry)
        if not os.path.isdir(page_path):
            continue
        page_json_path = os.path.join(page_path, 'page.json')
        if not os.path.isfile(page_json_path):
            continue
        page_json = _safe_load_json(page_json_path) or {}
        visuals: List[Dict[str, Any]] = []
        visuals_dir = os.path.join(page_path, 'visuals')
        if os.path.isdir(visuals_dir):
            for vname in sorted(os.listdir(visuals_dir)):
                vpath = os.path.join(visuals_dir, vname)
                vfile = os.path.join(vpath, 'visual.json')
                if not os.path.isfile(vfile):
                    continue
                vjson = _safe_load_json(vfile) or {}
                visuals.append({
                    'dir': vpath,
                    'name': vname,
                    'json': vjson,
                })
        pages.append({
            'dir': page_path,
            'name': entry,
            'json': page_json,
            'visuals': visuals,
        })

    return {
        'def_dir': def_dir,
        'pages_dir': pages_dir,
        'report_json': report_json,
        'pages_metadata': pages_metadata,
        'pages': pages,
        '_dirty_files': set(),
    }


def _mark_dirty(state: Dict[str, Any], path: str) -> None:
    state['_dirty_files'].add(path)


def write_report(state: Dict[str, Any]) -> int:
    """Re-write all dirty files. Returns count of files written."""
    written = 0
    dirty: Set[str] = state.get('_dirty_files', set())
    if not dirty:
        return 0
    # Map paths to their data sources.
    file_data: Dict[str, Dict[str, Any]] = {}
    file_data[os.path.join(state['def_dir'], 'report.json')] = state['report_json']
    file_data[os.path.join(state['pages_dir'], 'pages.json')] = state['pages_metadata']
    for page in state['pages']:
        file_data[os.path.join(page['dir'], 'page.json')] = page['json']
        for visual in page['visuals']:
            file_data[os.path.join(visual['dir'], 'visual.json')] = visual['json']
    for path in dirty:
        data = file_data.get(path)
        if data is None:
            continue
        if _safe_dump_json(path, data):
            written += 1
    state['_dirty_files'].clear()
    return written


# ════════════════════════════════════════════════════════════════════
#  Helpers
# ════════════════════════════════════════════════════════════════════

def _record(recovery, healer: str, target: str, severity: str,
            description: str, action: str, follow_up: str = '') -> None:
    if recovery is None:
        return
    try:
        recovery.record(
            category='visual',
            repair_type=healer,
            description=description,
            action=action,
            severity=severity,
            follow_up=follow_up,
            item_name=target,
        )
    except Exception:
        pass


def _visual_position(visual_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the position dict of a visual, or None."""
    return visual_json.get('position') if isinstance(visual_json.get('position'), dict) else None


def _canvas_dimensions(report_json: Dict[str, Any]) -> tuple:
    """Read explicit canvas size from report.json or fall back to defaults."""
    settings = report_json.get('settings') or {}
    cw = settings.get('canvasWidth') or _DEFAULT_CANVAS_WIDTH
    ch = settings.get('canvasHeight') or _DEFAULT_CANVAS_HEIGHT
    try:
        return int(cw), int(ch)
    except (TypeError, ValueError):
        return _DEFAULT_CANVAS_WIDTH, _DEFAULT_CANVAS_HEIGHT


# ════════════════════════════════════════════════════════════════════
#  v3.4 healers (10)
# ════════════════════════════════════════════════════════════════════

def _heal_visual_missing_position(state, recovery=None) -> int:
    """Visuals without an x/y position render at (0,0) and stack on top of
    each other. Default to a sensible offset so the user notices."""
    repairs = 0
    for page in state['pages']:
        offset = 0
        for visual in page['visuals']:
            pos = _visual_position(visual['json'])
            if pos is None:
                visual['json']['position'] = {
                    'x': 16, 'y': 16 + offset,
                    'width': 480, 'height': 280, 'z': offset,
                }
                _mark_dirty(state, os.path.join(visual['dir'], 'visual.json'))
                _record(recovery, 'visual_missing_position', visual['name'],
                        'warning',
                        'Visual has no position — would render at (0,0)',
                        'Inserted default position 16,16 size 480x280')
                repairs += 1
                offset += 16
            else:
                if 'x' not in pos or 'y' not in pos:
                    pos.setdefault('x', 16)
                    pos.setdefault('y', 16 + offset)
                    _mark_dirty(state, os.path.join(visual['dir'], 'visual.json'))
                    _record(recovery, 'visual_missing_position', visual['name'],
                            'warning',
                            "Visual position missing 'x' or 'y' coordinate",
                            'Filled missing coordinate with default')
                    repairs += 1
                    offset += 16
    return repairs


def _heal_visual_zero_size(state, recovery=None) -> int:
    """Visuals with width<=0 or height<=0 are invisible and trip PBI Desktop
    layout warnings. Reset to a sane minimum size."""
    repairs = 0
    for page in state['pages']:
        for visual in page['visuals']:
            pos = _visual_position(visual['json'])
            if not pos:
                continue
            w = pos.get('width', 0)
            h = pos.get('height', 0)
            try:
                w = float(w); h = float(h)
            except (TypeError, ValueError):
                w = h = 0
            if w <= 0:
                pos['width'] = max(_MIN_VISUAL_W, 480)
                _mark_dirty(state, os.path.join(visual['dir'], 'visual.json'))
                _record(recovery, 'visual_zero_size', visual['name'],
                        'warning',
                        f'Visual width was {w} (≤0) — invisible',
                        f"Reset width to {pos['width']}")
                repairs += 1
            if h <= 0:
                pos['height'] = max(_MIN_VISUAL_H, 280)
                _mark_dirty(state, os.path.join(visual['dir'], 'visual.json'))
                _record(recovery, 'visual_zero_size', visual['name'],
                        'warning',
                        f'Visual height was {h} (≤0) — invisible',
                        f"Reset height to {pos['height']}")
                repairs += 1
    return repairs


def _heal_visual_off_canvas(state, recovery=None) -> int:
    """Visual extending past canvas bounds is clipped in PBI Service.
    Clamp position+size to the canvas."""
    repairs = 0
    cw, ch = _canvas_dimensions(state['report_json'])
    for page in state['pages']:
        for visual in page['visuals']:
            pos = _visual_position(visual['json'])
            if not pos:
                continue
            try:
                x = float(pos.get('x', 0)); y = float(pos.get('y', 0))
                w = float(pos.get('width', 0)); h = float(pos.get('height', 0))
            except (TypeError, ValueError):
                continue
            changed = False
            if x < 0:
                pos['x'] = 0; changed = True
            if y < 0:
                pos['y'] = 0; changed = True
            if x + w > cw:
                pos['width'] = max(_MIN_VISUAL_W, cw - max(0, int(x)))
                changed = True
            if y + h > ch:
                pos['height'] = max(_MIN_VISUAL_H, ch - max(0, int(y)))
                changed = True
            if changed:
                _mark_dirty(state, os.path.join(visual['dir'], 'visual.json'))
                _record(recovery, 'visual_off_canvas', visual['name'],
                        'info',
                        f'Visual extended past canvas {cw}x{ch}',
                        'Clamped position/size to canvas bounds')
                repairs += 1
    return repairs


def _heal_visual_zindex_collision(state, recovery=None) -> int:
    """Two visuals on the same page sharing a zIndex render in undefined
    order. Re-assign sequential zIndex within each page (lowest first)."""
    repairs = 0
    for page in state['pages']:
        seen: Dict[int, str] = {}
        collisions: List[Dict[str, Any]] = []
        for visual in page['visuals']:
            pos = _visual_position(visual['json'])
            if not pos:
                continue
            z = pos.get('z')
            if z is None:
                continue
            try:
                z = int(z)
            except (TypeError, ValueError):
                continue
            if z in seen:
                collisions.append(visual)
            else:
                seen[z] = visual['name']
        if not collisions:
            continue
        # Reassign sequential z starting from max+1
        next_z = (max(seen.keys()) + 1) if seen else 0
        for visual in collisions:
            pos = _visual_position(visual['json'])
            if pos is None:
                continue
            old = pos.get('z')
            pos['z'] = next_z
            _mark_dirty(state, os.path.join(visual['dir'], 'visual.json'))
            _record(recovery, 'visual_zindex_collision', visual['name'],
                    'info',
                    f'Visual zIndex {old} collides with another visual',
                    f'Reassigned zIndex {old} → {next_z}')
            next_z += 1
            repairs += 1
    return repairs


def _heal_visual_missing_visualtype(state, recovery=None) -> int:
    """Visual containers without a ``visualType`` render as a blank rectangle
    in PBI Desktop. Default to ``tableEx`` so the data is at least visible."""
    repairs = 0
    for page in state['pages']:
        for visual in page['visuals']:
            vj = visual['json']
            visual_block = vj.get('visual') if isinstance(vj.get('visual'), dict) else None
            if visual_block is None:
                continue
            vt = visual_block.get('visualType')
            if vt is None or vt == '':
                visual_block['visualType'] = 'tableEx'
                _mark_dirty(state, os.path.join(visual['dir'], 'visual.json'))
                _record(recovery, 'visual_missing_visualtype', visual['name'],
                        'warning',
                        'Visual container missing visualType — would render blank',
                        "Defaulted to 'tableEx'",
                        follow_up='Pick a more appropriate visual type if needed')
                repairs += 1
    return repairs


def _heal_visual_negative_zindex(state, recovery=None) -> int:
    """Negative zIndex values cause rendering glitches in PBI Service.
    Clamp to 0."""
    repairs = 0
    for page in state['pages']:
        for visual in page['visuals']:
            pos = _visual_position(visual['json'])
            if not pos:
                continue
            z = pos.get('z')
            try:
                z = int(z) if z is not None else 0
            except (TypeError, ValueError):
                z = 0
            if z < 0:
                pos['z'] = 0
                _mark_dirty(state, os.path.join(visual['dir'], 'visual.json'))
                _record(recovery, 'visual_negative_zindex', visual['name'],
                        'info',
                        f'Visual zIndex was {z} (<0)',
                        'Clamped zIndex to 0')
                repairs += 1
    return repairs


def _heal_filter_dangling_field(state, recovery=None) -> int:
    """Report-, page-, or visual-level filters with no ``field`` reference
    are silently dropped by PBI but produce noisy load warnings. Strip them."""
    repairs = 0

    def _strip(filters: List[Any], owner: str) -> int:
        local = 0
        keep = []
        for f in filters:
            if not isinstance(f, dict):
                continue
            if not f.get('field') and not f.get('Expression') and not f.get('expression'):
                _record(recovery, 'filter_dangling_field', owner,
                        'warning',
                        'Filter has no field reference',
                        'Removed dangling filter entry')
                local += 1
                continue
            keep.append(f)
        if local:
            filters[:] = keep
        return local

    rj = state['report_json']
    if isinstance(rj.get('filters'), list):
        n = _strip(rj['filters'], 'report')
        if n:
            _mark_dirty(state, os.path.join(state['def_dir'], 'report.json'))
            repairs += n

    for page in state['pages']:
        if isinstance(page['json'].get('filters'), list):
            n = _strip(page['json']['filters'], page['name'])
            if n:
                _mark_dirty(state, os.path.join(page['dir'], 'page.json'))
                repairs += n
        for visual in page['visuals']:
            if isinstance(visual['json'].get('filters'), list):
                n = _strip(visual['json']['filters'], visual['name'])
                if n:
                    _mark_dirty(state, os.path.join(visual['dir'], 'visual.json'))
                    repairs += n
    return repairs


def _heal_bookmark_dangling_page(state, recovery=None) -> int:
    """Bookmarks targeting a page that no longer exists fail silently in PBI
    Desktop and break the bookmark navigation pane. Drop them."""
    repairs = 0
    rj = state['report_json']
    bookmarks = rj.get('bookmarks')
    if not isinstance(bookmarks, list):
        return 0
    page_names = {p['name'] for p in state['pages']}
    keep: List[Any] = []
    for bm in bookmarks:
        if not isinstance(bm, dict):
            continue
        target = (
            bm.get('targetPage')
            or bm.get('explorationState', {}).get('activeSection')
            if isinstance(bm.get('explorationState'), dict)
            else bm.get('targetPage')
        )
        if target and target not in page_names:
            _record(recovery, 'bookmark_dangling_page',
                    bm.get('name', 'unnamed_bookmark'),
                    'warning',
                    f"Bookmark targets page '{target}' which doesn't exist",
                    'Removed dangling bookmark')
            repairs += 1
            continue
        keep.append(bm)
    if repairs:
        rj['bookmarks'] = keep
        _mark_dirty(state, os.path.join(state['def_dir'], 'report.json'))
    return repairs


def _heal_pagesmeta_orphan_pageorder(state, recovery=None) -> int:
    """``pages.json`` ``pageOrder`` listing pages whose folder no longer
    exists makes PBI Desktop fail with "page not found". Sync to disk."""
    pm = state['pages_metadata']
    order = pm.get('pageOrder')
    if not isinstance(order, list):
        return 0
    on_disk = {p['name'] for p in state['pages']}
    bad = [n for n in order if n not in on_disk]
    missing = [p['name'] for p in state['pages'] if p['name'] not in order]
    if not bad and not missing:
        return 0
    new_order = [n for n in order if n in on_disk] + missing
    pm['pageOrder'] = new_order
    _mark_dirty(state, os.path.join(state['pages_dir'], 'pages.json'))
    if bad:
        _record(recovery, 'pagesmeta_orphan_pageorder', 'pages.json',
                'warning',
                f'pageOrder lists {len(bad)} non-existent pages: {bad}',
                'Removed orphan entries from pageOrder')
    if missing:
        _record(recovery, 'pagesmeta_orphan_pageorder', 'pages.json',
                'info',
                f'{len(missing)} pages on disk missing from pageOrder',
                'Appended to pageOrder')
    return len(bad) + len(missing)


def _heal_pagesmeta_missing_active(state, recovery=None) -> int:
    """``activePageName`` empty or pointing at a deleted page → PBI opens to
    a blank canvas. Default to first entry in ``pageOrder``."""
    pm = state['pages_metadata']
    active = pm.get('activePageName', '')
    order = pm.get('pageOrder') or []
    on_disk = {p['name'] for p in state['pages']}
    if not on_disk:
        return 0
    if active and active in on_disk:
        return 0
    new_active = order[0] if order and order[0] in on_disk else next(iter(sorted(on_disk)))
    pm['activePageName'] = new_active
    _mark_dirty(state, os.path.join(state['pages_dir'], 'pages.json'))
    _record(recovery, 'pagesmeta_missing_active', 'pages.json',
            'warning',
            f"activePageName was '{active}' (invalid or empty)",
            f"Set to '{new_active}'")
    return 1


def _heal_visual_query_no_select(state, recovery=None) -> int:
    """Visual ``query.queryState`` with no Values/Category projections renders
    as an empty visual. Tag with a MigrationNote so the user knows."""
    repairs = 0
    for page in state['pages']:
        for visual in page['visuals']:
            vj = visual['json']
            visual_block = vj.get('visual') if isinstance(vj.get('visual'), dict) else None
            if not visual_block:
                continue
            query = visual_block.get('query')
            if not isinstance(query, dict):
                continue
            qstate = query.get('queryState')
            if not isinstance(qstate, dict):
                continue
            # Count projection roles with at least one item
            non_empty = sum(
                1 for k, v in qstate.items()
                if isinstance(v, dict) and v.get('projections')
            )
            if non_empty > 0:
                continue
            # Add a MigrationNote so it's visible in version control diffs
            notes = visual_block.setdefault('annotations', [])
            if not any(
                isinstance(a, dict) and a.get('name') == 'MigrationNote'
                for a in notes
            ):
                notes.append({
                    'name': 'MigrationNote',
                    'value': 'Visual has no projections — empty query state',
                })
                _mark_dirty(state, os.path.join(visual['dir'], 'visual.json'))
                _record(recovery, 'visual_query_no_select', visual['name'],
                        'info',
                        'Visual queryState has no projections — empty visual',
                        'Tagged with MigrationNote for review')
                repairs += 1
    return repairs


# ════════════════════════════════════════════════════════════════════
#  Healer registry
# ════════════════════════════════════════════════════════════════════

_REPORT_HEALERS = (
    # v3.4 — PBIR / report-side
    _heal_visual_missing_position,           # 1
    _heal_visual_zero_size,                  # 2
    _heal_visual_off_canvas,                 # 3
    _heal_visual_zindex_collision,           # 4
    _heal_visual_missing_visualtype,         # 5
    _heal_visual_negative_zindex,            # 6
    _heal_filter_dangling_field,             # 7
    _heal_bookmark_dangling_page,            # 8
    _heal_pagesmeta_orphan_pageorder,        # 9
    _heal_pagesmeta_missing_active,          # 10
    _heal_visual_query_no_select,            # 11
)


def run_report_healers(state, recovery=None) -> int:
    """Run all v3.4 report healers on a loaded ReportState. Never raises."""
    if not state:
        return 0
    total = 0
    for healer in _REPORT_HEALERS:
        try:
            total += healer(state, recovery=recovery)
        except Exception as exc:  # never block migration
            logger.warning("Report healer %s raised: %s", healer.__name__, exc)
    return total


def heal_report(report_dir: str, recovery=None) -> int:
    """Convenience wrapper: load → heal → write. Returns repair count."""
    state = load_report(report_dir)
    if not state:
        return 0
    repairs = run_report_healers(state, recovery=recovery)
    if repairs:
        write_report(state)
    return repairs
