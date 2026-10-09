import re

with open('sudoku_ai_coach/static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('sudoku_ai_coach/static/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

ids_in_html = set(re.findall(r'id=["\']([^"\']+)["\']', html))
ids_in_js = re.findall(r'(?:document\.getElementById|\$)\(["\']([^"\']+)["\']\)', js)

missing = set()
for gid in ids_in_js:
    if gid not in ids_in_html:
        missing.add(gid)

print('IDs in JS but missing in HTML:', missing)
