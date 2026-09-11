"""用 Pydantic v2 + OpenAI 兼容接口抽取严格类型的硬件诊断报告。

Structured Outputs 会把 Pydantic 模型编译成 JSON Schema，并以
`response_format.type = json_schema` + `strict=true` 交给服务端约束解码。
模型在生成阶段就被限制为：字段名、类型、枚举值必须与 schema 一致。

兼容性：
- OpenAI、较新的 vLLM / llama.cpp OpenAI 兼容端点：走 `chat.completions.parse()`。
- 官方 DeepSeek Chat Completions、部分本地服务只支持 `json_object`：
  此时 schema 不会在服务端强制执行，本模块会降级，并在客户端用
  `HardwareDiagnosticReport.model_validate_json()` 做同等严格校验。
"""

from __future__ import annotations

import json
import os
import re
from enum import StrEnum
from typing import Final

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ContentFilterFinishReasonError,
    InternalServerError,
    LengthFinishReasonError,
    NotFoundError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError


# ---------------------------------------------------------------------------
# 1. 严格强类型数据模型
# ---------------------------------------------------------------------------


class DeviceStatus(StrEnum):
    """设备运行状态。取值必须是这三个中文枚举成员之一。"""

    NORMAL = "正常"
    OVERLOAD = "过载"
    DISCONNECTED = "断联"


class HardwareDiagnosticReport(BaseModel):
    """硬件诊断报告。

    `strict=True`：禁止隐式类型转换（例如字符串 `"5012"` 不能当成 int）。
    `extra="forbid"`：禁止 schema 之外的字段。
    `frozen=True`：实例创建后不可改，避免下游误改已校验数据。
    """

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        validate_default=True,
        str_strip_whitespace=True,
    )

    device_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="设备唯一标识。",
    )
    status: DeviceStatus = Field(
        ...,
        description="设备状态，只能是：正常、过载、断联。",
    )
    error_code: int = Field(
        ...,
        ge=0,
        le=999_999,
        description="诊断错误码。无错误时为 0。",
    )


# ---------------------------------------------------------------------------
# 2. 应用层错误
# ---------------------------------------------------------------------------


class DiagnosticExtractionError(Exception):
    """从大模型抽取 HardwareDiagnosticReport 失败。"""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


# ---------------------------------------------------------------------------
# 3. Prompt 与 schema
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT: Final[str] = (
    "你是硬件诊断信息抽取器。"
    "只根据用户提供的巡检/日志文本填写 JSON。"
    "不得编造文本中不存在的设备号或错误码。"
    "若文本未给出错误码，error_code 填 0。"
    "status 只能取：正常、过载、断联。"
)

_JSON_FENCE_RE: Final[re.Pattern[str]] = re.compile(
    r"^```(?:json)?\s*([\s\S]*?)\s*```$",
    re.IGNORECASE,
)


def _json_schema() -> dict[str, object]:
    """供降级路径写入 Prompt 的 JSON Schema（与 Pydantic 模型一致）。"""
    schema = HardwareDiagnosticReport.model_json_schema()
    schema["additionalProperties"] = False
    return schema


def _build_messages(source_text: str, *, require_json_keyword: bool) -> list[dict[str, str]]:
    schema_text = json.dumps(_json_schema(), ensure_ascii=False, indent=2)
    json_hint = (
        "你必须输出一个 JSON 对象，不要输出 Markdown，不要输出解释文字。"
        if require_json_keyword
        else "按给定 schema 输出。"
    )
    system = (
        f"{_SYSTEM_PROMPT}\n{json_hint}\n"
        f"JSON Schema:\n{schema_text}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": source_text},
    ]


def _strip_markdown_fence(raw: str) -> str:
    text = raw.strip()
    matched = _JSON_FENCE_RE.match(text)
    if matched:
        return matched.group(1).strip()
    return text


def build_client() -> OpenAI:
    """连接 OpenAI 兼容端点。本地 DeepSeek / vLLM / Ollama 把 BASE_URL 指过去即可。"""
    return OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", "not-needed"),
        base_url=os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1"),
        timeout=float(os.environ.get("OPENAI_TIMEOUT", "60")),
        max_retries=int(os.environ.get("OPENAI_MAX_RETRIES", "2")),
    )


