# v1.1 - 增加微信多 appid→secret 映射（wx_app_secrets JSON 格式存入环境变量）
import json
from pydantic_settings import BaseSettings
from typing import Optional, Dict

class Settings(BaseSettings):
    # 数据库
    database_url: str
    redis_url: str

    # 阿里云 OSS
    oss_access_key: str = ""
    oss_secret_key: str = ""
    oss_bucket: str = ""
    oss_endpoint: str = ""

    # 短信
    sms_access_key: str = ""
    sms_secret_key: str = ""
    sms_sign_name: str = "物采通"

    # 微信小程序（多商户多 appid，JSON 格式：{"appid1": "secret1", ...}）
    # 单一 appid 兼容旧配置
    wx_app_id: str = ""
    wx_app_secret: str = ""
    # 多 appid 映射（生产环境推荐）
    wx_app_secrets_json: str = "{}"

    # 电子签章
    esign_app_id: str = ""
    esign_secret: str = ""

    # 开票
    invoice_api_key: str = ""

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    # 环境
    environment: str = "development"
    debug: bool = True

    # 业务参数
    weight_tolerance_percent: float = 3.0  # 磅差容忍阈值
    gps_tolerance_meters: int = 500        # GPS偏差容忍（米）
    ocr_confidence_threshold: float = 0.9  # OCR置信度阈值

    class Config:
        env_file = ".env"
        extra = "ignore"

    def get_wx_secret(self, appid: str) -> Optional[str]:
        """根据 appid 查找微信 secret（优先多 appid 映射，回退单配置）"""
        mapping: Dict[str, str] = json.loads(self.wx_app_secrets_json)
        if appid in mapping:
            return mapping[appid]
        # 兼容旧单 appid 配置
        if appid == self.wx_app_id:
            return self.wx_app_secret
        return None

settings = Settings()
