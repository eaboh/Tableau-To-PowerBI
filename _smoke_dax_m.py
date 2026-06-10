"""Smoke test for _dax_to_m_expression with boolean+DATE pattern."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from powerbi_import.tmdl_generator import _dax_to_m_expression

tests = [
    # UC80 pattern (after self-table strip already applied)
    "DATE([Date Signature Surveillant]) >= DATE(2025, 1, 3) "
    "&& DATE([Date Signature Surveillant]) <= DATE(2026, 5, 29)",
    # Same pattern with self-table qualification
    "DATE('T'[Date Signature Surveillant]) >= DATE(2025, 1, 3) "
    "&& DATE('T'[Date Signature Surveillant]) <= DATE(2026, 5, 29)",
    # Other boolean+function compositions
    "YEAR([D]) = 2025 && MONTH([D]) >= 6",
    "[A] > 1 || [B] < 5",
    "IF(DATE([D]) >= DATE(2025,1,1), 1, 0)",
    # Cross-table ref (should stay None)
    "DATE('Other'[D]) >= DATE(2025,1,1)",
]
for t in tests:
    r = _dax_to_m_expression(t, table_name='T')
    print(f'IN:  {t}')
    print(f'OUT: {r}')
    print()