def _model_name() -> str:
    return os.environ.get("OPENAI_MODEL", "deepseek-chat")


def _unsupported_json_schema(exc: BadRequestError) -> bool:
    body = str(exc.body or "") + " " + str(exc.message or "")
    lowered = body.lower()
    hints = (
        "json_schema",
        "response_format",
        "unavailable",
        "not supported",
        "unknown parameter",
        "invalid_request_error",
        "extra inputs are not permitted",
    )
    return any(h in lowered for h in hints)


# ---------------------------------------------------------------------------
# 4. 两条抽取路径
# ---------------------------------------------------------------------------


def _extract_via_structured_outputs(
    client: OpenAI,
    source_text: str,
    *,
    model: str,
    max_tokens: int,
) -> HardwareDiagnosticReport:
    """服务端约束解码：SDK 把模型转成 strict JSON Schema，响应直接反序列化为 Pydantic 实例。"""
    completion = client.chat.completions.parse(
        model=model,
        messages=_build_messages(source_text, require_json_keyword=False),
        response_format=HardwareDiagnosticReport,
        max_tokens=max_tokens,
        temperature=0,
    )
    message = completion.choices[0].message
    if message.refusal:
        raise DiagnosticExtractionError(
            f"模型拒绝生成该结构：{message.refusal}",
            retryable=False,
        )
    if message.parsed is None:
        raise DiagnosticExtractionError("Structured Outputs 未返回 parsed 对象。", retryable=True)
    return message.parsed


def _extract_via_json_object(
    client: OpenAI,
    source_text: str,
    *,
    model: str,
    max_tokens: int,
) -> HardwareDiagnosticReport:
    """仅保证输出是 JSON 对象。字段合法性完全由本机 Pydantic 严格校验兜底。"""
    completion = client.chat.completions.create(
        model=model,
        messages=_build_messages(source_text, require_json_keyword=True),
        response_format={"type": "json_object"},
        max_tokens=max_tokens,
        temperature=0,
    )
    choice = completion.choices[0]
    if choice.finish_reason == "length":
        raise DiagnosticExtractionError(
            "输出在 JSON 闭合前被截断。增大 max_tokens 后重试。",
            retryable=True,
        )
    if choice.finish_reason == "content_filter":
        raise DiagnosticExtractionError("输出被内容过滤拦截。", retryable=False)

    raw = choice.message.content
    if raw is None or not raw.strip():
        raise DiagnosticExtractionError(
            "模型返回空内容（json_object 模式偶发空响应，可重试）。",
            retryable=True,
        )

    payload = _strip_markdown_fence(raw)
    try:
        return HardwareDiagnosticReport.model_validate_json(payload)
    except ValidationError as exc:
        raise DiagnosticExtractionError(
            f"返回 JSON 未通过 HardwareDiagnosticReport 严格校验：\n{exc}",
            retryable=True,
        ) from exc


# ---------------------------------------------------------------------------
# 5. 对外入口：完整错误捕获
# ---------------------------------------------------------------------------


