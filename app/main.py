# v1.0 - 物采通平台 FastAPI 主入口，注册所有路由
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.redis_client import get_redis, close_redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("物采通平台启动中...")
    await get_redis()   # 预热 Redis 连接
    yield
    await close_redis()
    logger.info("物采通平台已关闭")


app = FastAPI(
    title="物采通平台 API",
    description="废旧物资收购行业多商户SaaS交易平台",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.api.auth import router as auth_router
from app.api.platform import router as platform_router
from app.api.merchant import router as merchant_router
from app.api.portal import router as portal_router

app.include_router(auth_router,     prefix="/api/v1")
app.include_router(platform_router, prefix="/api/v1")
app.include_router(merchant_router, prefix="/api/v1")
app.include_router(portal_router,   prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "物采通平台 API v1.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
