"""Quick test for _strip_m_inline_comments and dax_converter comment stripping."""
import sys
sys.path.insert(0, '.')

from powerbi_import.tmdl_generator import _strip_m_inline_comments

print("=== _strip_m_inline_comments tests ===\n")

# Test 1: no comments
t1 = 'each if [X] = 1 then 1 else null'
r1 = _strip_m_inline_comments(t1)
print(f"Test 1 (no comment): {r1}")
assert r1 == t1, f"FAIL: {r1!r}"

# Test 2: multiline with // comment
t2 = 'each if [X] = 1  //New v1.6\n or [Y] = 2 then 1 else null'
r2 = _strip_m_inline_comments(t2)
print(f"Test 2 (multiline): {r2!r}")
assert '//New' not in r2
assert '[Y] = 2' in r2

# Test 3: single-line with [bracket] after comment
t3 = 'each if [X] = 1  //New v1.6 [Y] = 2 then yes else null'
r3 = _strip_m_inline_comments(t3)
print(f"Test 3 (single-line bracket): {r3!r}")
assert '//New' not in r3
assert '[Y] = 2' in r3

# Test 4: #"each if" / #"else if" corruption
t4 = '#"each if 2" =1 then [Ps Service] #"else if 2" =2 then [X] else null'
r4 = _strip_m_inline_comments(t4)
print(f"Test 4 (#each if fix): {r4!r}")
assert 'each if 2 =1' in r4
assert 'else if 2 =2' in r4
assert '#"each' not in r4

# Test 5: // inside string literal should NOT be stripped
t5 = 'each if [URL] = "http://example.com" then 1 else 0'
r5 = _strip_m_inline_comments(t5)
print(f"Test 5 (// in string): {r5!r}")
assert r5 == t5, f"FAIL: string content was modified"

# Test 6: trailing // with no code after
t6 = 'each [X] + [Y]  //sum of X and Y'
r6 = _strip_m_inline_comments(t6)
print(f"Test 6 (trailing comment): {r6!r}")
assert '//' not in r6

print("\n=== DAX converter comment stripping ===\n")

import re
# Simulate the dax converter's comment stripping
def strip_comments(dax):
    dax = re.sub(r'(?m)^\s*//[^\r\n]*', '', dax)  # Full-line
    dax = re.sub(r'(?m)\s*//[^\r\n"]*$', '', dax)  # Trailing
    _RE_NEWLINES = re.compile(r'[\r\n]+\s*')
    dax = _RE_NEWLINES.sub(' ', dax)
    return dax.strip()

# Test: multi-line formula with // annotations
formula = '''if ([Ps Service] = "SEC-ELES"  or  //New v1.6
[Ps Service] = "SEC-EME 1"  or  //New v1.6
[Ps Service] = "SEC-EME 2")
then "EC DIPDE" else null'''
result = strip_comments(formula)
print(f"Multi-line formula: {result!r}")
assert '//New' not in result
assert '[Ps Service] = "SEC-EME 1"' in result
assert '[Ps Service] = "SEC-EME 2"' in result

# Test: // in string should be preserved
formula2 = 'if [URL] = "http://foo.com" then "yes" else "no"'
result2 = strip_comments(formula2)
print(f"URL in string: {result2!r}")
assert 'http://foo.com' in result2

print("\n=== All tests passed! ===")
