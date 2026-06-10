"""Fix invalid `COUNTX(T, T[__tableau_internal_object_id__].T[Migrated Data])`
patterns in TMDL files.

The Tableau idiom `COUNT([__tableau_internal_object_id__].[Migrated Data])`
is a row-count of the secondary (blended) datasource. After migration the
secondary becomes its own table in PBI, so the equivalent is
`COUNTROWS('Table')`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MODEL_DIR = Path(
    r"C:\Tableau to Power BI\PowerBI\UC80_new\UC80\UC80.SemanticModel\definition\tables"
)

# Match COUNTX('Tbl', 'Tbl'[__tableau_internal_object_id__].'Tbl'[Migrated Data])
# (with optional whitespace and the same table name on both sides).
PAT = re.compile(
    r"COUNTX\(\s*'(?P<t>[^']+)'\s*,\s*"
    r"'(?P=t)'\[__tableau_internal_object_id__\]"
    r"\.\s*'(?P=t)'\[Migrated Data\]\s*\)"
)


def fix_text(text: str) -> tuple[str, int]:
    new_text, n = PAT.subn(lambda m: f"COUNTROWS('{m.group('t')}')", text)
    return new_text, n


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
        else:
            print(f"[skip] {f.name}")
    print(f"\nDone. {total} site(s) patched across {files_touched} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
