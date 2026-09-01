import json, re, sys

# Baca COLAB_NOTEBOOK.py
src_path = r'c:\Nusa Putra University\S2 Magister\Semester 1\Big Data Analytics\Penelitian\gold-research\COLAB_NOTEBOOK.py'
out_path = r'c:\Nusa Putra University\S2 Magister\Semester 1\Big Data Analytics\Penelitian\gold-research\gold_price_research.ipynb'

with open(src_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Split per cell berdasarkan marker
parts = re.split(r'\n# %% \[cell \d+[^\]]*\]\n', content)

cells = []
for i, part in enumerate(parts):
    if i == 0:
        continue   # Header komentar, skip
    lines = part.strip().split('\n')
    if not lines or all(l.strip() == '' for l in lines):
        continue
    # Cell 1 adalah markdown
    if i == 1 and lines[0].strip().startswith('"""'):
        md = '\n'.join(lines).replace('"""','').strip()
        cells.append({
            'cell_type': 'markdown',
            'metadata': {},
            'source': [md]
        })
    else:
        src = []
        for j, l in enumerate(lines):
            src.append(l + '\n' if j < len(lines)-1 else l)
        cells.append({
            'cell_type': 'code',
            'execution_count': None,
            'metadata': {},
            'outputs': [],
            'source': src
        })

nb = {
    'nbformat': 4,
    'nbformat_minor': 5,
    'metadata': {
        'kernelspec': {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3'
        },
        'language_info': {
            'name': 'python',
            'version': '3.10.0'
        },
        'colab': {
            'provenance': [],
            'toc_visible': True,
            'name': 'Gold Price Predictive Analytics — Nusa Putra University'
        }
    },
    'cells': cells
}

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f'[OK] Notebook berhasil: {len(cells)} cells')
print(f'[OK] Disimpan ke: {out_path}')
