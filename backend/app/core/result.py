from enum import IntEnum
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")      # 在定义类或函数时先不指定具体类型，等到实际使用或调用时再动态绑定具体的类型


class CodeEnum(IntEnum):  # 使用IntEnum确保枚举值是整数
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    # 会话归属没通过。用 410 而不是 404：会话确实存在过、也可能还在，
    # 只是这个请求方不再被允许读它 —— 前端的处置是丢弃本地 sid/secret 重开一个。
    SESSION_UNAVAILABLE = 410
    SERVER_ERROR = 500
    CHECK_CODE_ERROR = 605   # 证码不正确
    RATE_LIMITED = 701       # 限流


class BaseResult(BaseModel, Generic[T]):
    """非流式 API 的统一响应，前端按 code 判断结果并读取 msg/data。

    成功响应的 code 为 200，失败响应的 data 为 None。
    此结构是当前前后端接口契约，由 Pydantic 校验并生成 OpenAPI 模型。
    """

    code: int = CodeEnum.SUCCESS
    msg: str = "success"
    data: T | None = None

    @classmethod
    def ok(cls, data: T | None = None, msg: str = "success") -> "BaseResult[T]":
        return cls(code=CodeEnum.SUCCESS, msg=msg, data=data)

    @classmethod
    def fail(cls, code: int, msg: str) -> "BaseResult[T]":
        return cls(code=code, msg=msg, data=None)
