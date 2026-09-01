"""
update_paper.py — Update JTMI_Revised_v1.docx dengan hasil re-experiment
=========================================================================
Actions:
  1. Baca model_evaluation.json (metrik terbaru)
  2. Isi semua [UPDATE AFTER RE-EXPERIMENT] placeholder
  3. Update nilai AUC-ROC lama di seluruh dokumen
  4. Sisipkan Table 5 (State-of-the-Art) di Related Work A
  5. Simpan sebagai JTMI_Revised_v2.docx
"""

import json, os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE      = r"c:\Nusa Putra University\S2 Magister\Semester 1\Big Data Analytics\Penelitian\gold-research"
EVAL_PATH = os.path.join(BASE, "output", "model_evaluation.json")
DOCX_IN   = os.path.join(BASE, "Artikel", "JTMI_Revised_v1.docx")
DOCX_OUT  = os.path.join(BASE, "Artikel", "JTMI_Revised_v2.docx")

print("[INFO] Memuat model_evaluation.json...")
with open(EVAL_PATH) as f:
    ev = json.load(f)

ACC    = ev.get("Accuracy",  0.8828)
F1     = ev.get("F1-Score",  0.8812)
PREC   = ev.get("Precision", 0.8802)
REC    = ev.get("Recall",    0.8828)
AUC    = ev.get("AUC-ROC",   0.9383)
NTRAIN = ev.get("n_train",   19960)
NTEST  = ev.get("n_test",    4990)
ACC_S  = f"{ACC*100:.2f}%"
F1_S   = f"{F1*100:.2f}%"
PREC_S = f"{PREC*100:.2f}%"
REC_S  = f"{REC*100:.2f}%"
AUC_S  = f"{AUC*100:.2f}%"
print(f"[OK] Acc={ACC_S}  F1={F1_S}  AUC={AUC_S}")
print(f"[OK] Train={NTRAIN:,}  Test={NTEST:,}")

def replace_in_para(para, reps):
    changed = False
    for run in para.runs:
        for old, new in reps.items():
            if old in run.text:
                run.text = run.text.replace(old, new)
                changed = True
    return changed

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def bold_cell(cell, text, size=8, align=WD_ALIGN_PARAGRAPH.CENTER, color=None):
    cell.text = ""
    p = cell.paragraphs[0]; p.alignment = align
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size)
    if color: r.font.color.rgb = color

def norm_cell(cell, text, size=8, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]; p.alignment = align
    r = p.add_run(text); r.font.size = Pt(size)

print("\n[INFO] Membuka dokumen...")
doc = Document(DOCX_IN)

# --- Global replacements ---
reps = {
    "[UPDATE AFTER RE-EXPERIMENT]": AUC_S,
    "93.83%": AUC_S,  "93.83": f"{AUC*100:.2f}",
    "88.28%": ACC_S,  "88.28": f"{ACC*100:.2f}",
    "88.12%": F1_S,   "88.12": f"{F1*100:.2f}",
    "88.02%": PREC_S, "88.02": f"{PREC*100:.2f}",
    "0.9383": f"{AUC:.4f}",
    "19,960": f"{NTRAIN:,}", "4,990": f"{NTEST:,}",
    "is_volatile at t": "is_volatile at t+1",
}
n = 0
for para in doc.paragraphs:
    if replace_in_para(para, reps): n += 1
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                if replace_in_para(para, reps): n += 1
print(f"[OK] {n} elemen diganti")

