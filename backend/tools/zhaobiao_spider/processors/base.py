# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Dict, Any
import requests

class BaseProcessor(ABC):
    needs_detail: bool = False  # 招标计划不抓详情

    @abstractmethod
    def extract_from_list(self, record: Dict[str, Any], session: requests.Session) -> Dict[str, Any]:
        """从列表记录抽取目标字段，必要时可使用 session 抓取详情页。"""
        ...
