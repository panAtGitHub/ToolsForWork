#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_invoice.py  —  批量解析发票 / 行程报销单
排序规则：
  1) 文件名以数字或数字.数字开头 → 自然升序
  2) 文件名以 YYYY-MM-DD 开头 → 日期倒序
  3) 其余保持原顺序
依赖：pdfplumber
"""

import re
import datetime
from pathlib import Path
from typing import List, Tuple
import pdfplumber


# ---------- 工具函数 ----------
def format_workmeal(stem: str) -> str:
    """若文件名含中文逗号金额 → 生成工作餐说明列"""
    m = re.search(r'，([\d.]+)$', stem)
    if not m:
        return ""
    total = float(m.group(1))
    if total < 50:
        return "1人，事由：加班"
    people = max(1, round(total / 45))
    while total / people >= 50:
        people += 1
    while total / people <= 40 and people > 1:
        people -= 1
    per = int(total / people)
    return f"{people}人，人均约{per}元，事由：加班"


def extract_invoice_page1(pdf_path: Path):
    """普通发票：抓发票号码(20 或 8 位)和日期"""
    with pdfplumber.open(pdf_path) as doc:
        text = doc.pages[0].extract_text() or ""

    m_num = re.search(r'发票号码[：:\s]*([0-9]{20}|[0-9]{8})', text)
    if m_num:
        num = m_num.group(1)
    else:
        m_any = re.search(r'\b([0-9]{20}|[0-9]{8})\b', text)
        num = m_any.group(1) if m_any else ""

    m_date = re.search(r'(\d{4}[年/-]\d{2}[月/-]\d{2}[日]?)', text)
    date = m_date.group(1) if m_date else ""
    return num, date


def extract_trip_page1(pdf_path: Path):
    """行程报销单：抓‘YYYY-MM-DD 至 YYYY-MM-DD’"""
    with pdfplumber.open(pdf_path) as doc:
        text = doc.pages[0].extract_text() or ""
    m = re.search(r'(\d{4}-\d{2}-\d{2})\s*至\s*(\d{4}-\d{2}-\d{2})', text)
    if m:
        date_range = f"{m.group(1)} 至 {m.group(2)}"
        note = f"行程起止日期：{date_range}，外差车费，施工配合、开会等"
    else:
        note = "行程起止日期未识别"
    return note


# ---------- 自然排序 key ----------
def natural_key(s: str) -> Tuple[int, ...]:
    """'1.10.3' -> (1,10,3)"""
    return tuple(int(x) for x in s.split('.'))


# ---------- 主批量函数 ----------
def extract(folder: str, progress_cb=None) -> str:
    folder = Path(folder)
    pdfs: List[Path] = sorted(folder.rglob("*.pdf"), key=lambda p: p.name.lower())

    rows, grp1, grp2, grp3 = [], [], [], []
    total = len(pdfs)

    for idx, pdf in enumerate(pdfs, 1):
        stem = pdf.stem
        if "行程" in stem:                               # 行程报销单
            note = extract_trip_page1(pdf)
            num, date = "", ""
        else:                                            # 普通发票
            num, date = extract_invoice_page1(pdf)
            note = format_workmeal(stem)

        row = (pdf.name, num, date, note)

        # ---- 分类判断（先判日期，后判数字） ----
        if re.match(r'^\d{4}-\d{2}-\d{2}', stem):        # 段 2：日期前缀
            date_key = datetime.datetime.strptime(stem[:10], "%Y-%m-%d")
            grp2.append((date_key, row))

        elif re.match(r'^\d+(?:\.\d+)*(?=[^\d.]|$)', stem):  # 段 1：数字(点)前缀
            num_prefix = re.match(r'^\d+(?:\.\d+)*', stem).group(0)
            grp1.append((natural_key(num_prefix), row))

        else:                                            # 其他
            grp3.append(row)


        if progress_cb:
            progress_cb(int(idx / total * 100))

    # 排序
    grp1_sorted = [r for _, r in sorted(grp1, key=lambda x: x[0])]
    grp2_sorted = [r for _, r in sorted(grp2, key=lambda x: x[0], reverse=True)]

    # 合并顺序：段1 → 段2 → 其他
    rows = grp1_sorted + grp2_sorted + grp3

    # 输出
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = folder / f"invoice_{ts}.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("文件名\t发票号码\t开票日期\t说明\n")
        for fn, num, date, note in rows:
            f.write(f"{fn}\t{num}\t{date}\t{note}\n")

    if progress_cb:
        progress_cb(100)
    return str(out_file)


# ---------- CLI 测试 ----------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="批量解析发票 / 行程报销单 并排序")
    ap.add_argument("folder", nargs="?", default=".", help="待解析目录")
    args = ap.parse_args()

    def bar(p): print(f"\r进度 {p}%", end="", flush=True)

    output = extract(args.folder, bar)
    print(f"\n✅ 结果已保存到 {output}")
