$basePath = "C:\Tableau to Power BI\PowerBI\UC80_new\UC80\UC80.Report\definition\pages"
$pages = Get-ChildItem $basePath -Directory
$findings = @()

foreach ($page in $pages) {
    $pageJson = Get-Content "$($page.FullName)\page.json" -Raw | ConvertFrom-Json
    $visualDir = Join-Path $page.FullName "visuals"
    if (-not (Test-Path $visualDir)) { continue }
    $visuals = Get-ChildItem $visualDir -Directory
    foreach ($v in $visuals) {
        $vfile = Join-Path $v.FullName "visual.json"
        if (-not (Test-Path $vfile)) { continue }
        $j = Get-Content $vfile -Raw | ConvertFrom-Json
        if (-not $j.filterConfig) { continue }
        foreach ($f in $j.filterConfig.filters) {
            if (-not $f.filter -or -not $f.filter.Where) { continue }
            foreach ($w in $f.filter.Where) {
                $cond = $w.Condition
                if (-not $cond) { continue }
                # Comparison
                if ($cond.Comparison) {
                    $cmp = $cond.Comparison
                    $left = $cmp.Left | ConvertTo-Json -Depth 20 -Compress
                    $right = $cmp.Right | ConvertTo-Json -Depth 20 -Compress
                    # Flag if Left or Right is missing the standard SQExpr shape (Column/Measure/Literal/Aggregation)
                    $leftKeys = if ($cmp.Left) { ($cmp.Left | Get-Member -MemberType NoteProperty).Name -join "," } else { "" }
                    $rightKeys = if ($cmp.Right) { ($cmp.Right | Get-Member -MemberType NoteProperty).Name -join "," } else { "" }
                    $findings += [PSCustomObject]@{
                        Page = $pageJson.displayName
                        VisualId = $v.Name
                        Field = $f.field
                        Kind = "Comparison"
                        ComparisonKind = $cmp.ComparisonKind
                        LeftKeys = $leftKeys
                        RightKeys = $rightKeys
                        LeftJson = $left
                        RightJson = $right
                    }
                }
                # In
                if ($cond.In) {
                    $inExpr = $cond.In
                    $expKeys = ($inExpr.Expressions[0] | Get-Member -MemberType NoteProperty -ErrorAction SilentlyContinue).Name -join ","
                    $valuesShape = ""
                    if ($inExpr.Values) {
                        foreach ($vg in $inExpr.Values) {
                            foreach ($lit in $vg) {
                                $litKeys = ($lit | Get-Member -MemberType NoteProperty -ErrorAction SilentlyContinue).Name -join ","
                                if ($litKeys -ne "Literal") {
                                    $valuesShape += "[$litKeys]"
                                }
                            }
                        }
                    }
                    if ($valuesShape -or $expKeys -notmatch "Column|Measure|Aggregation|HierarchyLevel") {
                        $findings += [PSCustomObject]@{
                            Page = $pageJson.displayName
                            VisualId = $v.Name
                            Field = $f.field
                            Kind = "In"
                            ComparisonKind = ""
                            LeftKeys = $expKeys
                            RightKeys = $valuesShape
                            LeftJson = ($inExpr.Expressions | ConvertTo-Json -Depth 10 -Compress)
                            RightJson = ($inExpr.Values | ConvertTo-Json -Depth 10 -Compress)
                        }
                    }
                }
            }
        }
    }
}
$findings | Format-List
"Total flagged: $($findings.Count)"