def extract_hardware_diagnostic_report(
    source_text: str,
    *,
    client: OpenAI | None = None,
    model: str | None = None,
    max_tokens: int = 512,
) -> HardwareDiagnosticReport:
    """从非结构化文本抽取 HardwareDiagnosticReport。

    先尝试 Structured Outputs（json_schema / strict）。
    若服务端明确不支持该 response_format，再降级到 json_object + 本地校验。
    """
    if not source_text or not source_text.strip():
        raise DiagnosticExtractionError("source_text 为空，无法抽取。", retryable=False)

    owned_client = client is None
    client = client or build_client()
    model = model or _model_name()

    try:
        try:
            return _extract_via_structured_outputs(
                client, source_text, model=model, max_tokens=max_tokens
            )
        except BadRequestError as exc:
            if not _unsupported_json_schema(exc):
                raise DiagnosticExtractionError(
                    f"请求被拒绝（HTTP {exc.status_code}）：{exc.message}",
                    retryable=False,
                ) from exc
            return _extract_via_json_object(
                client, source_text, model=model, max_tokens=max_tokens
            )
    except DiagnosticExtractionError:
        raise
    except LengthFinishReasonError as exc:
        raise DiagnosticExtractionError(
            "输出因达到 max_tokens 被截断，JSON 不完整。增大 max_tokens 后重试。",
            retryable=True,
        ) from exc
    except ContentFilterFinishReasonError as exc:
        raise DiagnosticExtractionError("输出被内容过滤拦截。", retryable=False) from exc
    except AuthenticationError as exc:
        raise DiagnosticExtractionError(
            "鉴权失败：检查 OPENAI_API_KEY。本地服务通常可填任意非空字符串。",
            retryable=False,
        ) from exc
    except PermissionDeniedError as exc:
        raise DiagnosticExtractionError(
            f"无权调用该模型或该接口：{exc.message}",
            retryable=False,
        ) from exc
    except NotFoundError as exc:
        raise DiagnosticExtractionError(
            f"模型或路径不存在：检查 OPENAI_MODEL 与 OPENAI_BASE_URL。详情：{exc.message}",
            retryable=False,
        ) from exc
    except RateLimitError as exc:
        raise DiagnosticExtractionError(
            f"触发限流：{exc.message}",
            retryable=True,
        ) from exc
    except APITimeoutError as exc:
        raise DiagnosticExtractionError("请求超时。", retryable=True) from exc
    except APIConnectionError as exc:
        raise DiagnosticExtractionError(
            "无法连接 OpenAI 兼容端点。检查 OPENAI_BASE_URL 与本地服务是否已启动。",
            retryable=True,
        ) from exc
    except InternalServerError as exc:
        raise DiagnosticExtractionError(
            f"服务端内部错误（HTTP {exc.status_code}）。",
            retryable=True,
        ) from exc
    except APIStatusError as ext:
        raise DiagnosticExtractionError(
            f"API 返回未单独处理的状态码 {ext.status_code}：{ext.message}",
            retryable=500 <= ext.status_code < 600,
        ) from ext
    except ValidationError as exc:
        raise DiagnosticExtractionError(
            f"SDK 解析结果未通过严格校验：\n{exc}",
            retryable=True,
        ) from exc
    finally:
        if owned_client:
            client.close()


# ---------------------------------------------------------------------------
# 6. 本地校验演示 + 可选真实调用
# ---------------------------------------------------------------------------


def _demo_local_validation() -> None:
    valid = HardwareDiagnosticReport(
        device_id="SRV-A12",
        status=DeviceStatus.OVERLOAD,
        error_code=5012,
    )
    print("合法实例:")
    print(valid.model_dump_json(indent=2, ensure_ascii=False))

    cases: list[dict[str, object]] = [
        {"device_id": "SRV-A12", "status": "未知", "error_code": 0},
        {"device_id": "SRV-A12", "status": "过载", "error_code": "5012"},
        {"device_id": "SRV-A12", "status": "过载", "error_code": 5012, "extra": True},
        {"device_id": "", "status": "正常", "error_code": 0},
    ]
    print("\n非法数据（均应被 ValidationError 拒绝）:")
    for payload in cases:
        try:
            HardwareDiagnosticReport.model_validate(payload)
            print(f"  未拒绝（异常）: {payload}")
        except ValidationError as exc:
            first = exc.errors()[0]
            print(f"  {payload} -> {first['type']}: {first['msg']}")


def main() -> None:
    _demo_local_validation()

    source = os.environ.get(
        "DIAGNOSTIC_SOURCE_TEXT",
        "巡检记录：设备 ID=SRV-A12。当前状态：过载。错误码：5012。",
    )
    skip_llm = os.environ.get("SKIP_LLM", "").lower() in {"1", "true", "yes"}
    if skip_llm:
        return

    print("\n调用 OpenAI 兼容接口抽取:")
    print(f"  BASE_URL = {os.environ.get('OPENAI_BASE_URL', 'http://127.0.0.1:11434/v1')}")
    print(f"  MODEL    = {_model_name()}")
    try:
        report = extract_hardware_diagnostic_report(source)
    except DiagnosticExtractionError as exc:
        print(f"抽取失败（retryable={exc.retryable}）：{exc}")
        raise SystemExit(1) from exc

    print(report.model_dump_json(indent=2, ensure_ascii=False))
    print(f"status 的运行时类型: {type(report.status).__name__} = {report.status!s}")


if __name__ == "__main__":
    main()
