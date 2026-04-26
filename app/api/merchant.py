# v1.1 - 商户端（C/B）API
# 修复：
#   - 删除返回 None 的 _get_tenant_id，改为 Depends(get_merchant_id)（从 JWT tenant_id 提取）
#   - 所有 merchant_id=current_user.id 改为 merchant_id=merchant_id（真实 Merchant.id）
#   - 订单号加时间戳前缀防重复
#   - confirm_commitment 同步扣减 remaining_quantity
#   - dispatch_order 校验司机与商户的归属关系
#   - pay_order 先检查幂等 key 防止重复支付
#   - 所有列表接口加 skip/limit 分页
#   - transport_arrangement 枚举统一大写
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import require_merchant, get_merchant_id
from app.core.order_service import transition_order
from app.models.user import User, NaturalPerson
from app.models.merchant import Merchant, Driver, DriverMerchantRelation, WarehouseKeeper
from app.models.broker import BrokerTask
from app.models.announcement import PurchaseAnnouncement, SupplyCommitment
from app.models.order import PurchaseOrder, ORDER_TRANSITIONS
from app.models.transport import TransportTask
from app.models.weighbridge import WeighbridgeRecord
from app.models.warehouse import WarehouseReceipt
from app.models.contract import Contract
from app.models.payment import Payment
from app.schemas.merchant import (
    AnnouncementCreate, AnnouncementResponse, ConfirmCommitmentRequest,
    OrderResponse, DispatchRequest, WeighbridgeRecordRequest,
    WarehouseReceiptRequest, BrokerTaskCreate, SupplierAdmitRequest,
    InviteRequest, PayRequest,
)

router = APIRouter(prefix="/merchant", tags=["商户端"])


def _require_merchant_id(merchant_id: Optional[UUID]) -> UUID:
    """确保 merchant_id 已从 JWT 中解析，否则拒绝请求"""
    if not merchant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号未关联商户档案，请联系平台管理员",
        )
    return merchant_id


def _make_order_no() -> str:
    """生成时间戳+随机的订单号，格式：ORD-20260426143012-A1B2C3D4"""
    return f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"


# ── 采购公告 ─────────────────────────────────────────────────────────────────

