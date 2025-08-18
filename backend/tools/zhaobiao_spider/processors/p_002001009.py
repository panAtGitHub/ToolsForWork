# -*- coding: utf-8 -*-
import re
from typing import Dict, Any
from .base import BaseProcessor

BASE_DOMAIN = 'https://ggzyjy.sc.gov.cn'  # 来自你原脚本的 base_url

def _clean_html_br(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r'<br\s*/?>', '，', text, flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

class TenderPlanProcessor(BaseProcessor):
    needs_detail = False

    def extract_from_list(self, record: Dict[str, Any]) -> Dict[str, Any]:
        title = (record.get('titlenew') or '').strip()
        where = (record.get('zhuanzai') or '').strip()
        link = (record.get('linkurl') or '').strip()
        if link and not link.startswith('http'):
            if not link.startswith('/'):
                link = '/' + link
            link = BASE_DOMAIN + link
        date = (record.get('infodate') or '').strip()
        content = _clean_html_br(record.get('content') or '')

        # Python内直接计数，避免CSV里公式无效
        design_cnt = content.count('设计')
        construction_cnt = content.count('施工')

        return {
            '项目名称': title,
            '项目所在地': where,
            '网页链接': link,
            '公示时间': date,
            '内容': content,
            '设计统计': design_cnt,
            '施工统计': construction_cnt,
        }
