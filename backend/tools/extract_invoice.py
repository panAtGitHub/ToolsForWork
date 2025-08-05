#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_invoice.py   (no-OCR, TXT only)
------------------------------------------------------------
在当前或指定目录递归扫描 .pdf / .PDF，提取「发票号码」「开票日期」。
• 仅依赖 pdfplumber 与 tqdm
• 发票号码匹配 ≥8 位数字
• 结果按文件名升序，写入 Tab 分隔 TXT，
  文件名形如 result_20250804_153012.txt
依赖安装：
    pip3 install pdfplumber tqdm
用法：
    cd <包含 PDF 的目录>
    python3 extract_invoice.py          # 结果文件自动生成
    # 若要指定其他目录，可：
    python3 extract_invoice.py /path/to/invoices
------------------------------------------------------------
"""

import re, pathlib, argparse, datetime
import pdfplumber
from tqdm import tqdm

# ---------- 正则 ----------
PATTERN_NUM  = re.compile(r"发票号码[:：]?\s*([0-9]{8,})")
PATTERN_DATE = re.compile(r"开票日期[:：]?\s*([0-9]{4}年[0-9]{2}月[0-9]{2}日)")

def parse_text(text: str):
    txt = text.replace(" ", "").replace("\n", "")
    num  = PATTERN_NUM.search(txt)
    date = PATTERN_DATE.search(txt)
    return (num.group(1) if num else "", date.group(1) if date else "")

def extract_from_pdf(pdf_path: pathlib.Path):
    with pdfplumber.open(str(pdf_path)) as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages)
    return parse_text(text)

def main(target_dir: pathlib.Path):
    pdf_list = list(target_dir.rglob("*.pdf")) + list(target_dir.rglob("*.PDF"))
    pdf_list.sort(key=lambda x: x.name)

    rows = []
    for pdf in tqdm(pdf_list, desc="解析发票", unit="份"):
        num, date = extract_from_pdf(pdf)
        rows.append((pdf.name, num, date))

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = target_dir / f"result_{ts}.txt"

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("文件名\t发票号码\t开票日期\n")
        for fn, num, date in rows:
            f.write(f"{fn}\t{num}\t{date}\n")

    print(f"\n✅ 已生成：{out_file}")

# ========= 供 Flask 调用的函数 ========= #
def extract(target_dir: str, progress_cb=None):
    """
    批量解析目标目录下所有 PDF（递归），生成 TSV 文本，返回输出文件路径。
        target_dir   : str | Path
        progress_cb  : callable(int pct)  解析进度回调，可为空
    """
    target_dir = pathlib.Path(target_dir)
    pdf_list = list(target_dir.rglob("*.pdf")) + list(target_dir.rglob("*.PDF"))
    pdf_list.sort(key=lambda x: x.name)

    rows = []
    total = len(pdf_list)
    for idx, pdf in enumerate(pdf_list, 1):
        num, date = extract_from_pdf(pdf)
        rows.append((pdf.name, num, date))
        if progress_cb:
            progress_cb(int(idx / total * 100))

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = target_dir / f"invoice_{ts}.txt"

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("文件名\t发票号码\t开票日期\n")
        for fn, num, date in rows:
            f.write(f"{fn}\t{num}\t{date}\n")

    if progress_cb:
        progress_cb(100)
    return str(out_file)
# ========= 命令行调用 ========= #

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量提取 PDF 发票信息（纯文本版）")
    parser.add_argument("folder", nargs="?", default=".", help="目标目录（默认为当前目录）")
    args = parser.parse_args()

    main(pathlib.Path(args.folder).expanduser().resolve())
