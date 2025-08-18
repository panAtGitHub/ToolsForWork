# -*- coding: utf-8 -*-
from .p_002001009 import TenderPlanProcessor
from .base import BaseProcessor

REGISTRY = {
    "002001009": TenderPlanProcessor(),  # 招标计划
}

def get_processor(equal: str) -> BaseProcessor:
    try:
        return REGISTRY[equal]
    except KeyError:
        raise KeyError(f"未注册的 equal: {equal}，可用: {list(REGISTRY)}")
