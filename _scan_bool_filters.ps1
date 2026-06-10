$pagesRoot = "C:\Tableau to Power BI\PowerBI\UC80_new\UC80\UC80.Report\definition\pages"
$globalBroken = 0
Get-ChildItem -Path $pagesRoot -Recurse -Filter "visual.json" | ForEach-Object {
    $j = Get-Content $_.FullName -Raw | ConvertFrom-Json
    if (-not $j.filterConfig) { return }
    foreach ($f in $j.filterConfig.filters) {
        if (-not $f.filter -or -not $f.filter.Where) { continue }
        foreach ($w in $f.filter.Where) {
            $cmp = $w.Condition.Comparison
            if ($cmp -and ($cmp.Right.Literal.Value -eq 'true' -or $cmp.Right.Literal.Value -eq 'false')) {
                $globalBroken++
                Write-Host "BROKEN COMPARISON: $($_.FullName)"
            }
            $inNode = $w.Condition.In
            if ($inNode) {
                foreach ($vg in $inNode.Values) {
                    foreach ($lit in $vg) {
                        if ($lit.Literal.Value -eq 'true' -or $lit.Literal.Value -eq 'false') {
                            $globalBroken++
                            Write-Host "BROKEN IN: $($_.FullName)"
                        }
                    }
                }
            }
        }
    }
}
Write-Host "Total broken boolean-literal filter occurrences: $globalBroken"
