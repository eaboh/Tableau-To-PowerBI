"""One-off: push fragile DAX calculated columns into Power Query M.

Targets the UC80 PBIP semantic model. For each entry in TARGETS:
  1. Replace the calc column declaration `column 'X' = <DAX>` with a
     plain source-column block (`column 'X'` + `sourceColumn: 'X'`).
  2. Inject a `Table.AddColumn` step at the end of the partition's
     `let .. in` block (just before `Result = #"<lastStep>"`) and
     update `Result` to reference the new step.

The script is idempotent — running it twice is a no-op.
"""

from __future__ import annotations

import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MODEL_DIR = Path(r"C:\Tableau to Power BI\PowerBI\UC80_new\UC80\UC80.SemanticModel\definition\tables")


@dataclass
class Target:
    file_name: str
    column_name: str           # exact column name (without surrounding quotes)
    m_expression: str          # M expression body (after `each `)
    m_type: str = "type logical"


# Each target: a single calc column to push to M.
TARGETS: list[Target] = [
    Target(
        file_name="EDH_OBSERVABLES_UC80 (2).tmdl",
        column_name="FLT Ps date de modification PAR",
        m_expression=(
            "let d = try Date.From([#\"Ps Date Modification\"]) otherwise null "
            "in d <> null and d >= #date(2025, 1, 3) and d <= #date(2026, 5, 29)"
        ),
    ),
    Target(
        file_name="EDH_OBSERVATION_UC80 (2).tmdl",
        column_name="Date Signature Surveillant PAR",
        m_expression=(
            "let d = try Date.From([#\"Date Signature Surveillant\"]) otherwise null "
            "in d <> null and d >= #date(2025, 1, 3) and d <= Date.From(DateTime.LocalNow())"
        ),
    ),
    Target(
        file_name="EDH_PROGRAMMES_SURVEILLANCES_UC80 (2).tmdl",
        column_name="Date Modification PAR",
        m_expression=(
            "let d = try Date.From([#\"Ps Date Modification\"]) otherwise null "
            "in d <> null and d >= #date(2025, 1, 3) and d <= #date(2026, 5, 29)"
        ),
    ),
    Target(
        file_name="EDH_UTILISATION_CATALOGUE_NATIONAL_D_UC80 (2).tmdl",
        column_name="FLT Date Signature surveillant PAR",
        m_expression=(
            "let d = try Date.From([#\"Date Signature Surveillant\"]) otherwise null "
            "in d <> null and d >= #date(2025, 1, 3) and d <= #date(2026, 5, 29)"
        ),
    ),
    Target(
        file_name="EDH_UTILISATION_CATALOGUE_NATIONAL_HISTORIQUE_UC80.tmdl",
        column_name="Date signature surveillance PAR",
        m_expression=(
            "let d = try Date.From([#\"Date Signature Surveillant\"]) otherwise null "
            "in d <> null and d >= #date(2025, 1, 3) and d <= #date(2026, 5, 29)"
        ),
    ),
    Target(
        file_name="EDH_UTILISATION_CATALOGUE_NATIONAL_UC80 (2).tmdl",
        column_name="Date Signature Surveillant PAR",
        m_expression=(
            "let d = try Date.From([#\"Date Signature Surveillant\"]) otherwise null "
            "in d <> null and d >= #date(2025, 1, 3) and d <= #date(2026, 5, 29)"
        ),
    ),
    # Fix the malformed Bool_Commentaire too (push to M).
    Target(
        file_name="EDH_OBSERVATION_UC80 (2).tmdl",
        column_name="Bool_Commentaire",
        m_expression=(
            "if [#\"Commentaire\"] = null or [#\"Commentaire\"] = \"\" then 0 else 1"
        ),
        m_type="Int64.Type",
    ),
    # AT is a simple text column. Push to M so it loads cleanly at refresh time.
    Target(
        file_name="EDH_OBSERVATION_UC80 (2).tmdl",
        column_name="AT",
        m_expression=(
            "if Text.Length(Text.From([#\"Surveillant Nni\"])) > 6 then \"AT\" else \"EDF\""
        ),
        m_type="type text",
    ),
]


def quote_tmdl_name(name: str) -> str:
    """Return a TMDL identifier — quoted with single quotes if needed."""
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        return name
    # Escape single-quotes by doubling.
    return "'" + name.replace("'", "''") + "'"


def m_step_name(col_name: str) -> str:
    """Build the M step identifier `#"Added <col>"` for the AddColumn line."""
    return '#"Added ' + col_name.replace('"', '""') + '"'


def find_calc_column_block(lines: list[str], col_name: str):
    """Return (decl_idx, props_end_idx) for the `column 'X' = ...` block.

    `decl_idx`        — index of the `column 'X' = ...` line.
    `props_end_idx`   — exclusive end of the property block (index of the
                        first blank line that follows the `summarizeBy`
                        line, or the line after `annotation Summarization...`
                        if the block has no trailing blank).
    Returns None if not found or if the column has no `=` (already migrated).
    """
    qname_apos = "'" + col_name + "'"
    pat_quoted = re.compile(r"^\s*column\s+" + re.escape(qname_apos) + r"\s*=", re.UNICODE)
    pat_bare = re.compile(r"^\s*column\s+" + re.escape(col_name) + r"\s*=", re.UNICODE)
    decl_idx = None
    for i, line in enumerate(lines):
        if pat_quoted.match(line) or pat_bare.match(line):
            decl_idx = i
            break
    if decl_idx is None:
        return None
    # Find end of properties block: scan until we hit a blank line followed
    # by a non-property (next column / measure / partition / table-end), or
    # we hit the next `column ` declaration.
    end = decl_idx + 1
    while end < len(lines):
        s = lines[end].strip()
        if s.startswith("column ") or s.startswith("measure ") or s.startswith("partition "):
            break
        end += 1
    return decl_idx, end


