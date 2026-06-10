"""Full inspection of visuals with broken filters on Indicateurs nationaux."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
page = 'ReportSection'  # Indicateurs nationaux
vdir = os.path.join(pages_dir, page, 'visuals')

# Find visuals that have filters and a query (chart visuals)
for vid in sorted(os.listdir(vdir)):
    vjson = os.path.join(vdir, vid, 'visual.json')
    if not os.path.exists(vjson):
        continue
    with open(vjson, encoding='utf-8') as f:
        data = json.load(f)
    vis = data.get('visual', {})
    vtype = vis.get('visualType', '?')
    has_q = 'query' in vis
    fc = data.get('filterConfig', {}).get('filters', [])
    
    title_obj = vis.get('visualContainerObjects', {}).get('title', [{}])
    title = ''
    if title_obj:
        title = title_obj[0].get('properties', {}).get('text', {}).get('expr', {}).get('Literal', {}).get('Value', '')
        title = title.strip("'")
    
    if fc and has_q:
        # Get the entities used in the query
        query_entities = set()
        qs = vis.get('query', {}).get('queryState', {})
        for role, role_data in qs.items():
            for proj in role_data.get('projections', []):
                field = proj.get('field', {})
                for field_type in ('Column', 'Measure'):
                    if field_type in field:
                        e = field[field_type].get('Expression', {}).get('SourceRef', {}).get('Entity', '')
                        if e:
                            query_entities.add(e)
        
        # Get filter entities
        filter_info = []
        for fi in fc:
            prop = ''
            entity = ''
            ftype = fi.get('type', '?')
            if 'Column' in fi.get('field', {}):
                prop = fi['field']['Column'].get('Property', '')
                entity = fi['field']['Column']['Expression']['SourceRef'].get('Entity', '')
            elif 'Measure' in fi.get('field', {}):
                prop = fi['field']['Measure'].get('Property', '')
                entity = fi['field']['Measure']['Expression']['SourceRef'].get('Entity', '')
            filter_info.append((entity, prop, ftype))
        
        # Check for cross-table filters
        cross_table = []
        for entity, prop, ftype in filter_info:
            if entity and entity not in query_entities:
                cross_table.append(f'{entity}.{prop}')
        
        if cross_table:
            print(f'=== {vid[:12]} ({vtype}) | {title[:60]} ===')
            print(f'  Query entities: {sorted(query_entities)}')
            print(f'  CROSS-TABLE filters:')
            for ct in cross_table:
                print(f'    - {ct}')
            print()
