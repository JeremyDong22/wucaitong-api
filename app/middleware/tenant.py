# v1.1 - 租户隔离中间件（从请求头读取 tenant_id，供非认证接口使用）
# 注意：已认证接口的租户隔离由 deps.py 中 require_* 函数通过 JWT 负责
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """租户隔离中间件 - 从 X-Tenant-ID 请求头读取租户 ID"""

    async def dispatch(self, request: Request, call_next):
        # 从请求头获取 tenant_id（前端或网关注入）
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            request.state.tenant_id = tenant_id
        response = await call_next(request)
        return response
