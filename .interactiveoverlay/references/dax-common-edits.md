# Common DAX Edits — Interactive Migration Reference

When `hook:dax-preview` shows **approximated** conversions, use this reference to suggest corrections.

---

## LOD Expressions

### FIXED → CALCULATE + ALLEXCEPT

**Tableau:**
```
{FIXED [Region] : SUM([Sales])}
```

**Auto-converted DAX (may need review):**
```dax
CALCULATE(SUM('Sales'[Sales]), ALLEXCEPT('Sales', 'Sales'[Region]))
```

**Common fix needed:** Ensure the table name in ALLEXCEPT matches the actual model table, not the datasource name.

---

### INCLUDE → CALCULATE

**Tableau:**
```
{INCLUDE [Product] : AVG([Profit])}
```

**Auto-converted DAX:**
```dax
CALCULATE(AVERAGE('Sales'[Profit]))
```

**Note:** INCLUDE adds granularity — in most cases the simple CALCULATE is correct because PBI automatically includes visual-level filters.

---

### EXCLUDE → CALCULATE + REMOVEFILTERS

**Tableau:**
```
{EXCLUDE [Month] : SUM([Sales])}
```

**Auto-converted DAX:**
```dax
CALCULATE(SUM('Sales'[Sales]), REMOVEFILTERS('Sales'[Month]))
```

**Common fix:** Verify the column being excluded is on the correct table.

---

## Table Calculations

### RUNNING_SUM

**Tableau:** `RUNNING_SUM(SUM([Sales]))`

**Correct DAX:**
```dax
CALCULATE(
    SUM('Sales'[Sales]),
    FILTER(
        ALL('Date'[Date]),
        'Date'[Date] <= MAX('Date'[Date])
    )
)
```

**Common issue:** The auto-conversion may not identify the correct sort column. Verify the date/order column.

---

### RANK / RANK_UNIQUE / RANK_DENSE

**Tableau:** `RANK(SUM([Sales]))`

**Correct DAX:**
```dax
RANKX(ALL('Table'), [Sales Measure])
```

**Common edits:**
- Replace `ALL('Table')` with the specific dimension table being ranked
- Use `RANKX(ALL('Table'), [Measure],, ASC)` for ascending rank
- Use `RANKX(ALL('Table'), [Measure],, DESC, Dense)` for dense ranking

---

### WINDOW_SUM / WINDOW_AVG

**Tableau:** `WINDOW_SUM(SUM([Sales]), -2, 0)`

**Correct DAX (moving window):**
```dax
VAR _CurrentDate = MAX('Date'[Date])
RETURN
CALCULATE(
    SUM('Sales'[Sales]),
    DATESBETWEEN('Date'[Date], _CurrentDate - 2, _CurrentDate)
)
```

**Note:** Window size parameters (-2, 0) need manual mapping to date/row offsets.

---

## Aggregation Context

### SUM-of-IF → SUMX

**Tableau:** `SUM(IF [Category] = "Tech" THEN [Sales] END)`

**Correct DAX:**
```dax
SUMX('Sales', IF('Sales'[Category] = "Tech", 'Sales'[Sales], BLANK()))
```

**Rule:** Any `SUM(IF(...))` pattern must become `SUMX('table', IF(...))`. Same for AVG→AVERAGEX, COUNT→COUNTX.

---

### COUNTD → DISTINCTCOUNT

**Tableau:** `COUNTD([Customer ID])`

**DAX:**
```dax
DISTINCTCOUNT('Customers'[Customer ID])
```

**Common fix:** Ensure the column reference includes the correct table name.

---

## Cross-Table References

### RELATED vs LOOKUPVALUE

**When to use RELATED (manyToOne):**
```dax
RELATED('Dimension'[Column])
```
Use when there is a single active relationship from the fact table to the dimension table.

**When to use LOOKUPVALUE (manyToMany or no relationship):**
```dax
LOOKUPVALUE('OtherTable'[Value], 'OtherTable'[Key], 'CurrentTable'[Key])
```
Use when there is no direct relationship, or the relationship is manyToMany.

**Common fix:** The auto-converter may use RELATED where LOOKUPVALUE is needed (or vice versa). Check the relationship cardinality in the model.

---

## Null Handling

### ZN / IFNULL → IF(ISBLANK)

**Tableau:** `ZN([Profit])` or `IFNULL([Profit], 0)`

**DAX:**
```dax
IF(ISBLANK([Profit]), 0, [Profit])
```

**Optimization:** After `dax-optimize` runs, this becomes:
```dax
COALESCE([Profit], 0)
```

---

## Date Functions

### DATETRUNC → STARTOF*

**Tableau:** `DATETRUNC('month', [Order Date])`

**DAX by granularity:**
- `'year'` → `STARTOFYEAR('Date'[Date])`
- `'quarter'` → `STARTOFQUARTER('Date'[Date])`
- `'month'` → `STARTOFMONTH('Date'[Date])`
- `'week'` → `'Date'[Date] - WEEKDAY('Date'[Date], 2) + 1`
- `'day'` → `'Date'[Date]` (no-op)

**Common fix:** Ensure the date column references the Calendar/Date table, not raw date columns.

---

### DATEDIFF

**Tableau:** `DATEDIFF('day', [Start Date], [End Date])`

**DAX:**
```dax
DATEDIFF('Table'[Start Date], 'Table'[End Date], DAY)
```

**Note:** Argument order differs — Tableau: (unit, start, end); DAX: (start, end, unit).

---

## String Functions

### CONTAINS → CONTAINSSTRING

**Tableau:** `CONTAINS([Name], "Smith")`

**DAX:**
```dax
CONTAINSSTRING('Table'[Name], "Smith")
```

---

### String concatenation: + → &

**Tableau:** `[First Name] + " " + [Last Name]`

**DAX:**
```dax
'Table'[First Name] & " " & 'Table'[Last Name]
```

**Common fix:** The auto-converter handles this, but verify table name prefixes are correct.

---

## Security Functions

### USERNAME() → USERPRINCIPALNAME()

**Tableau:** `USERNAME()`

**DAX:**
```dax
USERPRINCIPALNAME()
```

Used in RLS role filters. The converter handles this automatically.

---

### ISMEMBEROF → RLS roles

**Tableau:** `ISMEMBEROF("Managers")`

**DAX:** Cannot be directly converted. Instead, a separate RLS role named "Managers" is created. Assign Azure AD group members to the role in Power BI Service.

---

## Tips for Reviewing Approximated Formulas

1. **Check table names** — Auto-conversion may use datasource names instead of actual table names
2. **Check column qualifiers** — DAX requires `'Table'[Column]` syntax; bare `[Column]` only works for measures
3. **Check aggregation context** — Tableau auto-aggregates; DAX measures need explicit aggregation
4. **Check relationship direction** — RELATED only works along manyToOne relationships
5. **Check date intelligence** — Tableau date functions may need Calendar table references in DAX
