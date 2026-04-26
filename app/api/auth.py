# v1.1 - 认证路由：发送验证码 / 手机登录 / 微信登录 / 注册
# 修复：
#   - 登录时查询 Merchant 并将 merchant_id 写入 JWT tenant_id（解决 User/Merchant ID 混用根源）
#   - 注册时根据 role 自动创建对应档案（Broker/Driver/WarehouseKeeper）
#   - 微信登录支持多 appid→secret 映射（通过 settings.get_wx_secret）
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.security import create_access_token, hash_password
from app.core.sms import send_sms_code, verify_sms_code
from app.core.config import settings
from app.models.user import User, UserWxAuth, NaturalPerson, Enterprise
from app.models.merchant import Merchant, Broker, Driver, WarehouseKeeper
from app.schemas.auth import (
    SendSmsRequest, PhoneLoginRequest, WxLoginRequest,
    TokenResponse, RegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["认证"])

# 邀请码存储前缀（Redis）
INVITE_CODE_PREFIX = "invite:"


@router.post("/sms/send")
async def send_sms(
    body: SendSmsRequest,
    redis=Depends(get_redis),
):
    """发送短信验证码（含频率限制：60秒冷却，每小时最多5次）"""
    code = await send_sms_code(body.phone, redis)
    result = {"message": "验证码已发送"}
    if settings.environment == "development":
        result["debug_code"] = code
    return result


@router.post("/login/phone", response_model=TokenResponse)
async def login_with_phone(
    body: PhoneLoginRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """手机号 + 短信验证码登录"""
    if not await verify_sms_code(body.phone, body.code, redis):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期")

    result = await db.execute(select(User).where(User.phone == body.phone))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在，请先注册")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已停用")

    # C/B 商户登录：查询 Merchant.id 写入 JWT，解决下游接口 User/Merchant 混用问题
    merchant_id = await _resolve_merchant_id(user, db)

    token = create_access_token(str(user.id), user.role, tenant_id=merchant_id)
    return TokenResponse(access_token=token, user_id=str(user.id), role=user.role)


@router.post("/login/wx", response_model=TokenResponse)
async def login_with_wx(
    body: WxLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """微信小程序登录（code 换 open_id，支持多商户多 appid）"""
    wx_resp = await _wx_code2session(body.code, body.appid)
    open_id = wx_resp.get("openid")
    if not open_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="微信登录失败")

    result = await db.execute(
        select(UserWxAuth).where(
            UserWxAuth.mini_program_appid == body.appid,
            UserWxAuth.open_id == open_id,
        )
    )
    wx_auth = result.scalar_one_or_none()
    if not wx_auth:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="微信未绑定账号，请先注册")

    result = await db.execute(select(User).where(User.id == wx_auth.user_id))
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号不可用")

    merchant_id = await _resolve_merchant_id(user, db)
    token = create_access_token(str(user.id), user.role, tenant_id=merchant_id)
    return TokenResponse(access_token=token, user_id=str(user.id), role=user.role)


@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """注册（门户端：供应商A / 经纪人 / 司机 / 仓管员）
    注册后自动创建对应角色档案，避免下游接口找不到档案记录。
    """
    if not await verify_sms_code(body.phone, body.code, redis):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期")

    result = await db.execute(select(User).where(User.phone == body.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="手机号已注册")

    invite_data = await _parse_invite_code(body.invite_code, redis)
    role = invite_data.get("role", "A")

    # 创建用户（初始密码用随机值占位，实际通过短信验证码登录）
    user = User(
        phone=body.phone,
        password_hash=hash_password(uuid.uuid4().hex),  # 随机占位，不可登录密码
        role=role,
        status="active",
    )
    db.add(user)
    await db.flush()

    # 创建自然人档案（所有门户端角色通用）
    person = NaturalPerson(
        user_id=user.id,
        real_name=body.real_name,
        auth_status="pending",
    )
    db.add(person)
    await db.flush()

    # 根据角色创建对应档案
    if role == "BROKER":
        db.add(Broker(user_id=user.id, natural_person_id=person.id, status="active"))

    elif role == "DRIVER":
        db.add(Driver(user_id=user.id, natural_person_id=person.id, status="pending"))

    elif role == "WAREHOUSE_KEEPER":
        # 仓管员必须由商户邀请，邀请码中含 merchant_id
        merchant_id_str = invite_data.get("merchant_id")
        if not merchant_id_str:
            raise HTTPException(status_code=400, detail="仓管员邀请码无效，缺少商户信息")
        from uuid import UUID as _UUID
        db.add(WarehouseKeeper(
            user_id=user.id,
            natural_person_id=person.id,
            merchant_id=_UUID(merchant_id_str),
            sign_authorized=False,
            status="active",
        ))

    await db.commit()
    token = create_access_token(str(user.id), role)
    return TokenResponse(access_token=token, user_id=str(user.id), role=role)


# ── 内部工具函数 ──────────────────────────────────────────────────────────────

async def _resolve_merchant_id(user: User, db: AsyncSession):
    """C/B 商户：Enterprise → Merchant 查询 merchant.id，写入 JWT tenant_id。
    其他角色返回 None。
    """
    if user.role not in ("C", "B"):
        return None
    ent_result = await db.execute(select(Enterprise).where(Enterprise.user_id == user.id))
    enterprise = ent_result.scalar_one_or_none()
    if not enterprise:
        return None
    mer_result = await db.execute(
        select(Merchant).where(Merchant.enterprise_id == enterprise.id)
    )
    merchant = mer_result.scalar_one_or_none()
    return str(merchant.id) if merchant else None


async def _wx_code2session(code: str, appid: str) -> dict:
    """调用微信 code2session，使用 appid 对应的 secret"""
    wx_secret = settings.get_wx_secret(appid)
    if not wx_secret:
        raise HTTPException(status_code=400, detail=f"未配置 appid={appid} 的微信密钥")
    url = (
        f"https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={appid}&secret={wx_secret}&js_code={code}&grant_type=authorization_code"
    )
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        return resp.json()


async def _parse_invite_code(invite_code: str, redis) -> dict:
    """从 Redis 解析邀请码元数据（角色/merchant_id 等）"""
    key = f"{INVITE_CODE_PREFIX}{invite_code}"
    data = await redis.hgetall(key)
    if not data:
        return {"role": "A"}
    return {k.decode(): v.decode() for k, v in data.items()}
