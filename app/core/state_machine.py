# v1.1 - 订单状态机（兼容层，实际逻辑已移至 order_service.py）
# 保留此文件供旧代码引用，新代码请直接使用 transition_order()
from app.models.order import ORDER_TRANSITIONS
from typing import List


def can_transition(from_status: str, to_status: str) -> bool:
    """检查状态转换是否合法"""
    allowed = ORDER_TRANSITIONS.get(from_status, [])
    return to_status in allowed


def get_allowed_next_states(current_status: str) -> List[str]:
    """获取当前状态允许的下一个状态列表"""
    return ORDER_TRANSITIONS.get(current_status, [])
