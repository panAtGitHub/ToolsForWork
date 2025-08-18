# -*- coding: utf-8 -*-
import os, csv, json, math, time, argparse
from datetime import datetime
from .post_data import url, headers, build, with_pagination
from .http_client import create_session, post_json
from .processors import get_processor

CSV_FIELDS = ['序号','项目名称','项目所在地','网页链接','公示时间','内容','设计统计','施工统计']

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def save_csv(path: str, rows: list[dict]):
    ensure_dir(path)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for i, row in enumerate(rows, start=1):
            out = {'序号': i, **row}
            w.writerow(out)

def save_json(path: str, rows: list[dict]):
    ensure_dir(path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

def run(equal: str, rn: int, outfmt: str, start: str | None, end: str | None, no_dialog: bool):
    session = create_session()

    # 构造带日期的探测请求
    probe = build(equal, start, end, interactive=not no_dialog)
    probe['rn'] = 1
    probe['pn'] = 0
    data0 = post_json(session, url, headers, probe)
    total = (data0.get('result') or {}).get('totalcount', 0)
    print(f"总记录数: {total}")
    if total <= 0:
        return

    pages = math.ceil(total / rn)
    proc = get_processor(equal)
    rows, raw_pages = [], []

    for p in range(pages):
        pn = p * rn
        body = with_pagination(build(equal, start, end, interactive=False), pn, rn)
        data = post_json(session, url, headers, body)
        raw_pages.append(data)
        recs = (data.get('result') or {}).get('records', []) or []
        for rec in recs:
            rows.append(proc.extract_from_list(rec))
        print(f"第 {p+1}/{pages} 页，拉取 {len(recs)} 条")
        time.sleep(0.4)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    outbase = f'./output/{equal}_{ts}'
    if outfmt == 'csv':
        save_csv(f'{outbase}.csv', rows)
        print(f'CSV: {outbase}.csv')
    else:
        save_json(f'{outbase}.json', rows)
        print(f'JSON: {outbase}.json')

    with open(f'{outbase}_raw.json', 'w', encoding='utf-8') as f:
        json.dump(raw_pages, f, ensure_ascii=False, indent=2)
    print(f'原始JSON: {outbase}_raw.json')

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--equal", required=True, help="例如 002001009")
    ap.add_argument("--rn", type=int, default=100)
    ap.add_argument("--out", choices=["csv","json"], default="csv")
    ap.add_argument("--start", help="开始日期 YYYY-MM-DD（可选）")
    ap.add_argument("--end", help="结束日期 YYYY-MM-DD（可选）")
    ap.add_argument("--no-dialog", action="store_true", help="禁用交互对话框")
    args = ap.parse_args()
    run(args.equal, args.rn, args.out, args.start, args.end, args.no_dialog)