def rewrite_calc_block(lines: list[str], decl_idx: int, props_end: int, col_name: str) -> list[str]:
    """Replace the calc-column block with a plain source-column block.

    Preserves indentation, dataType, lineageTag, summarizeBy, formatString,
    and annotations. Strips the `= <expr>` from the declaration line and
    inserts `sourceColumn: 'X'` right after `summarizeBy: none` if absent.
    """
    decl_line = lines[decl_idx]
    # Strip `= <expr>` keeping leading whitespace and `column 'X'`.
    new_decl = re.sub(r"\s*=.*$", "", decl_line.rstrip("\r\n"))
    # Determine indent of property lines (first non-blank line after decl).
    prop_indent = ""
    for j in range(decl_idx + 1, props_end):
        if lines[j].strip():
            prop_indent = re.match(r"^[\t ]*", lines[j]).group(0)
            break
    src_decl = f"{prop_indent}sourceColumn: {quote_tmdl_name(col_name)}\n"

    block = lines[decl_idx:props_end]
    # Rebuild block.
    rebuilt: list[str] = []
    rebuilt.append(new_decl + "\n")
    has_source = False
    inserted_source = False
    for j, ln in enumerate(block[1:], start=1):
        if re.match(r"^\s*sourceColumn\s*:", ln):
            has_source = True
        rebuilt.append(ln)
        # After summarizeBy line, insert sourceColumn if not present anywhere
        if (not inserted_source and not has_source
                and re.match(r"^\s*summarizeBy\s*:", ln)):
            rebuilt.append(src_decl)
            inserted_source = True
    if not inserted_source and not has_source:
        # Fallback: append before the trailing blank/annotation lines.
        rebuilt.append(src_decl)
    return lines[:decl_idx] + rebuilt + lines[props_end:]


def find_partition_result(lines: list[str]):
    """Return (result_idx, last_step_token) for the `Result = #"..."` line
    inside the partition's `let .. in` block.

    Returns None if no such line is found.
    """
    pat = re.compile(r'^(\s*)Result\s*=\s*(#?\"[^\"]+\"|[A-Za-z_][\w]*)\s*,?\s*$')
    for i, line in enumerate(lines):
        m = pat.match(line)
        if m:
            return i, m.group(2), m.group(1)
    return None


def inject_m_step(lines: list[str], target: Target) -> list[str]:
    """Inject Table.AddColumn step before the `Result =` line."""
    found = find_partition_result(lines)
    if not found:
        raise RuntimeError("partition Result line not found")
    result_idx, last_step_token, indent = found
    new_step_id = m_step_name(target.column_name)

    # Idempotency: bail if the new step name already exists in the file.
    for ln in lines:
        if new_step_id in ln:
            return lines  # already injected

    add_line = (
        f'{indent}{new_step_id} = Table.AddColumn('
        f'{last_step_token}, "{target.column_name}", '
        f'each {target.m_expression}, {target.m_type}),\n'
    )
    new_result = f"{indent}Result = {new_step_id}\n"
    return lines[:result_idx] + [add_line] + [new_result] + lines[result_idx + 1:]


def process_file(target: Target) -> bool:
    path = MODEL_DIR / target.file_name
    if not path.exists():
        print(f"[SKIP] missing file: {path}")
        return False
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    # Preserve line endings (TMDL files are typically LF).
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)

    block = find_calc_column_block(lines, target.column_name)
    if not block:
        # Maybe already migrated. Check if column block has sourceColumn.
        re_decl = re.compile(
            r"^\s*column\s+'?" + re.escape(target.column_name) + r"'?\s*$",
            re.UNICODE,
        )
        already = any(re_decl.match(ln) for ln in lines)
        if already:
            # Still inject M step if not present.
            try:
                lines2 = inject_m_step(lines, target)
            except RuntimeError as e:
                print(f"[WARN] {target.file_name}::{target.column_name}: {e}")
                return False
            if lines2 == lines:
                print(f"[OK ] {target.file_name}::{target.column_name} (already migrated)")
                return False
            with io.open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write("".join(lines2))
            print(f"[FIX] {target.file_name}::{target.column_name} (M step injected)")
            return True
        print(f"[MISS] {target.file_name}::{target.column_name} (no calc block found)")
        return False

    decl_idx, props_end = block
    lines2 = rewrite_calc_block(lines, decl_idx, props_end, target.column_name)
    lines2 = inject_m_step(lines2, target)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(lines2))
    print(f"[OK ] {target.file_name}::{target.column_name} -> Power Query M")
    return True


def main() -> int:
    changed = 0
    for t in TARGETS:
        if process_file(t):
            changed += 1
    print(f"\nDone. {changed}/{len(TARGETS)} targets updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