# --- Table 5 State-of-the-Art ---
table5 = [
    ["Study", "Algorithm", "Data Source", "Granularity", "#Instruments", "Task", "Best Metric", "Key Limitation"],
    ["Sadorsky [14]\n2021", "RF, Bagging, GBT", "Yahoo Finance", "Daily", "1 (ETF)", "Price Direction", "Acc. 85-90%", "Daily; single instr."],
    ["Jain & Bhende [16]\n2019", "SVM, RF, ANN", "Historical gold", "Daily", "1 (XAU)", "Price Direction", "Acc. 82%", "No intraday/NLP"],
    ["Kristjanpoller [17]\n2015", "ANN-GARCH", "Spot XAU/USD", "Daily", "1", "Volatility Forecast", "RMSE vs. GARCH", "No Big Data infra"],
    ["Livieris et al. [19]\n2020", "CNN-LSTM", "Gold + indices", "Daily", "3", "Price Regression", "RMSE 2.3%", "Daily; no NLP pipe"],
    ["Hajek & Novotny [32]\n2022", "Fuzzy Rule-Based", "News + gold", "Daily", "1", "Price Direction", "Acc. 68%", "Low acc.; no Spark"],
    ["Bollen et al. [21]\n2011", "Neural Net", "Twitter mood", "Daily", "Stock mkt", "Direction", "Acc. 87.6%", "Stock, not gold"],
    ["This Work", f"RF (Spark MLlib 4.2)", "Yahoo Finance + NewsAPI", "Hourly (1h)", "5 (GC=F,GLD,IAU,GDX,GDXJ)", f"Next-Hour Volatility\n(t+1 classification)", f"AUC-ROC {AUC_S}\nAcc. {ACC_S}", "Single-node; API limit"],
]

# Find insertion point
insert_idx = None
for i, para in enumerate(doc.paragraphs):
    if "Table 5" in para.text and ("State-of-the-Art" in para.text or "prior work" in para.text.lower()):
        insert_idx = i
        print(f"[OK] Posisi Table 5: paragraph {i}")
        break
if insert_idx is None:
    for i, para in enumerate(doc.paragraphs):
        if "Sadorsky" in para.text and "tree-based" in para.text:
            insert_idx = i
            print(f"[OK] Posisi Table 5 (fallback): sebelum paragraf Sadorsky {i}")
            break

if insert_idx is not None:
    ref_elem = doc.paragraphs[insert_idx]._element

    # Title paragraph
    tp = OxmlElement("w:p")
    ppr = OxmlElement("w:pPr"); jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "center")
    ppr.append(jc); tp.append(ppr)
    tr = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr"); b = OxmlElement("w:b")
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "18")
    rpr.append(b); rpr.append(sz); tr.append(rpr)
    tt = OxmlElement("w:t")
    tt.text = "Table 5. State-of-the-Art Comparison of Gold Price Prediction Studies"
    tr.append(tt); tp.append(tr)
    ref_elem.addprevious(tp)

    # Build table
    tbl = doc.add_table(rows=len(table5), cols=8)
    tbl.style = "Table Grid"
    for ri, row_data in enumerate(table5):
        row = tbl.rows[ri]
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]
            if ri == 0:
                bold_cell(cell, val, size=8, color=RGBColor(0xFF,0xFF,0xFF))
                set_cell_bg(cell, "1F3864")
            elif ri == len(table5)-1:
                bold_cell(cell, val, size=8, align=WD_ALIGN_PARAGRAPH.LEFT)
                set_cell_bg(cell, "D9E2F3")
            else:
                norm_cell(cell, val)

    # Column widths (inches)
    widths = [0.85, 0.90, 0.85, 0.70, 0.90, 0.90, 0.85, 1.05]
    for ci, col in enumerate(tbl.columns):
        for cell in col.cells:
            cell.width = Inches(widths[ci])

    tbl._tbl.addprevious = None   # prevent double-add
    ref_elem.addprevious(tbl._tbl)
    print("[OK] Table 5 disisipkan")
else:
    print("[WARN] Insert point tidak ditemukan, Table 5 di akhir dokumen")
    doc.add_heading("Table 5. State-of-the-Art Comparison", level=3)
    tbl = doc.add_table(rows=len(table5), cols=8)
    tbl.style = "Table Grid"
    for ri, row_data in enumerate(table5):
        for ci, val in enumerate(row_data):
            tbl.rows[ri].cells[ci].text = val

doc.save(DOCX_OUT)
print(f"\n[DONE] Tersimpan: {DOCX_OUT}")
print(f"{'='*55}")
print(f"  Accuracy  : {ACC_S}")
print(f"  F1-Score  : {F1_S}")
print(f"  Precision : {PREC_S}")
print(f"  Recall    : {REC_S}")
print(f"  AUC-ROC   : {AUC_S}")
print(f"  Table 5   : 7 studi + This Work (8 kolom)")
print(f"{'='*55}")
