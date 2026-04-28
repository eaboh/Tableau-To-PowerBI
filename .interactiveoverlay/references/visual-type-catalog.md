# Visual Type Catalog — Interactive Migration Reference

Complete mapping of Tableau mark types to Power BI visual types. Use at `hook:visual-mapping` to guide override decisions.

---

## Bar Charts

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| bar | clusteredBarChart | Standard horizontal bar |
| stacked-bar | stackedBarChart | |
| 100-stacked-bar | hundredPercentStackedBarChart | |
| lollipop | clusteredBarChart | Approximation |
| butterfly | hundredPercentStackedBarChart | Negate one measure for symmetry |
| waffle | hundredPercentStackedBarChart | Approximation |

---

## Column Charts

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| column | clusteredColumnChart | Standard vertical bar |
| stacked-column | stackedColumnChart | |
| 100-stacked-column | hundredPercentStackedColumnChart | |
| histogram | clusteredColumnChart | |

---

## Line & Area Charts

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| line | lineChart | With markers |
| area | areaChart | |
| stacked-area | stackedAreaChart | |
| sparkline | lineChart | Small multiples pattern |
| bumpchart | lineChart | Rank over time |
| slopechart | lineChart | Two-point comparison |
| timeline | lineChart | Time series |

---

## Combo Charts

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| combo | lineStackedColumnComboChart | |
| dualaxis | lineClusteredColumnComboChart | Dual Y-axis |
| pareto | lineClusteredColumnComboChart | Bar + cumulative line |

---

## Pie & Donut Charts

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| pie | pieChart | |
| donut | donutChart | |
| semicircle | donutChart | |
| ring | donutChart | |
| funnel | funnel | |

---

## Scatter & Bubble

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| scatter | scatterChart | |
| bubble | scatterChart | Size encoding auto-injected |
| circle | scatterChart | |
| shape | scatterChart | |
| dot | scatterChart | Dot plot |
| packedbubble | scatterChart | |
| stripplot | scatterChart | |

---

## Maps

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| map | map | Bing Maps |
| density | map | Heat map overlay |
| polygon | map | |
| multipolygon | map | |
| filledmap | filledMap | Choropleth |
| shapemap | shapeMap | Custom shapes |
| makepoint | azureMap | Azure Maps |
| spatial | azureMap | |

---

## Table & Matrix

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| text | tableEx | Text table |
| automatic | tableEx | Default |
| table | tableEx | |
| straight-table | tableEx | |
| pivot | pivotTable | |
| pivot-table | pivotTable | |
| matrix | matrix | Cross-tab |
| heatmap | matrix | With conditional formatting |
| highlighttable | matrix | With conditional formatting |
| calendar | matrix | Calendar heatmap |

---

## KPI & Card

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| kpi | card | Single value |
| card | card | |
| multi-kpi | multiRowCard | |
| gauge | gauge | |
| meter | gauge | |
| bullet | gauge | Bullet graph |
| radial | gauge | |

---

## Treemap & Hierarchy

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| treemap | treemap | |
| square | treemap | |
| hex | treemap | |
| sunburst | sunburst | |
| decompositiontree | decompositionTree | |

---

## Waterfall & Box

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| waterfall | waterfallChart | |
| boxplot | boxAndWhisker | |
| violin | boxAndWhisker | Custom visual fallback |

---

## Specialty Charts

| Tableau Mark | PBI Visual Type | Notes |
|-------------|----------------|-------|
| wordcloud | wordCloud | AppSource custom visual |
| ribbon | ribbonChart | |
| mekko | stackedBarChart | Approximation |
| sankey | sankeyDiagram | AppSource: ChicagoITSankey1.1.0 |
| chord | chordChart | AppSource: ChicagoITChord1.0.0 |
| network | networkNavigator | AppSource: NetworkNavigator1.0.0 |
| ganttbar | ganttChart | AppSource visual |
| parallelcoordinates | lineChart | AppSource: ParallelCoordinates1.0.0 |

---

## Layout Elements

| Tableau Object | PBI Visual Type | Notes |
|---------------|----------------|-------|
| textbox / text-image | textbox | Rich text |
| image | image | Static image |
| container | actionButton | Navigation container |
| button | actionButton | |
| filter_control | slicer | Dropdown/list slicer |
| slicer | slicer | |

---

## Override Examples

Common visual type overrides users request:

| Scenario | Default Mapping | Suggested Override |
|----------|----------------|-------------------|
| Tableau bar chart → want column chart | clusteredBarChart | clusteredColumnChart |
| Tableau text table → want matrix | tableEx | matrix |
| Tableau scatter → want bubble chart | scatterChart | scatterChart (add size encoding) |
| Tableau area → want stacked area | areaChart | stackedAreaChart |
| Tableau map → want filled map | map | filledMap |
| Tableau pie → want donut | pieChart | donutChart |
| Tableau combo → want line+column | lineStackedColumnComboChart | lineClusteredColumnComboChart |
| Tableau KPI → want multi-row card | card | multiRowCard |
| Tableau box plot → want violin | boxAndWhisker | Use custom visual ViolinPlot1.0.0 |

---

## Available PBI Visual Types (for overrides)

When overriding, use these exact strings:

**Built-in:**
`clusteredBarChart`, `stackedBarChart`, `hundredPercentStackedBarChart`, `clusteredColumnChart`, `stackedColumnChart`, `hundredPercentStackedColumnChart`, `lineChart`, `areaChart`, `stackedAreaChart`, `hundredPercentStackedAreaChart`, `lineStackedColumnComboChart`, `lineClusteredColumnComboChart`, `pieChart`, `donutChart`, `funnel`, `scatterChart`, `map`, `filledMap`, `shapeMap`, `azureMap`, `tableEx`, `pivotTable`, `matrix`, `card`, `multiRowCard`, `gauge`, `treemap`, `sunburst`, `decompositionTree`, `waterfallChart`, `ribbonChart`, `boxAndWhisker`, `slicer`, `textbox`, `image`, `actionButton`

**Custom visuals (AppSource):**
`wordCloud`, `sankeyDiagram`, `chordChart`, `networkNavigator`, `ganttChart`, `bulletChart`
