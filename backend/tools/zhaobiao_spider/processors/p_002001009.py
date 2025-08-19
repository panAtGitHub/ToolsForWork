# -*- coding: utf-8 -*-
"""Processor for招标计划 (equal=002001009).

该处理器会进入每条记录的详情页，解析表格信息，并按行抓取关键信息。
"""

from typing import Dict, Any
import re

import requests
from bs4 import BeautifulSoup

from .base import BaseProcessor

BASE_DOMAIN = 'https://ggzyjy.sc.gov.cn'  # 来自原脚本的 base_url


def _clean_html_br(text: str) -> str:
    """将HTML中的<br>转换为逗号并清理多余空白。"""

    if not text:
        return ""
    t = re.sub(r'<br\s*/?>', '，', text, flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


class TenderPlanProcessor(BaseProcessor):
    """招标计划页面处理器"""

    needs_detail = True

    # 输出CSV的字段顺序（不含序号列）
    CSV_FIELDS = [
        '项目名称',
        '项目所在地',
        '网页链接',
        '公示时间',
        '内容',
        '设计统计',
        '施工统计',
        '拟招标项目名称',
        '招标人（建设单位）',
        '联系人及联系方式',
        '估算总投资（元）',
        '资金来源',
        '建设内容',
    ]

    FIELD_MAP = {
        '拟招标项目名称': ['拟招标项目名称', '项目名称'],
        '招标人（建设单位）': ['招标人', '建设单位'],
        '联系人及联系方式': ['联系人及联系方式', '联系方式', '联系人'],
        '估算总投资（元）': ['估算总投资', '估算'],
        '资金来源': ['资金来源', '来源'],
        '建设内容': ['建设内容', '内容'],
    }

    def extract_from_list(self, record: Dict[str, Any], session: requests.Session) -> Dict[str, Any]:
        """从列表记录中抓取基础字段并解析详情页。"""

        title = (record.get('titlenew') or '').strip()
        where = (record.get('zhuanzai') or '').strip()
        link = (record.get('linkurl') or '').strip()
        if link and not link.startswith('http'):
            if not link.startswith('/'):
                link = '/' + link
            link = BASE_DOMAIN + link
        date = (record.get('infodate') or '').strip()
        content = _clean_html_br(record.get('content') or '')
        design_cnt = content.count('设计')
        construction_cnt = content.count('施工')

        row = {
            '项目名称': title,
            '项目所在地': where,
            '网页链接': link,
            '公示时间': date,
            '内容': content,
            '设计统计': design_cnt,
            '施工统计': construction_cnt,
        }

        html = ''
        if link:
            resp = session.get(link, timeout=20)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            html = resp.text

        detail = self._parse_detail(html)
        if not detail.get('拟招标项目名称'):
            detail['拟招标项目名称'] = title
        row.update(detail)
        return row

    def _parse_detail(self, html: str) -> Dict[str, Any]:
        """解析详情页表格，按关键词抓取对应字段。"""

        soup = BeautifulSoup(html or '', 'html.parser')
        result = {k: '' for k in self.FIELD_MAP}

        for tr in soup.select('tr'):
            cells = tr.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            label = cells[0].get_text(strip=True)
            value = ' '.join(c.get_text(separator=' ', strip=True) for c in cells[1:])
            for field, kws in self.FIELD_MAP.items():
                if any(kw in label for kw in kws) and not result[field]:
                    result[field] = value

        return result

