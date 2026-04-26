# v1.0 - 认证相关请求/响应 Schema
from pydantic import BaseModel, field_validator
import re


class SendSmsRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v


class PhoneLoginRequest(BaseModel):
    phone: str
    code: str  # 短信验证码


class WxLoginRequest(BaseModel):
    code: str           # 微信小程序 wx.login() 返回的 code
    appid: str          # 小程序 AppID（多商户场景需传入）


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


class RegisterRequest(BaseModel):
    phone: str
    code: str           # 短信验证码
    real_name: str
    invite_code: str    # 邀请码（决定角色和归属商户）

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v
