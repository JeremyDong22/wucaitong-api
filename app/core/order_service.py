# v1.1 - 订单状态机服务（统一管理状态转换、日志记录）
# 修复：补充 committed_at 时间戳记录
# 修复：使用 SELECT FOR UPDATE 行锁防止并发重复状态变更
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.order import PurchaseOrder, OrderStatusLog, ORDER_TRANSITIONS


async def transition_order(
    order: PurchaseOrder,
    to_status: str,
    operator_id,
    operator_role: str,
    db: AsyncSession,
    remark: str = None,
) -> PurchaseOrder:
    """执行订单状态转换并记录日志。

    使用 SELECT FOR UPDATE 加行锁，防止并发场景下重复执行同一状态变更。
    """
    # 重新查询并加行锁，确保拿到最新状态
    locked = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == order.id)
        .with_for_update()
    )
    fresh = locked.scalar_one_or_none()
    if not fresh:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 以数据库最新状态为准（防止内存缓存的 order 状态已过时）
    allowed = ORDER_TRANSITIONS.get(fresh.status, [])
    if to_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不允许从 {fresh.status} 转换到 {to_status}",
        )

    from_status = fresh.status
    fresh.status = to_status

    # 更新内存中的 order 对象保持同步
    order.status = to_status

    # 记录对应节点时间戳
    now = datetime.utcnow()
    ts_map = {
        "COMMITTED":         "committed_at",
        "DISPATCHED":        "dispatched_at",
        "ARRIVED_SOURCE":    "arrived_source_at",
        "SOURCE_WEIGHED":    "source_weighed_at",
        "IN_TRANSIT":        "in_transit_at",
        "ARRIVED_WAREHOUSE": "arrived_warehouse_at",
        "WAREHOUSE_WEIGHED": "warehouse_weighed_at",
        "WAREHOUSING":       "warehousing_at",
        "WAREHOUSED":        "warehoused_at",
        "PAID":              "paid_at",
    }
    if ts_field := ts_map.get(to_status):
        if hasattr(fresh, ts_field):
            setattr(fresh, ts_field, now)
        if hasattr(order, ts_field):
            setattr(order, ts_field, now)

    # 写审计日志
    log = OrderStatusLog(
        order_id=fresh.id,
        from_status=from_status,
        to_status=to_status,
        operator_id=operator_id,
        operator_role=operator_role,
        remark=remark,
    )
    db.add(log)
    return fresh
