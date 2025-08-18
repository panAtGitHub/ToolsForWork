# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProcessor(ABC):
    needs_detail: bool = False  # 招标计划不抓详情

    @abstractmethod
    def extract_from_list(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """从列表记录抽取目标字段。"""
        ...
