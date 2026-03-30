"""Centralized model catalog and runtime hints for provider integrations."""

from __future__ import annotations

from typing import Literal


DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_GEMINI_MODEL = "gemini-3.1-pro-preview"
DEFAULT_GEMINI_SLIDE_DECK_MODEL = "gemini-3-pro-image-preview"
PROVIDER_MODEL_CATALOG_REVISION = 1

DEFAULT_OPENAI_MODELS = (
    "gpt-5.4",
    "gpt-5.2",
    "gpt-5.1",
    "gpt-5-mini",
)
DEFAULT_ANTHROPIC_MODELS = (
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
)
DEFAULT_GEMINI_MODELS = (
    "gemini-3.1-pro-preview",
    "gemini-3-pro-image-preview",
    "gemini-3.1-flash-image-preview",
    "gemini-3-flash-preview",
)

OPENAI_REASONING_EFFORT_OPTIONS = (
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
)
DEFAULT_OPENAI_REASONING_EFFORT = "medium"

ANTHROPIC_THINKING_EFFORT_OPTIONS = (
    "low",
    "medium",
    "high",
    "max",
)
DEFAULT_ANTHROPIC_THINKING_EFFORT = "high"

MODEL_ALIASES = {
    "claude-opus-4-5": "claude-opus-4-6",
    "claude-sonnet-4-5": "claude-sonnet-4-6",
    "claude-3-5-haiku-latest": "claude-haiku-4-5",
    "claude-3-7-sonnet-latest": "claude-3-7-sonnet-20250219",
}

_COMMON_CAPABILITIES = {
    "pdf": True,
    "image": True,
    "streaming": True,
    "reasoning": True,
    "generated_image_output": False,
}

