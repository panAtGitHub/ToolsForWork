#!/usr/bin/env python3
"""
merge_invoice_and_screenshot.py
核心逻辑保持不变，只在循环里加一个 progress_cb 回调，实时上报百分比。
"""

from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from PIL import Image, ImageOps
import fitz  # PyMuPDF

PAGE_W, PAGE_H = landscape(A4)

def render_first_page_to_png(pdf_path: Path, dpi=150):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False)
    tmp_png = pdf_path.with_suffix(".tmp_invoice.png")
    pix.save(tmp_png.as_posix())
    w_pt, h_pt = page.rect.width, page.rect.height
    doc.close()
    return tmp_png, w_pt, h_pt

def draw_pair(c: canvas.Canvas, pdf_path: Path, img_path: Path, inv_ratio: float):
    margin = gap = 20
    inv_png, pdf_w, pdf_h = render_first_page_to_png(pdf_path)
    max_inv_w = (PAGE_W - 2*margin - gap) * inv_ratio
    scale = min(max_inv_w / pdf_w, (PAGE_H - 2*margin) / pdf_h)
    inv_w, inv_h = pdf_w * scale, pdf_h * scale
    inv_x = margin
    inv_y = margin + (PAGE_H - 2*margin - inv_h)/2
    c.drawImage(inv_png.as_posix(), inv_x, inv_y, inv_w, inv_h)
    Path(inv_png).unlink(missing_ok=True)

    img = Image.open(img_path)
    img = ImageOps.exif_transpose(img)
    ratio = img.width / img.height
    avail_w = PAGE_W - inv_w - 3*margin - gap
    avail_h = PAGE_H - 2*margin
    tgt_w = min(avail_w, avail_h * ratio)
    tgt_h = tgt_w / ratio
    img_x = inv_x + inv_w + gap
    img_y = margin + (avail_h - tgt_h)/2
    tmp_img = img_path.with_suffix(".tmp_shot.png")
    img.save(tmp_img.as_posix(), dpi=(300,300))
    img.close()
    c.drawImage(tmp_img.as_posix(), img_x, img_y, tgt_w, tgt_h)
    Path(tmp_img).unlink(missing_ok=True)

# ------------------ 公开函数 ------------------ #
def merge(src: str, inv_ratio: float = 0.75, progress_cb=None):
    """
    合并 src 目录下同名前缀的 PDF+图片。
    progress_cb(pct:int) -> None  # 每完成一页调用
    返回 (output_pdf_path:str, unpaired_files:list[str])
    """
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"源目录不存在: {src}")

    # 递归扫描
    registry = {}
    for f in src_path.rglob('*'):
        if not f.is_file(): continue
        suf = f.suffix.lower()
        if suf not in ('.pdf', '.jpg', '.jpeg', '.png'): continue
        stem = f.stem.split('.')[0]
        registry.setdefault(stem, {})['pdf' if suf == '.pdf' else 'img'] = f

    pairs, unpaired = [], []
    for stem, comp in registry.items():
        if 'pdf' in comp and 'img' in comp:
            pairs.append((stem, comp['pdf'], comp['img']))
        else:
            unpaired.extend(p.name for p in comp.values())

    if not pairs:
        raise RuntimeError("未找到任何完整的 PDF + 图片 对")

    pairs.sort(key=lambda x: x[0], reverse=True)

    out_name = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(out_name, pagesize=landscape(A4))

    total = len(pairs)
    for idx, (_, pdf_f, img_f) in enumerate(pairs, 1):
        draw_pair(c, pdf_f, img_f, inv_ratio)
        c.showPage()
        if progress_cb:
            progress_cb(int(idx / total * 100))

    c.save()
    if progress_cb:
        progress_cb(100)
    return out_name, unpaired
