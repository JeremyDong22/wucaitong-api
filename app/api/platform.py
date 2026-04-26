# v1.0 - 平台管理端（W）API：品种字典 / C/B入驻审批 / C-B关系绑定
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.deps import require_platform_admin
from app.models.user import User
from app.models.product import ProductCategory, MerchantRelation
from app.models.merchant import Merchant
from app.schemas.platform import (
    ProductCategoryCreate, ProductCategoryResponse,
    MerchantApproveRequest, MerchantResponse,
    BindMerchantRelationRequest, MerchantRelationResponse,
)

router = APIRouter(prefix="/platform", tags=["平台管理"])


# ── 品种字典 ────────────────────────────────────────────────────────────────

@router.post("/products", response_model=ProductCategoryResponse)
async def create_product_category(
    body: ProductCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """上架新品种大类"""
    exists = await db.execute(
        select(ProductCategory).where(ProductCategory.category_code == body.category_code)
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="品种代码已存在")

    category = ProductCategory(
        **body.model_dump(),
        created_by=current_user.id,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/products", response_model=List[ProductCategoryResponse])
async def list_product_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """品种列表"""
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.status == "active").order_by(ProductCategory.category_name)
    )
    return result.scalars().all()


@router.patch("/products/{category_id}/status")
async def update_product_status(
    category_id: UUID,
    active: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """启用/停用品种"""
    result = await db.execute(select(ProductCategory).where(ProductCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="品种不存在")
    category.status = "active" if active else "inactive"
    await db.commit()
    return {"message": "更新成功"}


# ── 商户入驻审批 ─────────────────────────────────────────────────────────────

@router.get("/merchants", response_model=List[MerchantResponse])
async def list_merchants(
    merchant_type: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """商户列表（可按类型/状态筛选）"""
    query = select(Merchant)
    if merchant_type:
        query = query.where(Merchant.merchant_type == merchant_type)
    if status:
        query = query.where(Merchant.status == status)
    result = await db.execute(query.order_by(Merchant.created_at.desc()))
    return result.scalars().all()


@router.post("/merchants/{merchant_id}/approve")
async def approve_merchant(
    merchant_id: UUID,
    body: MerchantApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """审批商户入驻（通过/拒绝）"""
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="商户不存在")
    if merchant.status != "pending":
        raise HTTPException(status_code=400, detail="该商户已审批")

    merchant.status = "active" if body.approved else "suspended"
    merchant.approved_by = current_user.id
    from datetime import datetime
    merchant.approved_at = datetime.utcnow()
    await db.commit()
    return {"message": "审批通过" if body.approved else "已拒绝"}


# ── C-B 关系绑定 ──────────────────────────────────────────────────────────────

@router.post("/merchants/relations", response_model=MerchantRelationResponse)
async def bind_merchant_relation(
    body: BindMerchantRelationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """绑定 C-B 交易关系（按品种大类）"""
    # 校验商户类型
    b_result = await db.execute(select(Merchant).where(Merchant.id == body.upstream_merchant_id))
    b_merchant = b_result.scalar_one_or_none()
    c_result = await db.execute(select(Merchant).where(Merchant.id == body.downstream_merchant_id))
    c_merchant = c_result.scalar_one_or_none()

    if not b_merchant or b_merchant.merchant_type != "B":
        raise HTTPException(status_code=400, detail="上游商户必须是贸易收购商(B)")
    if not c_merchant or c_merchant.merchant_type != "C":
        raise HTTPException(status_code=400, detail="下游商户必须是终端收购商(C)")

    # 校验 C 包含该品种
    c_categories = c_merchant.allowed_product_categories or []
    if str(body.product_category_id) not in [str(i) for i in c_categories]:
        raise HTTPException(status_code=400, detail="终端收购商C未开通该品种，B的品种必须 ⊆ C的品种")

    # 防重复
    dup = await db.execute(
        select(MerchantRelation).where(
            MerchantRelation.upstream_merchant_id == body.upstream_merchant_id,
            MerchantRelation.downstream_merchant_id == body.downstream_merchant_id,
            MerchantRelation.product_category_id == body.product_category_id,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="该 C-B-品种 关系已存在")

    relation = MerchantRelation(
        upstream_merchant_id=body.upstream_merchant_id,
        downstream_merchant_id=body.downstream_merchant_id,
        product_category_id=body.product_category_id,
        created_by=current_user.id,
    )
    db.add(relation)
    await db.commit()
    await db.refresh(relation)
    return relation


@router.get("/merchants/relations", response_model=List[MerchantRelationResponse])
async def list_merchant_relations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """C-B 关系列表"""
    result = await db.execute(
        select(MerchantRelation).where(MerchantRelation.status == "active")
    )
    return result.scalars().all()


@router.delete("/merchants/relations/{relation_id}")
async def unbind_merchant_relation(
    relation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """解绑 C-B 关系"""
    result = await db.execute(select(MerchantRelation).where(MerchantRelation.id == relation_id))
    relation = result.scalar_one_or_none()
    if not relation:
        raise HTTPException(status_code=404, detail="关系不存在")
    relation.status = "suspended"
    await db.commit()
    return {"message": "已解绑"}
