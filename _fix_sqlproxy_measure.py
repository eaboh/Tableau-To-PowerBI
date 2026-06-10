"""Fix invalid `<AGG>('Table'[sqlproxy.<uuid>]).[<MeasureName>]` patterns
in TMDL files.

Background: Tableau's data-blending lets a primary datasource reference a
calculation defined on a secondary datasource via the syntax
`[sqlproxy.<id>].[<CalcName>]`. The Tableau→DAX converter literally wrapped
this in SUM(...) before propagating the trailing `.[Measure]`, producing
invalid DAX. After migration both datasources become sibling tables in the
PBI model and the secondary calculations exist as first-class measures, so
the correct collapse is just `[<MeasureName>]`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MODEL_DIR = Path(
    r"C:\Tableau to Power BI\PowerBI\UC80_new\UC80\UC80.SemanticModel\definition\tables"
)

# AGG('Table'[sqlproxy.<id>]).[<Measure>]
PAT = re.compile(
    r"(?:SUM|AVG|AVERAGE|MIN|MAX|COUNT|COUNTX|COUNTD|DISTINCTCOUNT)\(\s*"
    r"'[^']+'\[sqlproxy\.[A-Za-z0-9]+\]\s*\)"
    r"\.\[(?P<m>[^\]]+)\]"
)


def fix_text(text: str) -> tuple[str, int]:
    return PAT.subn(lambda m: f"[{m.group('m')}]", text)


def main() -> int:
    if not MODEL_DIR.is_dir():
        print(f"ERR: model dir not found: {MODEL_DIR}")
        return 2
    total = 0
    files_touched = 0
    for f in sorted(MODEL_DIR.glob("*.tmdl")):
        original = f.read_text(encoding="utf-8")
        patched, n = fix_text(original)
        if n:
            f.write_text(patched, encoding="utf-8")
            files_touched += 1
            total += n
            print(f"[OK ] {f.name}: {n} site(s) patched")
    print(f"\nDone. {total} site(s) patched across {files_touched} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
