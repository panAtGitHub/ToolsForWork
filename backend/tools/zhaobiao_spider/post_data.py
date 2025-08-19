# -*- coding: utf-8 -*-
from copy import deepcopy
from datetime import datetime, timedelta

# === 你的原常量，保持不变 ===
url = 'https://ggzyjy.sc.gov.cn/inteligentsearch/rest/esinteligentsearch/getFullTextDataNew'

headers = {
    'Content-Type': 'application/json',
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/131.0.0.0 Safari/537.36'),
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://ggzyjy.sc.gov.cn/jyxx/002001/transactionInfo.html'
}

# 模板里不再写死时间，改为空占位
post_data_template = {
    "token": "",
    "pn": 0,
    "rn": 100,
    "sdt": "",
    "edt": "",
    "wd": "",
    "inc_wd": "",
    "exc_wd": "",
    "fields": "",
    "cnum": "",
    "sort": "{\"webdate\":\"0\"}",
    "ssort": "",
    "cl": 10000,
    "terminal": "",
    "condition": [
        {
            "fieldName": "categorynum",
            "equal": "002001009",   # 运行时会覆盖
            "notEqual": None,
            "equalList": None,
            "notEqualList": None,
            "isLike": True,
            "likeType": 2
        }
    ],
    "time": [
        {
            "fieldName": "webdate",
            "startTime": "",        # 运行时注入
            "endTime": ""           # 运行时注入
        }
    ],
    "highlights": "",
    "statistics": None,
    "unionCondition": None,
    "accuracy": "",
    "noParticiple": "1",
    "searchRange": None,
    "noWd": True
}

# ---------- 日期工具 ----------

def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def _one_month_ago_str() -> str:
    # 简化：30天前；若要“自然月”可再换算法
    return (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

def _norm_ymd(s: str, fallback: str) -> str:
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return fallback

def choose_date_range_dialog(default_start=None, default_end=None) -> tuple[str, str]:
    """优先弹窗对话框；失败则退回命令行输入。返回 YYYY-MM-DD 字符串对。"""
    ds = default_start or _one_month_ago_str()
    de = default_end or _today_str()

    # 尝试 Tk 对话框
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        s = simpledialog.askstring("开始日期", f"格式 YYYY-MM-DD（默认 {ds}）")
        e = simpledialog.askstring("结束日期", f"格式 YYYY-MM-DD（默认 {de}）")
        root.destroy()
        start = _norm_ymd(s or ds, ds)
        end = _norm_ymd(e or de, de)
        return start, end
    except Exception:
        # 退回命令行交互
        try:
            s = input(f"开始日期 YYYY-MM-DD [默认 {ds}]: ").strip()
            e = input(f"结束日期 YYYY-MM-DD [默认 {de}]: ").strip()
        except EOFError:
            s, e = "", ""
        start = _norm_ymd(s or ds, ds)
        end = _norm_ymd(e or de, de)
        return start, end

# ---------- 请求体构造 ----------

def build(equal: str, start_date: str | None = None, end_date: str | None = None, interactive: bool = True) -> dict:
    """
    构造请求体：
      - 若提供 start_date/end_date（YYYY-MM-DD），直接使用；
      - 否则在 interactive=True 时弹窗/命令行询问；
      - 都没有时用默认：今天为 end，向前30天为 start。
    """
    if start_date and end_date:
        s, e = _norm_ymd(start_date, _one_month_ago_str()), _norm_ymd(end_date, _today_str())
    elif interactive:
        s, e = choose_date_range_dialog()
    else:
        s, e = _one_month_ago_str(), _today_str()

    payload = deepcopy(post_data_template)
    payload["condition"][0]["equal"] = equal
    payload["time"][0]["startTime"] = f"{s} 00:00:00"
    payload["time"][0]["endTime"]   = f"{e} 23:59:59"
    return payload

def with_pagination(payload: dict, pn: int, rn: int) -> dict:
    p = deepcopy(payload)
    p["pn"] = pn
    p["rn"] = rn
    return p