MODEL_CAPABILITIES: dict[str, dict] = {
    # OpenAI
    "gpt-5.4": {
        "provider": "openai",
        **_COMMON_CAPABILITIES,
        "openai_reasoning_efforts": ("none", "low", "medium", "high", "xhigh"),
        "openai_default_reasoning_effort": "medium",
        "openai_question_verbosity": "low",
        "openai_reading_verbosity": "medium",
    },
    "gpt-5.4-pro": {
        "provider": "openai",
        **_COMMON_CAPABILITIES,
        "openai_reasoning_efforts": ("none", "low", "medium", "high", "xhigh"),
        "openai_default_reasoning_effort": "high",
        "openai_question_verbosity": "low",
        "openai_reading_verbosity": "medium",
        "requires_ui_confirmation": True,
    },
    "gpt-5.2": {
        "provider": "openai",
        **_COMMON_CAPABILITIES,
        "openai_reasoning_efforts": ("none", "low", "medium", "high", "xhigh"),
        "openai_default_reasoning_effort": "medium",
        "openai_question_verbosity": "low",
        "openai_reading_verbosity": "medium",
    },
    "gpt-5.1": {
        "provider": "openai",
        **_COMMON_CAPABILITIES,
        "openai_reasoning_efforts": ("none", "low", "medium", "high"),
        "openai_default_reasoning_effort": "medium",
        "openai_question_verbosity": "low",
        "openai_reading_verbosity": "medium",
    },
    "gpt-5": {
        "provider": "openai",
        **_COMMON_CAPABILITIES,
        "openai_reasoning_efforts": ("minimal", "low", "medium", "high"),
        "openai_default_reasoning_effort": "medium",
        "openai_question_verbosity": "low",
        "openai_reading_verbosity": "medium",
    },
    "gpt-5-mini": {
        "provider": "openai",
        **_COMMON_CAPABILITIES,
        "openai_reasoning_efforts": ("minimal", "low", "medium", "high"),
        "openai_default_reasoning_effort": "medium",
        "openai_question_verbosity": "low",
        "openai_reading_verbosity": "medium",
    },
    "o4-mini": {
        "provider": "openai",
        **_COMMON_CAPABILITIES,
        "openai_reasoning_efforts": ("low", "medium", "high"),
        "openai_default_reasoning_effort": "high",
    },
    "o3-mini": {
        "provider": "openai",
        **_COMMON_CAPABILITIES,
        "openai_reasoning_efforts": ("low", "medium", "high"),
        "openai_default_reasoning_effort": "high",
    },
    "o1": {
        "provider": "openai",
        **_COMMON_CAPABILITIES,
        "openai_reasoning_efforts": ("low", "medium", "high"),
        "openai_default_reasoning_effort": "high",
    },
    "o1-mini": {
        "provider": "openai",
        **_COMMON_CAPABILITIES,
        "openai_reasoning_efforts": ("low", "medium", "high"),
        "openai_default_reasoning_effort": "high",
    },
    # Anthropic
    "claude-opus-4-6": {
        "provider": "anthropic",
        **_COMMON_CAPABILITIES,
        "anthropic_thinking_type": "adaptive",
        "anthropic_thinking_efforts": ANTHROPIC_THINKING_EFFORT_OPTIONS,
        "anthropic_default_thinking_effort": DEFAULT_ANTHROPIC_THINKING_EFFORT,
    },
    "claude-sonnet-4-6": {
        "provider": "anthropic",
        **_COMMON_CAPABILITIES,
        "anthropic_thinking_type": "adaptive",
        "anthropic_thinking_efforts": ANTHROPIC_THINKING_EFFORT_OPTIONS,
        "anthropic_default_thinking_effort": DEFAULT_ANTHROPIC_THINKING_EFFORT,
    },
    "claude-haiku-4-5": {
        "provider": "anthropic",
        **_COMMON_CAPABILITIES,
        "anthropic_thinking_type": "enabled",
    },
    "claude-opus-4-1-20250805": {
        "provider": "anthropic",
        **_COMMON_CAPABILITIES,
        "anthropic_thinking_type": "adaptive",
        "anthropic_thinking_efforts": ANTHROPIC_THINKING_EFFORT_OPTIONS,
        "anthropic_default_thinking_effort": DEFAULT_ANTHROPIC_THINKING_EFFORT,
    },
    "claude-opus-4-20250514": {
        "provider": "anthropic",
        **_COMMON_CAPABILITIES,
        "anthropic_thinking_type": "adaptive",
        "anthropic_thinking_efforts": ANTHROPIC_THINKING_EFFORT_OPTIONS,
        "anthropic_default_thinking_effort": DEFAULT_ANTHROPIC_THINKING_EFFORT,
    },
    "claude-sonnet-4-20250514": {
        "provider": "anthropic",
        **_COMMON_CAPABILITIES,
        "anthropic_thinking_type": "adaptive",
        "anthropic_thinking_efforts": ANTHROPIC_THINKING_EFFORT_OPTIONS,
        "anthropic_default_thinking_effort": DEFAULT_ANTHROPIC_THINKING_EFFORT,
    },
    "claude-3-7-sonnet-20250219": {
        "provider": "anthropic",
        **_COMMON_CAPABILITIES,
        "anthropic_thinking_type": "enabled",
    },
    "claude-3-5-haiku-latest": {
        "provider": "anthropic",
        **_COMMON_CAPABILITIES,
        "anthropic_thinking_type": "enabled",
    },
    # Gemini
    "gemini-3.1-pro-preview": {"provider": "gemini", **_COMMON_CAPABILITIES},
    "gemini-3-pro-image-preview": {
        "provider": "gemini",
        **_COMMON_CAPABILITIES,
        "generated_image_output": True,
    },
    "gemini-3.1-flash-image-preview": {
        "provider": "gemini",
        **_COMMON_CAPABILITIES,
        "generated_image_output": True,
    },
    "gemini-3-flash-preview": {"provider": "gemini", **_COMMON_CAPABILITIES},
}

MODEL_PROVIDERS = {model: caps["provider"] for model, caps in MODEL_CAPABILITIES.items()}

PROVIDER_DEFAULT_CAPABILITIES = {
    "openai": {
        "pdf": True,
        "image": True,
        "streaming": True,
        "reasoning": True,
        "generated_image_output": False,
    },
    "anthropic": {
        "pdf": True,
        "image": True,
        "streaming": True,
        "reasoning": True,
        "generated_image_output": False,
    },
    "gemini": {
        "pdf": True,
        "image": True,
        "streaming": True,
        "reasoning": True,
        "generated_image_output": False,
    },
}

_GENERIC_TO_ANTHROPIC_EFFORT = {
    "none": "low",
    "minimal": "low",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "max",
    "max": "max",
}