@router.post("/announcements", response_model=AnnouncementResponse)
async def create_announcement(
    body: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """发布采购公告"""
    mid = _require_merchant_id(merchant_id)
    announcement = PurchaseAnnouncement(
        merchant_id=mid,
        product_category_id=body.product_category_id,
        product_name=body.product_name,
        specification=body.specification,
        grade=body.grade,
        unit_price=body.unit_price,
        quantity=body.quantity,
        remaining_quantity=body.quantity,
        deadline=body.deadline,
        transport_arrangement=body.transport_arrangement,
        status="active",
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    return announcement


@router.get("/announcements", response_model=List[AnnouncementResponse])
async def list_announcements(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """采购公告列表"""
    mid = _require_merchant_id(merchant_id)
    result = await db.execute(
        select(PurchaseAnnouncement)
        .where(PurchaseAnnouncement.merchant_id == mid)
        .order_by(PurchaseAnnouncement.created_at.desc())
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.post("/announcements/{announcement_id}/confirm")
async def confirm_commitment(
    announcement_id: UUID,
    body: ConfirmCommitmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """确认供应商认售，生成订单并扣减公告剩余数量"""
    mid = _require_merchant_id(merchant_id)

    commitment_result = await db.execute(
        select(SupplyCommitment).where(
            SupplyCommitment.id == body.commitment_id,
            SupplyCommitment.announcement_id == announcement_id,
        )
    )
    commitment = commitment_result.scalar_one_or_none()
    if not commitment:
        raise HTTPException(status_code=404, detail="认售记录不存在")
    if commitment.status != "pending":
        raise HTTPException(status_code=400, detail="认售记录已处理")

    if not body.approved:
        commitment.status = "rejected"
        commitment.confirmed_by = current_user.id
        commitment.confirmed_at = datetime.utcnow()
        await db.commit()
        return {"message": "已拒绝"}

    # 查公告（加行锁防并发超量确认）
    ann_result = await db.execute(
        select(PurchaseAnnouncement)
        .where(PurchaseAnnouncement.id == announcement_id)
        .with_for_update()
    )
    announcement = ann_result.scalar_one()

    # 检查剩余数量是否足够
    remaining = Decimal(str(announcement.remaining_quantity))
    commit_qty = Decimal(str(commitment.quantity))
    if remaining < commit_qty:
        raise HTTPException(status_code=400, detail="认售数量超过公告剩余可供量")

    # 计算金额（Decimal 精确计算，四舍五入到分）
    unit_price = Decimal(str(announcement.unit_price))
    total_amount = (commit_qty * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    order = PurchaseOrder(
        tenant_id=mid,
        order_no=_make_order_no(),
        order_type="DIRECT",
        buyer_merchant_id=mid,
        seller_supplier_id=commitment.supplier_id,
        product_category_id=announcement.product_category_id,
        product_name=announcement.product_name,
        quantity=commitment.quantity,
        unit_price=announcement.unit_price,
        total_amount=total_amount,
        transport_arrangement=announcement.transport_arrangement,
        status="COMMITTED",
        broker_task_id=commitment.broker_id,
    )
    db.add(order)

    # 扣减剩余数量
    announcement.remaining_quantity = float(remaining - commit_qty)
    if announcement.remaining_quantity <= 0:
        announcement.status = "closed"

    commitment.status = "confirmed"
    commitment.confirmed_by = current_user.id
    commitment.confirmed_at = datetime.utcnow()
    await db.commit()
    return {"message": "已确认，订单已生成", "order_no": order.order_no}


# ── 订单管理 ─────────────────────────────────────────────────────────────────

@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    order_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """订单列表（分页）"""
    mid = _require_merchant_id(merchant_id)
    query = select(PurchaseOrder).where(PurchaseOrder.tenant_id == mid)
    if order_status:
        query = query.where(PurchaseOrder.status == order_status)
    result = await db.execute(
        query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """订单详情"""
    mid = _require_merchant_id(merchant_id)
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == order_id,
            PurchaseOrder.tenant_id == mid,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.post("/orders/{order_id}/dispatch")
async def dispatch_order(
    order_id: UUID,
    body: DispatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """派车（校验司机必须属于本商户）"""
    mid = _require_merchant_id(merchant_id)

    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == order_id,
            PurchaseOrder.tenant_id == mid,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 校验司机归属：driver 必须在 driver_merchant_relations 中与本商户关联
    driver_result = await db.execute(
        select(Driver).where(Driver.id == body.driver_id)
    )
    driver = driver_result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="司机不存在")

    rel_result = await db.execute(
        select(DriverMerchantRelation).where(
            DriverMerchantRelation.driver_id == body.driver_id,
            DriverMerchantRelation.merchant_id == mid,
            DriverMerchantRelation.status == "active",
        )
    )
    if not rel_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="该司机未与本商户关联，无法派车")

    order.driver_id = body.driver_id
    order.plate_no = body.plate_no

    await transition_order(order, "DISPATCHED", current_user.id, current_user.role, db)

    transport = TransportTask(
        order_id=order.id,
        driver_id=body.driver_id,
        plate_no=body.plate_no,
        status="assigned",
    )
    db.add(transport)
    await db.commit()
    return {"message": "派车成功"}


@router.post("/orders/{order_id}/weighbridge")
async def record_weighbridge(
    order_id: UUID,
    body: WeighbridgeRecordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """录入过磅数据（同类型防重复由数据库 UniqueConstraint 保证）"""
    mid = _require_merchant_id(merchant_id)
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == order_id,
            PurchaseOrder.tenant_id == mid,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    net_weight = Decimal(str(body.gross_weight)) - Decimal(str(body.tare_weight))
    deduction = Decimal(str(body.deduction or 0))
    actual_weight = net_weight - deduction

    record = WeighbridgeRecord(
        order_id=order_id,
        record_type=body.record_type,
        gross_weight=body.gross_weight,
        tare_weight=body.tare_weight,
        net_weight=float(net_weight),
        deduction=float(deduction),
        actual_weight=float(actual_weight),
        recorded_by=current_user.id,
        recorded_by_role=current_user.role,
        recorded_at=datetime.utcnow(),
    )
    db.add(record)

    next_status = "SOURCE_WEIGHED" if body.record_type == "source" else "WAREHOUSE_WEIGHED"
    await transition_order(order, next_status, current_user.id, current_user.role, db)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"该订单已存在{body.record_type}类型过磅记录")
    return {"message": "过磅记录已保存", "actual_weight": float(actual_weight)}


@router.post("/orders/{order_id}/warehouse")
async def confirm_warehousing(
    order_id: UUID,
    body: WarehouseReceiptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """入库确认"""
    mid = _require_merchant_id(merchant_id)
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == order_id,
            PurchaseOrder.tenant_id == mid,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    receipt = WarehouseReceipt(
        order_id=order_id,
        warehouse_id=body.warehouse_id,
        keeper_id=current_user.id,
        product_category_id=order.product_category_id,
        quantity=body.quantity,
        actual_weight=body.actual_weight,
        location=body.location,
        signed=False,
    )
    db.add(receipt)

    await transition_order(order, "WAREHOUSING", current_user.id, current_user.role, db)
    await db.commit()
    return {"message": "入库记录已创建，等待仓管员签章"}


@router.post("/orders/{order_id}/contract/sign")
async def sign_contract(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """商户端签章"""
    mid = _require_merchant_id(merchant_id)
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == order_id,
            PurchaseOrder.tenant_id == mid,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "CONTRACT_PENDING":
        raise HTTPException(status_code=400, detail="订单不在待签章状态")

    contract_result = await db.execute(
        select(Contract).where(Contract.order_id == order_id)
    )
    contract = contract_result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # TODO: 调用 e签宝 API 完成电子签章
    await transition_order(order, "CONTRACTED", current_user.id, current_user.role, db)
    await db.commit()
    return {"message": "签章完成"}


@router.post("/orders/{order_id}/pay")
async def pay_order(
    order_id: UUID,
    body: PayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """发起支付（幂等：同一 order+payer 组合只创建一条支付记录）"""
    mid = _require_merchant_id(merchant_id)
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == order_id,
            PurchaseOrder.tenant_id == mid,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "CONTRACTED":
        raise HTTPException(status_code=400, detail="合同未签章，不能支付")

    # 幂等检查：同一 order+payer 已有支付记录则直接返回
    idempotency_key = f"pay-{order_id}-{current_user.id}"
    existing = await db.execute(
        select(Payment).where(Payment.idempotency_key == idempotency_key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="支付请求已提交，请勿重复操作")

    payment = Payment(
        payment_no=f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}",
        order_id=order_id,
        payer_id=current_user.id,
        payee_id=order.seller_supplier_id or order.seller_merchant_id,
        amount=order.total_amount,
        payment_type="GOODS_PAYMENT",
        idempotency_key=idempotency_key,
        status="pending",
        channel=body.channel,
    )
    db.add(payment)

    await transition_order(order, "PAYING", current_user.id, current_user.role, db)
    await db.commit()
    # TODO: 调用支付 API（微信/支付宝），通过回调更新 payment.status 和 order.status
    return {"message": "支付请求已提交", "payment_no": payment.payment_no}


# ── 经纪人任务 ────────────────────────────────────────────────────────────────

@router.post("/broker-tasks")
async def create_broker_task(
    body: BrokerTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """创建经纪人任务"""
    mid = _require_merchant_id(merchant_id)
    task = BrokerTask(
        task_no=f"BT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
        merchant_id=mid,
        broker_id=body.broker_id,
        product_category_id=body.product_category_id,
        product_name=body.product_name,
        quantity=body.quantity,
        unit_price=body.unit_price,
        deadline=body.deadline,
        status="pending",
    )
    db.add(task)
    await db.commit()
    return {"message": "经纪人任务已创建", "task_no": task.task_no}


@router.get("/broker-tasks")
async def list_broker_tasks(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """经纪人任务列表（分页）"""
    mid = _require_merchant_id(merchant_id)
    result = await db.execute(
        select(BrokerTask)
        .where(BrokerTask.merchant_id == mid)
        .order_by(BrokerTask.created_at.desc())
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


# ── 人员管理 ──────────────────────────────────────────────────────────────────

@router.post("/suppliers")
async def admit_supplier(
    body: SupplierAdmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """准入供应商"""
    mid = _require_merchant_id(merchant_id)
    result = await db.execute(select(User).where(User.phone == body.user_phone))
    supplier_user = result.scalar_one_or_none()
    if not supplier_user:
        raise HTTPException(status_code=404, detail="用户不存在，请让供应商先注册")

    person_result = await db.execute(
        select(NaturalPerson).where(NaturalPerson.user_id == supplier_user.id)
    )
    person = person_result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=400, detail="供应商未完成实名认证")

    from app.models.product import MerchantSupplierRelation
    relation = MerchantSupplierRelation(
        merchant_id=mid,
        supplier_id=person.id,
        product_category_id=body.product_category_id,
        status="active",
    )
    db.add(relation)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="该供应商已准入")
    return {"message": "供应商准入成功"}


@router.post("/drivers")
async def invite_driver(
    body: InviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """邀请司机（生成邀请码，实际通过短信或二维码发送给司机）"""
    mid = _require_merchant_id(merchant_id)
    invite_code = uuid.uuid4().hex[:8].upper()
    # TODO: 将邀请码写入 Redis（含 role=DRIVER, merchant_id）并通过短信发送
    return {"message": "邀请链接已生成", "invite_code": invite_code}


@router.post("/warehouse-keepers")
async def add_warehouse_keeper(
    body: InviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_merchant),
    merchant_id: Optional[UUID] = Depends(get_merchant_id),
):
    """添加仓管员"""
    mid = _require_merchant_id(merchant_id)
    result = await db.execute(select(User).where(User.phone == body.user_phone))
    keeper_user = result.scalar_one_or_none()
    if not keeper_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    person_result = await db.execute(
        select(NaturalPerson).where(NaturalPerson.user_id == keeper_user.id)
    )
    person = person_result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=400, detail="用户未完成实名认证")

    keeper = WarehouseKeeper(
        user_id=keeper_user.id,
        natural_person_id=person.id,
        merchant_id=mid,
        sign_authorized=False,
        status="active",
    )
    db.add(keeper)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="该仓管员已添加")
    return {"message": "仓管员已添加"}
