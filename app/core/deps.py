# v1.1 - FastAPI 依赖注入：当前用户、商户ID、租户、权限校验
# 新增：get_merchant_id（从 JWT tenant_id 字段提取商户ID，避免 User.id 和 Merchant.id 混用）
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT 获取当前登录用户"""
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效令牌")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌验证失败")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已停用")
    return user


async def get_merchant_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Optional[UUID]:
    """从 JWT payload 的 tenant_id 字段提取 Merchant.id。
    C/B 用户登录时由 auth.py 写入；其他角色返回 None。
    """
    try:
        payload = decode_access_token(credentials.credentials)
        tid = payload.get("tenant_id")
        return UUID(tid) if tid else None
    except Exception:
        return None


def require_role(*roles: str):
    """角色权限校验装饰器工厂"""
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限，需要角色：{'/'.join(roles)}"
            )
        return current_user
    return checker


# 常用角色依赖
require_platform_admin = require_role("W")
require_merchant = require_role("C", "B")
require_any = require_role("W", "C", "B", "A", "BROKER", "DRIVER", "WAREHOUSE_KEEPER")