def canonicalize_model(model: str) -> str:
    return MODEL_ALIASES.get(model, model)


def get_provider(model: str) -> str:
    model = canonicalize_model(model)
    if model in MODEL_PROVIDERS:
        return MODEL_PROVIDERS[model]
    if model.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    if model.startswith("claude"):
        return "anthropic"
    if model.startswith("gemini"):
        return "gemini"
    return "openai"


def get_model_capabilities(model: str) -> dict:
    model = canonicalize_model(model)
    if model in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model]
    provider = get_provider(model)
    caps = PROVIDER_DEFAULT_CAPABILITIES.get(provider, {})
    return {"provider": provider, **caps}


def requires_explicit_confirmation(model: str) -> bool:
    caps = get_model_capabilities(model)
    return bool(caps.get("requires_ui_confirmation"))


def validate_model_support(model: str, feature: str) -> tuple[bool, str]:
    caps = get_model_capabilities(model)
    if not caps.get(feature, False):
        if feature == "generated_image_output":
            return (
                False,
                f"{model} does not support illustrated slide decks. "
                "Please select a Gemini image-preview model.",
            )
        return False, f"{model} does not support {feature}. Please select a different model."
    return True, ""


def get_openai_reasoning_efforts(model: str) -> tuple[str, ...]:
    model = canonicalize_model(model)
    caps = get_model_capabilities(model)
    allowed = caps.get("openai_reasoning_efforts")
    if isinstance(allowed, tuple):
        return allowed
    if model.startswith(("gpt-5.4", "gpt-5.2")):
        return ("none", "low", "medium", "high", "xhigh")
    if model.startswith("gpt-5.1"):
        return ("none", "low", "medium", "high")
    if model.startswith("gpt-5"):
        return ("minimal", "low", "medium", "high")
    return ("low", "medium", "high")


def get_default_openai_reasoning_effort(model: str) -> str:
    caps = get_model_capabilities(canonicalize_model(model))
    effort = caps.get("openai_default_reasoning_effort")
    if isinstance(effort, str):
        return effort
    return DEFAULT_OPENAI_REASONING_EFFORT


def normalize_openai_reasoning_effort(model: str, effort: str) -> str:
    allowed = get_openai_reasoning_efforts(model)
    if effort in allowed:
        return effort

    effort_order = OPENAI_REASONING_EFFORT_OPTIONS
    if effort in effort_order:
        requested_index = effort_order.index(effort)
        ranked_allowed = sorted(
            allowed,
            key=lambda candidate: (
                abs(effort_order.index(candidate) - requested_index),
                effort_order.index(candidate),
            ),
        )
        if ranked_allowed:
            return ranked_allowed[0]

    fallback = get_default_openai_reasoning_effort(model)
    if fallback in allowed:
        return fallback
    return allowed[-1]


def get_openai_text_verbosity(
    model: str,
    task: Literal["questions", "reading"],
) -> str | None:
    model = canonicalize_model(model)
    if not model.startswith("gpt-5"):
        return None
    caps = get_model_capabilities(model)
    if task == "questions":
        return caps.get("openai_question_verbosity", "low")
    return caps.get("openai_reading_verbosity", "medium")


def uses_anthropic_adaptive_thinking(model: str) -> bool:
    caps = get_model_capabilities(canonicalize_model(model))
    return caps.get("anthropic_thinking_type") == "adaptive"


def get_anthropic_thinking_efforts(model: str) -> tuple[str, ...]:
    caps = get_model_capabilities(canonicalize_model(model))
    efforts = caps.get("anthropic_thinking_efforts")
    if isinstance(efforts, tuple):
        return efforts
    return ANTHROPIC_THINKING_EFFORT_OPTIONS


def normalize_anthropic_thinking_effort(model: str, effort: str) -> str:
    allowed = get_anthropic_thinking_efforts(model)
    mapped_effort = _GENERIC_TO_ANTHROPIC_EFFORT.get(effort, effort)
    if mapped_effort in allowed:
        return mapped_effort

    caps = get_model_capabilities(canonicalize_model(model))
    fallback = caps.get("anthropic_default_thinking_effort")
    if isinstance(fallback, str) and fallback in allowed:
        return fallback
    return DEFAULT_ANTHROPIC_THINKING_EFFORT
