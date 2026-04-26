# v1.1 - 短信验证码服务（阿里云短信 + Redis 存储）
# 新增：频率限制（同号1分钟1次，1小时最多5次）
import random
import string
from fastapi import HTTPException, status
import redis.asyncio as aioredis
from app.core.config import settings

# 验证码有效期（秒）
SMS_CODE_TTL = 300
SMS_CODE_PREFIX = "sms_code:"
# 频率限制 Key 前缀
SMS_RATE_MINUTE_PREFIX = "sms_rate_1m:"   # 1分钟冷却
SMS_RATE_HOUR_PREFIX = "sms_rate_1h:"     # 1小时次数上限
SMS_HOUR_LIMIT = 5                        # 每小时最多发送次数


def _make_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


async def send_sms_code(phone: str, redis_client: aioredis.Redis) -> str:
    """生成验证码并发送短信，返回验证码（开发模式直接返回不发送）

    频率限制：
    - 同一手机号 60 秒内只能发送 1 次
    - 同一手机号 1 小时内最多发送 5 次
    """
    # ── 1分钟冷却检查 ──────────────────────────────────────────────
    minute_key = f"{SMS_RATE_MINUTE_PREFIX}{phone}"
    if await redis_client.exists(minute_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="发送过于频繁，请60秒后重试",
        )

    # ── 每小时次数检查 ──────────────────────────────────────────────
    hour_key = f"{SMS_RATE_HOUR_PREFIX}{phone}"
    hour_count = await redis_client.get(hour_key)
    if hour_count and int(hour_count) >= SMS_HOUR_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"今日发送次数已达上限（每小时{SMS_HOUR_LIMIT}次），请稍后再试",
        )

    # ── 生成验证码，写入 Redis ──────────────────────────────────────
    code = _make_code()
    await redis_client.setex(f"{SMS_CODE_PREFIX}{phone}", SMS_CODE_TTL, code)

    # 记录频率
    await redis_client.setex(minute_key, 60, "1")          # 1分钟冷却
    pipe = redis_client.pipeline()
    pipe.incr(hour_key)
    pipe.expire(hour_key, 3600)
    await pipe.execute()

    if settings.environment == "development":
        # 开发模式跳过真实短信发送，直接返回验证码
        return code

    # ── 生产：调用阿里云短信 ────────────────────────────────────────
    try:
        from alibabacloud_dysmsapi20170525.client import Client
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_dysmsapi20170525 import models as sms_models

        config = open_api_models.Config(
            access_key_id=settings.sms_access_key,
            access_key_secret=settings.sms_secret_key,
        )
        config.endpoint = "dysmsapi.aliyuncs.com"
        client = Client(config)
        request = sms_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=settings.sms_sign_name,
            template_code="SMS_CODE_TEMPLATE",  # 在阿里云控制台配置
            template_param=f'{{"code":"{code}"}}',
        )
        client.send_sms(request)
    except Exception:
        # 短信发送失败不阻断流程，验证码已存入 Redis
        pass

    return code


async def verify_sms_code(phone: str, code: str, redis_client: aioredis.Redis) -> bool:
    """校验验证码，成功后删除（一次性使用）"""
    key = f"{SMS_CODE_PREFIX}{phone}"
    stored = await redis_client.get(key)
    if stored and stored.decode() == code:
        await redis_client.delete(key)
        return True
    return False
