import xml.etree.ElementTree as ET
root = ET.parse('examples/tableau_samples/Marketing_Campaign.twb').getroot()
for ws in root.findall('.//worksheet'):
    name = ws.get('name')
    cols = ws.findall('.//table/cols')
    rows = ws.findall('.//table/rows')
    sc = ws.findall('.//shelf-columns/field')
    sr = ws.findall('.//shelf-rows/field')
    mt = ws.find('.//mark-type')
    mc = ws.find('.//mark')
    cls = mc.get('class') if mc is not None else None
    mtt = mt.text if mt is not None else None
    print(f'WS: {name}')
    print(f'  table/cols: {len(cols)}  rows: {len(rows)}  shelf-cols: {len(sc)}  shelf-rows: {len(sr)}')
    print(f'  mark class: {cls}  mark-type elem: {mtt}')
    for c in cols:
        t = (c.text or '').strip()
        if t: print(f'   cols.text: {t[:300]}')
    for r in rows:
        t = (r.text or '').strip()
        if t: print(f'   rows.text: {t[:300]}')
    for f in sc:
        print(f'   shelf-col field: {f.text}')
    for f in sr:
        print(f'   shelf-row field: {f.text}')
    # Check encodings
    encs = ws.findall('.//encodings/*')
    for e in encs:
        print(f'   encoding {e.tag}: {dict(e.attrib)}')
