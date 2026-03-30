"""
Unified LLM Handler Module

Provides a unified interface for OpenAI, Anthropic (Claude), and Google Gemini APIs.
Supports text-based questions, image-based questions, and reading material generation.
"""

import os
import logging
import base64
import asyncio
import hashlib
import re
from dataclasses import dataclass
from typing import Optional, AsyncGenerator, Callable, Awaitable, Any

import httpx
import openai as openai_sdk
import anthropic as anthropic_sdk

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.prompts.qti_prompts import PromptPrefixGenerator
from app.utils.model_catalog import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_OPENAI_MODEL,
    MODEL_CAPABILITIES,
    canonicalize_model,
    get_openai_text_verbosity,
    get_provider,
    normalize_anthropic_thinking_effort,
    normalize_openai_reasoning_effort,
    requires_explicit_confirmation,
    uses_anthropic_adaptive_thinking,
    validate_model_support,
)

READING_MATERIAL_SYSTEM_PROMPT = """You are an expert educational content creator.
Generate engaging, age-appropriate reading material based on the specifications provided.

Requirements:
- Match the specified grade level in vocabulary and complexity
- Cover the topic thoroughly while staying focused
- Address all learning objectives
- Use clear, well-structured paragraphs
- Include relevant examples and explanations
- If an image is provided, incorporate it naturally into the content
- If a PDF is provided, use it as reference material for the content

Output Format:
Return the reading material as plain text, ready to be used as educational content.
"""

READING_MATERIAL_ILLUSTRATED_PROMPT = """You are an expert educational content creator specializing in richly illustrated learning materials.

Create comprehensive, visually engaging educational content with the following structure:

## Content Requirements:
1. **Chapter-based Organization**: Divide content into logical chapters/sections with clear headings
2. **Rich Paragraphs**: Write detailed, information-rich paragraphs that explain concepts thoroughly
3. **Interesting Facts**: Include "Did You Know?" boxes with fascinating facts related to the topic
4. **Real-world Analogies**: Use relatable analogies to explain complex concepts
5. **Phenomena & Examples**: Describe real-world phenomena, case studies, or examples
6. **Visual Illustrations**: Generate relevant educational images to accompany each major section
7. **Key Vocabulary**: Highlight and define important terms
8. **Summary Points**: End each chapter with key takeaways

## Visual Content Guidelines:
- Create clear, educational illustrations that enhance understanding
- Include diagrams, charts, or visual representations where helpful
- Generate images that are appropriate for the grade level
- Each major section should have at least one relevant illustration

## Tone & Style:
- Engaging and accessible for the target grade level
- Balance between educational rigor and readability
- Use active voice and concrete examples
- Build concepts progressively from simple to complex

Generate a complete, illustrated educational reading material that a student would find both informative and engaging.
"""

SLIDE_DECK_PROMPT = """You are an expert educational content creator specializing in visual presentation slides.

Create a comprehensive, illustrated slide deck in a single ordered response.

## Slide Format:
- Use `## Slide N: Title` for each new slide title
- Keep text concise: 3-5 bullets per slide, not paragraphs
- Each major concept should have its own slide
- Return the full deck in slide order, from the first slide to the last slide
- After each slide's text block, provide one corresponding illustration in the same response order
- Do not combine all visuals into one infographic unless explicitly asked

## Required Slides:
1. **Title Slide**: Topic name and grade level
2. **Learning Objectives**: What students will learn
3. **Introduction**: Hook and overview
4. **Content Slides**: One concept per slide with:
   - Clear heading
   - 3-5 bullet points
   - Key terms highlighted
   - One corresponding educational illustration
5. **Summary Slide**: Key takeaways
6. **Discussion Questions**: 2-3 questions for class discussion

## Visual Content:
- Make each illustration directly represent the slide content immediately before it
- Prefer diagrams, labeled scientific drawings, charts, classroom scenes, or instructional visuals over decorative art
- Use a clean 16:9 slide-friendly composition
- Avoid branding, watermarks, and dense text in the image itself

## Style Guidelines:
- Concise, scannable text
- Active voice
- Grade-appropriate vocabulary
- Engaging, visual-first approach

Generate a complete slide deck that a teacher can use directly for classroom presentation.
"""


def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """Safely retrieve configuration values from environment."""
    return os.getenv(key, default)

def get_api_key_for_provider(provider: str, api_key: str = "") -> str:
    """Get API key for provider from argument or environment."""
    if api_key:
        return api_key

    if provider == "openai":
        return get_config_value("OPENAI_API_KEY", "")
    elif provider == "anthropic":
        return get_config_value("CLAUDE_API_KEY", "")
    elif provider == "gemini":
        return get_config_value("GEMINI_API_KEY", "")
    return ""


LLM_CONNECT_TIMEOUT_SECONDS = 30.0
LLM_POOL_TIMEOUT_SECONDS = 30.0
LLM_WRITE_TIMEOUT_SECONDS = 120.0
LLM_READ_TIMEOUT_SECONDS = 600.0
LLM_UPLOAD_TIMEOUT_SECONDS = 180.0
LLM_RETRY_DELAYS_SECONDS = (2.0, 4.0, 8.0)
_OPENAI_FILE_ID_CACHE: dict[str, str] = {}


def _provider_http_timeout(
    *,
    read_timeout: float = LLM_READ_TIMEOUT_SECONDS,
    write_timeout: float = LLM_WRITE_TIMEOUT_SECONDS,
) -> httpx.Timeout:
    return httpx.Timeout(
        connect=LLM_CONNECT_TIMEOUT_SECONDS,
        read=read_timeout,
        write=write_timeout,
        pool=LLM_POOL_TIMEOUT_SECONDS,
    )


def _openai_file_cache_key(api_key: str, file_bytes: bytes) -> str:
    api_key_digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    file_digest = hashlib.sha256(file_bytes).hexdigest()
    return f"{api_key_digest}:{file_digest}"


async def _openai_get_or_upload_file_id(
    api_key: str,
    file_bytes: bytes,
    filename: str,
    mime_type: str = "application/pdf",
) -> str:
    cache_key = _openai_file_cache_key(api_key, file_bytes)
    cached_file_id = _OPENAI_FILE_ID_CACHE.get(cache_key)
    if cached_file_id:
        return cached_file_id

    client = AsyncOpenAI(
        api_key=api_key,
        timeout=_provider_http_timeout(
            read_timeout=LLM_UPLOAD_TIMEOUT_SECONDS,
            write_timeout=LLM_UPLOAD_TIMEOUT_SECONDS,
        ),
    )
    uploaded_file = await client.files.create(
        file=(filename, file_bytes, mime_type),
        purpose="user_data",
    )

    existing_file_id = _OPENAI_FILE_ID_CACHE.setdefault(cache_key, uploaded_file.id)
    if existing_file_id != uploaded_file.id:
        try:
            await client.files.delete(uploaded_file.id)
        except Exception:
            logging.warning("Failed to delete duplicate OpenAI file upload %s", uploaded_file.id)
        return existing_file_id

    return uploaded_file.id


async def release_openai_cached_file(api_key: str, file_bytes: bytes) -> bool:
    if not api_key or not file_bytes:
        return False

    cache_key = _openai_file_cache_key(api_key, file_bytes)
    file_id = _OPENAI_FILE_ID_CACHE.pop(cache_key, None)
    if not file_id:
        return False

    client = AsyncOpenAI(
        api_key=api_key,
        timeout=_provider_http_timeout(
            read_timeout=LLM_UPLOAD_TIMEOUT_SECONDS,
            write_timeout=LLM_UPLOAD_TIMEOUT_SECONDS,
        ),
    )
    try:
        await client.files.delete(file_id)
    except openai_sdk.APIStatusError as error:
        if getattr(error, "status_code", None) != 404:
            logging.warning("Failed to delete cached OpenAI file %s: %s", file_id, error)
            _OPENAI_FILE_ID_CACHE[cache_key] = file_id
            return False
    except Exception as error:
        logging.warning("Failed to delete cached OpenAI file %s: %s", file_id, error)
        _OPENAI_FILE_ID_CACHE[cache_key] = file_id
        return False

    return True


def _is_gemini_3_model(model: str) -> bool:
    return model.startswith("gemini-3")


def _gemini_thinking_config(thinking_enabled: bool, thinking_budget: int) -> types.ThinkingConfig | None:
    if not thinking_enabled:
        return None
    return types.ThinkingConfig(thinking_budget=thinking_budget)


def _anthropic_thinking_config(
    model: str,
    thinking_enabled: bool,
    thinking_budget: int,
    reasoning_effort: str = "high",
) -> dict[str, str | int] | None:
    if not thinking_enabled:
        return None
    if uses_anthropic_adaptive_thinking(model):
        return {"type": "adaptive"}
    return {
        "type": "enabled",
        "budget_tokens": thinking_budget,
    }


def _anthropic_output_config(
    model: str,
    reasoning_effort: str = "high",
) -> dict[str, str] | None:
    if uses_anthropic_adaptive_thinking(model):
        return {
            "effort": normalize_anthropic_thinking_effort(model, reasoning_effort),
        }
    return None


def _is_timeout_error(error: Exception) -> bool:
    if isinstance(
        error,
        (
            httpx.TimeoutException,
            openai_sdk.APITimeoutError,
            anthropic_sdk.APITimeoutError,
        ),
    ):
        return True
    if isinstance(error, genai_errors.APIError):
        status = getattr(error, "status", "")
        code = getattr(error, "code", None)
        return status == "DEADLINE_EXCEEDED" or code == 504
    return False


def _is_retryable_error(provider: str, error: Exception) -> bool:
    if _is_timeout_error(error):
        return True

    if provider == "openai":
        if isinstance(error, openai_sdk.RateLimitError):
            return True
        if isinstance(error, openai_sdk.APIStatusError):
            return getattr(error, "status_code", 0) >= 500
        if isinstance(error, openai_sdk.APIConnectionError):
            return True
        return False

    if provider == "anthropic":
        if isinstance(error, anthropic_sdk.RateLimitError):
            return True
        if isinstance(error, anthropic_sdk.InternalServerError):
            return True
        if isinstance(error, anthropic_sdk.APIStatusError):
            return getattr(error, "status_code", 0) >= 500
        if isinstance(error, anthropic_sdk.APIConnectionError):
            return True
        return False

    if provider == "gemini":
        if isinstance(error, (genai_errors.ClientError, genai_errors.ServerError, genai_errors.APIError)):
            code = getattr(error, "code", None)
            if code in (429, 500, 502, 503, 504):
                return True
        return _is_timeout_error(error)

    return False


async def _retry_async_call(provider: str, operation_name: str, fn: Callable[[], Awaitable[Any]]) -> Any:
    max_attempts = len(LLM_RETRY_DELAYS_SECONDS) + 1
    for attempt in range(max_attempts):
        try:
            return await fn()
        except Exception as error:
            if attempt >= max_attempts - 1 or not _is_retryable_error(provider, error):
                raise
            delay_seconds = LLM_RETRY_DELAYS_SECONDS[attempt]
            logging.warning(
                "%s %s failed (attempt %s/%s): %s. Retrying in %ss.",
                provider,
                operation_name,
                attempt + 1,
                max_attempts,
                error,
                delay_seconds,
            )
            await asyncio.sleep(delay_seconds)


async def _retry_async_stream(
    provider: str,
    operation_name: str,
    stream_factory: Callable[[], AsyncGenerator[dict, None]],
) -> AsyncGenerator[dict, None]:
    max_attempts = len(LLM_RETRY_DELAYS_SECONDS) + 1
    for attempt in range(max_attempts):
        yielded_any = False
        try:
            async for item in stream_factory():
                yielded_any = True
                yield item
            return
        except Exception as error:
            # Do not replay a partially streamed response.
            if yielded_any:
                raise
            if attempt >= max_attempts - 1 or not _is_retryable_error(provider, error):
                raise
            delay_seconds = LLM_RETRY_DELAYS_SECONDS[attempt]
            logging.warning(
                "%s %s stream failed (attempt %s/%s): %s. Retrying in %ss.",
                provider,
                operation_name,
                attempt + 1,
                max_attempts,
                error,
                delay_seconds,
            )
            await asyncio.sleep(delay_seconds)


# =============================================================================
# OpenAI Implementation
# =============================================================================

async def _openai_generate_streaming(
    api_key: str,
    model: str,
    system_prompt: str,
    user_content: list,
    reasoning_effort: str = "high",
    total_questions: int = 1,
    text_verbosity: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Generate content using OpenAI Responses API with streaming."""
    client = AsyncOpenAI(
        api_key=api_key,
        timeout=_provider_http_timeout(),
    )

    input_messages = [{"role": "user", "content": user_content}]

    request_params = {
        "model": model,
        "reasoning": {"effort": normalize_openai_reasoning_effort(model, reasoning_effort)},
        "instructions": system_prompt,
        "input": input_messages,
        "max_output_tokens": 16384,
        "stream": True,
        "store": True,
    }
    if text_verbosity:
        request_params["text"] = {"verbosity": text_verbosity}

    stream = await client.responses.create(**request_params)

    full_response = []
    async for event in stream:
        if event.type == "response.output_text.delta":
            delta = event.delta
            full_response.append(delta)
            displayed_response = "".join(full_response)

            yield {
                "yaml": displayed_response,
                "count": 0,
                "progress": 0.5,
            }

        elif event.type == "response.completed":
            yaml_response = "".join(full_response).strip()
            yield {
                "yaml": yaml_response,
                "count": total_questions,
                "progress": 1.0,
                "completed": True
            }


async def _openai_generate_responses(
    api_key: str,
    model: str,
    system_prompt: str,
    user_content: list,
    reasoning_effort: str = "high",
    text_verbosity: str | None = None,
) -> str:
    """Generate content using OpenAI Responses API."""
    client = AsyncOpenAI(
        api_key=api_key,
        timeout=_provider_http_timeout(),
    )

    input_messages = [{"role": "user", "content": user_content}]

    request_params = {
        "model": model,
        "reasoning": {"effort": normalize_openai_reasoning_effort(model, reasoning_effort)},
        "instructions": system_prompt,
        "input": input_messages,
        "max_output_tokens": 16384,
        "store": True,
    }
    if text_verbosity:
        request_params["text"] = {"verbosity": text_verbosity}

    response = await client.responses.create(**request_params)

    # Extract text from response
    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if content.type == "output_text":
                    return content.text.strip()

    return ""


# =============================================================================
# Anthropic (Claude) Implementation
# =============================================================================

async def _anthropic_generate(
    api_key: str,
    model: str,
    system_prompt: str,
    user_content: list,
    thinking_enabled: bool = True,
    thinking_budget: int = 10000,
    reasoning_effort: str = "high",
) -> str:
    """Generate content using Anthropic Messages API with extended thinking."""
    client = AsyncAnthropic(
        api_key=api_key,
        timeout=_provider_http_timeout(),
    )

    system_message = [{
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"}
    }]

    messages = [{
        "role": "user",
        "content": user_content
    }]

    # Build request parameters
    request_params = {
        "model": model,
        "max_tokens": 16384,
        "system": system_message,
        "messages": messages,
    }

    thinking_config = _anthropic_thinking_config(
        model,
        thinking_enabled,
        thinking_budget,
        reasoning_effort,
    )
    if thinking_config:
        request_params["thinking"] = thinking_config
        output_config = _anthropic_output_config(model, reasoning_effort)
        if output_config:
            request_params["output_config"] = output_config
    else:
        request_params["temperature"] = 0.7

    response = await client.messages.create(**request_params)

    # Extract text from response (skip thinking blocks)
    text_content = []
    for block in response.content:
        if hasattr(block, 'text'):
            text_content.append(block.text)

    return "\n".join(text_content).strip()


async def _anthropic_generate_streaming(
    api_key: str,
    model: str,
    system_prompt: str,
    user_content: list,
    thinking_enabled: bool = True,
    thinking_budget: int = 10000,
    total_questions: int = 1,
    reasoning_effort: str = "high",
) -> AsyncGenerator[dict, None]:
    """Generate content using Anthropic streaming API."""
    client = AsyncAnthropic(
        api_key=api_key,
        timeout=_provider_http_timeout(),
    )

    system_message = [{
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"},
    }]
    messages = [{
        "role": "user",
        "content": user_content,
    }]

    request_params = {
        "model": model,
        "max_tokens": 16384,
        "system": system_message,
        "messages": messages,
    }

    thinking_config = _anthropic_thinking_config(
        model,
        thinking_enabled,
        thinking_budget,
        reasoning_effort,
    )
    if thinking_config:
        request_params["thinking"] = thinking_config
        output_config = _anthropic_output_config(model, reasoning_effort)
        if output_config:
            request_params["output_config"] = output_config
    else:
        request_params["temperature"] = 0.7

    full_response = []
    async with client.messages.stream(**request_params) as stream:
        async for text_chunk in stream.text_stream:
            if not text_chunk:
                continue
            full_response.append(text_chunk)
            displayed_response = "".join(full_response)
            yield {
                "yaml": displayed_response,
                "count": 0,
                "progress": 0.5,
            }

    yaml_response = "".join(full_response).strip()
    yield {
        "yaml": yaml_response,
        "count": total_questions,
        "progress": 1.0,
        "completed": True,
    }


# =============================================================================
# Gemini Implementation
# =============================================================================

async def _gemini_generate(
    api_key: str,
    model: str,
    system_prompt: str,
    user_content: list,
    thinking_enabled: bool = True,
    thinking_budget: int = 10000
) -> str:
    """Generate content using Google Gemini API with thinking mode."""
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=int(LLM_READ_TIMEOUT_SECONDS * 1000)),
    )

    # Build contents list
    contents = []

    # Add user content parts
    for item in user_content:
        if isinstance(item, str):
            contents.append(item)
        elif isinstance(item, dict):
            if item.get("type") == "text":
                contents.append(item.get("text", ""))
            elif item.get("type") == "image_bytes":
                # Image data as bytes
                contents.append(types.Part.from_bytes(
                    data=item.get("data"),
                    mime_type=item.get("mime_type", "image/jpeg")
                ))
            elif item.get("type") == "pdf_bytes":
                # PDF data as bytes
                contents.append(types.Part.from_bytes(
                    data=item.get("data"),
                    mime_type="application/pdf"
                ))

    # Build config with model-specific thinking configuration.
    config_params = {}
    thinking_config = _gemini_thinking_config(thinking_enabled, thinking_budget)
    if thinking_config:
        config_params["thinking_config"] = thinking_config

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        **config_params
    )

    response = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

    return (response.text or "").strip()


async def _gemini_generate_illustrated(
    api_key: str,
    model: str,
    system_prompt: str,
    user_content: list,
    thinking_enabled: bool = True,
    thinking_budget: int = 10000,
    image_aspect_ratio: str | None = None,
) -> dict:
    """
    Generate illustrated content using Gemini 3 Pro Image API.
    Returns dict with raw text and generated images.
    """
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=int(LLM_READ_TIMEOUT_SECONDS * 1000)),
    )

    # Build contents list
    contents = []

    # Add user content parts
    for item in user_content:
        if isinstance(item, str):
            contents.append(item)
        elif isinstance(item, dict):
            if item.get("type") == "text":
                contents.append(item.get("text", ""))
            elif item.get("type") == "image_bytes":
                contents.append(types.Part.from_bytes(
                    data=item.get("data"),
                    mime_type=item.get("mime_type", "image/jpeg")
                ))
            elif item.get("type") == "pdf_bytes":
                contents.append(types.Part.from_bytes(
                    data=item.get("data"),
                    mime_type="application/pdf"
                ))

    config_params: dict[str, Any] = {
        "system_instruction": system_prompt,
        "response_modalities": ["TEXT", "IMAGE"],
    }
    thinking_config = _gemini_thinking_config(thinking_enabled, thinking_budget)
    if thinking_config:
        config_params["thinking_config"] = thinking_config
    if image_aspect_ratio:
        config_params["image_config"] = {"aspect_ratio": image_aspect_ratio}

    result_text = []
    images = []
    image_counter = 0

    response = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=config_params,
    )

    parts = []
    if getattr(response, "parts", None):
        parts = list(response.parts)
    elif getattr(response, "candidates", None):
        for candidate in response.candidates or []:
            candidate_parts = getattr(getattr(candidate, "content", None), "parts", None)
            if candidate_parts:
                parts.extend(candidate_parts)

    for part in parts:
        if hasattr(part, "text") and part.text:
            result_text.append(part.text)
            continue

        inline_data = getattr(part, "inline_data", None)
        if not inline_data:
            continue

        image_counter += 1
        image_data = inline_data.data
        mime_type = inline_data.mime_type
        if isinstance(image_data, bytes):
            b64_image = base64.b64encode(image_data).decode("utf-8")
        else:
            b64_image = image_data

        images.append({
            "data": b64_image,
            "mime_type": mime_type,
            "index": image_counter,
        })

    return {
        "text": "".join(result_text).strip(),
        "images": images
    }


def _split_slide_sections(markdown_text: str) -> list[dict[str, str]]:
    sections = re.split(r"(?=^## )", markdown_text.strip(), flags=re.MULTILINE)
    slides: list[dict[str, str]] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        lines = section.splitlines()
        title = lines[0][3:].strip() if lines[0].startswith("## ") else "Slide"
        body = "\n".join(lines[1:]).strip()
        slides.append({"title": title, "body": body})
    return slides


def _slide_needs_generated_illustration(title: str) -> bool:
    normalized = title.strip().lower()
    if not normalized:
        return False
    skip_keywords = (
        "title",
        "discussion",
        "question",
        "summary",
        "objective",
    )
    return not any(keyword in normalized for keyword in skip_keywords)


def _rebuild_slide_deck_markdown(slides: list[dict[str, str]]) -> str:
    rendered_slides = []
    for slide in slides:
        title = slide["title"].strip() or "Slide"
        body = slide["body"].strip()
        rendered_slides.append(f"## {title}\n{body}".rstrip())
    return "\n\n".join(rendered_slides).strip()


def _markdown_image_for_generated_asset(image: dict) -> str:
    return (
        f'![Illustration {image["index"]}]'
        f'(data:{image["mime_type"]};base64,{image["data"]})'
    )


def _append_images_to_markdown(markdown_text: str, images: list[dict]) -> str:
    combined = markdown_text.strip()
    if not images:
        return combined
    image_blocks = "\n\n".join(_markdown_image_for_generated_asset(image) for image in images)
    if combined:
        return f"{combined}\n\n{image_blocks}"
    return image_blocks


def _merge_one_run_slide_deck_content(markdown_text: str, images: list[dict]) -> str:
    slides = _split_slide_sections(markdown_text)
    if not slides:
        return _append_images_to_markdown(markdown_text, images)

    image_iter = iter(images)
    last_slide_with_image: dict[str, str] | None = None

    for slide in slides:
        body = slide["body"].strip()
        if not _slide_needs_generated_illustration(slide["title"]):
            slide["body"] = body
            continue

        image = next(image_iter, None)
        if image is None:
            slide["body"] = f"{body}\n\n_Illustration unavailable_".strip()
            continue

        last_slide_with_image = slide
        rendered_image = _markdown_image_for_generated_asset(image)
        slide["body"] = f"{body}\n\n{rendered_image}".strip()

    extra_images = list(image_iter)
    if extra_images:
        target_slide = last_slide_with_image or slides[-1]
        extras_markdown = "\n\n".join(
            _markdown_image_for_generated_asset(image) for image in extra_images
        )
        target_slide["body"] = f'{target_slide["body"].strip()}\n\n{extras_markdown}'.strip()

    return _rebuild_slide_deck_markdown(slides)


# =============================================================================
# Provider Adapter Layer
# =============================================================================


@dataclass(frozen=True)
class TextQuestionsRequest:
    prompt: str
    total_questions: int
    model: str
    api_key: str
    pdf_content: str
    system_prompt: str
    thinking_enabled: bool = True
    thinking_budget: int = 10000
    reasoning_effort: str = "high"


@dataclass(frozen=True)
class ImageQuestionsRequest:
    prompt: str
    image_data: bytes
    image_format: str
    model: str
    api_key: str
    system_prompt: str
    thinking_enabled: bool = True
    thinking_budget: int = 10000
    reasoning_effort: str = "medium"


@dataclass(frozen=True)
class ReadingMaterialRequest:
    full_prompt: str
    model: str
    api_key: str
    system_prompt: str
    grade_level: str
    topic: str
    user_content: list[dict]
    content_type: str = "reading_material"
    image_data: bytes | None = None
    image_format: str | None = None
    pdf_content: str | None = None
    thinking_enabled: bool = True
    thinking_budget: int = 10000
    reasoning_effort: str = "high"


class ProviderAdapter:
    provider: str

    def __init__(self, provider: str):
        self.provider = provider

    def resolve_api_key(self, api_key: str) -> str:
        return get_api_key_for_provider(self.provider, api_key)

    @staticmethod
    def normalize_error(provider: str, error: Exception) -> Exception:
        logging.exception(f"{provider} API error: {str(error)}")
        if _is_timeout_error(error):
            return TimeoutError(
                "Request timed out while waiting for the provider. "
                "Try again, reduce reasoning effort, or switch to a faster model."
            )
        return Exception(f"{provider} API error: {str(error)}")

    async def generate_text_questions(self, request: TextQuestionsRequest) -> AsyncGenerator[dict, None]:
        raise NotImplementedError

    async def generate_image_questions(self, request: ImageQuestionsRequest) -> str:
        raise NotImplementedError

    async def generate_reading_material(self, request: ReadingMaterialRequest) -> str:
        raise NotImplementedError


class OpenAIAdapter(ProviderAdapter):
    def __init__(self):
        super().__init__("openai")

    async def generate_text_questions(self, request: TextQuestionsRequest) -> AsyncGenerator[dict, None]:
        pdf_bytes = base64.b64decode(request.pdf_content)
        file_id = await _openai_get_or_upload_file_id(
            api_key=request.api_key,
            file_bytes=pdf_bytes,
            filename="teacheraide.pdf",
        )
        user_content = [
            {"type": "input_file", "file_id": file_id},
            {"type": "input_text", "text": request.prompt},
        ]

        async for result in _openai_generate_streaming(
            api_key=request.api_key,
            model=request.model,
            system_prompt=request.system_prompt,
            user_content=user_content,
            reasoning_effort=request.reasoning_effort,
            total_questions=request.total_questions,
            text_verbosity=get_openai_text_verbosity(request.model, "questions"),
        ):
            yield result

    async def generate_image_questions(self, request: ImageQuestionsRequest) -> str:
        encoded_image = base64.b64encode(request.image_data).decode('utf-8')
        mime_type = f"image/{request.image_format}"
        user_content = [
            {"type": "input_text", "text": request.prompt},
            {"type": "input_image", "image_url": f"data:{mime_type};base64,{encoded_image}"},
        ]
        return await _openai_generate_responses(
            api_key=request.api_key,
            model=request.model,
            system_prompt=request.system_prompt,
            user_content=user_content,
            reasoning_effort=request.reasoning_effort,
            text_verbosity=get_openai_text_verbosity(request.model, "questions"),
        )

    async def generate_reading_material(self, request: ReadingMaterialRequest) -> str:
        user_content = []

        if request.pdf_content:
            pdf_bytes = base64.b64decode(request.pdf_content)
            file_id = await _openai_get_or_upload_file_id(
                api_key=request.api_key,
                file_bytes=pdf_bytes,
                filename="reference.pdf",
            )
            user_content.append({
                "type": "input_file",
                "file_id": file_id,
            })

        if request.image_data and request.image_format:
            encoded_image = base64.b64encode(request.image_data).decode('utf-8')
            mime_type = f"image/{request.image_format}"
            user_content.append({
                "type": "input_image",
                "image_url": f"data:{mime_type};base64,{encoded_image}",
            })

        user_content.append({"type": "input_text", "text": request.full_prompt})

        return await _openai_generate_responses(
            api_key=request.api_key,
            model=request.model,
            system_prompt=request.system_prompt,
            user_content=user_content,
            reasoning_effort=request.reasoning_effort,
            text_verbosity=get_openai_text_verbosity(request.model, "reading"),
        )


class AnthropicAdapter(ProviderAdapter):
    def __init__(self):
        super().__init__("anthropic")

    async def generate_text_questions(self, request: TextQuestionsRequest) -> AsyncGenerator[dict, None]:
        user_content = [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": request.pdf_content,
                },
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": request.prompt,
                "cache_control": {"type": "ephemeral"},
            },
        ]

        async for result in _anthropic_generate_streaming(
            api_key=request.api_key,
            model=request.model,
            system_prompt=request.system_prompt,
            user_content=user_content,
            thinking_enabled=request.thinking_enabled,
            thinking_budget=request.thinking_budget,
            total_questions=request.total_questions,
            reasoning_effort=request.reasoning_effort,
        ):
            yield result

    async def generate_image_questions(self, request: ImageQuestionsRequest) -> str:
        encoded_image = base64.b64encode(request.image_data).decode('utf-8')
        mime_type = f"image/{request.image_format}"
        user_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": encoded_image,
                },
            },
            {"type": "text", "text": request.prompt},
        ]
        return await _anthropic_generate(
            api_key=request.api_key,
            model=request.model,
            system_prompt=request.system_prompt,
            user_content=user_content,
            thinking_enabled=request.thinking_enabled,
            thinking_budget=request.thinking_budget,
            reasoning_effort=request.reasoning_effort,
        )

    async def generate_reading_material(self, request: ReadingMaterialRequest) -> str:
        user_content = []

        if request.image_data and request.image_format:
            encoded_image = base64.b64encode(request.image_data).decode('utf-8')
            mime_type = f"image/{request.image_format}"
            user_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": encoded_image,
                },
            })

        if request.pdf_content:
            user_content.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": request.pdf_content,
                },
            })

        user_content.append({"type": "text", "text": request.full_prompt})

        return await _anthropic_generate(
            api_key=request.api_key,
            model=request.model,
            system_prompt=request.system_prompt,
            user_content=user_content,
            thinking_enabled=request.thinking_enabled,
            thinking_budget=request.thinking_budget,
            reasoning_effort=request.reasoning_effort,
        )


class GeminiAdapter(ProviderAdapter):
    def __init__(self):
        super().__init__("gemini")

    async def generate_text_questions(self, request: TextQuestionsRequest) -> AsyncGenerator[dict, None]:
        pdf_bytes = base64.b64decode(request.pdf_content)
        user_content = [
            {"type": "pdf_bytes", "data": pdf_bytes, "mime_type": "application/pdf"},
            {"type": "text", "text": request.prompt},
        ]
        yaml_response = await _gemini_generate(
            api_key=request.api_key,
            model=request.model,
            system_prompt=request.system_prompt,
            user_content=user_content,
            thinking_enabled=request.thinking_enabled,
            thinking_budget=request.thinking_budget,
        )
        yield {
            "yaml": yaml_response,
            "count": request.total_questions,
            "progress": 1.0,
            "completed": True,
        }

    async def generate_image_questions(self, request: ImageQuestionsRequest) -> str:
        mime_type = f"image/{request.image_format}"
        user_content = [
            {"type": "image_bytes", "data": request.image_data, "mime_type": mime_type},
            {"type": "text", "text": request.prompt},
        ]
        return await _gemini_generate(
            api_key=request.api_key,
            model=request.model,
            system_prompt=request.system_prompt,
            user_content=user_content,
            thinking_enabled=request.thinking_enabled,
            thinking_budget=request.thinking_budget,
        )

    async def generate_reading_material(self, request: ReadingMaterialRequest) -> str:
        if request.content_type == "slide_deck":
            result = await _gemini_generate_illustrated(
                api_key=request.api_key,
                model=request.model,
                system_prompt=request.system_prompt,
                user_content=request.user_content,
                thinking_enabled=request.thinking_enabled,
                thinking_budget=request.thinking_budget,
                image_aspect_ratio="16:9",
            )
            return _merge_one_run_slide_deck_content(result["text"], result["images"])

        result = await _gemini_generate_illustrated(
            api_key=request.api_key,
            model=request.model,
            system_prompt=request.system_prompt,
            user_content=request.user_content,
            thinking_enabled=request.thinking_enabled,
            thinking_budget=request.thinking_budget,
        )
        return _append_images_to_markdown(result["text"], result["images"])


ADAPTERS: dict[str, ProviderAdapter] = {
    "openai": OpenAIAdapter(),
    "anthropic": AnthropicAdapter(),
    "gemini": GeminiAdapter(),
}


def get_adapter(model: str) -> ProviderAdapter:
    provider = get_provider(model)
    adapter = ADAPTERS.get(provider)
    if adapter is None:
        raise ValueError(f"Unknown provider: {provider}")
    return adapter


# =============================================================================
# Unified Public Functions
# =============================================================================

async def generate_text_questions(
    prompt: str,
    total_questions: int,
    model: str,
    api_key: str,
    pdf_content: str,
    thinking_enabled: bool = True,
    thinking_budget: int = 10000,
    reasoning_effort: str = "high"
) -> AsyncGenerator[dict, None]:
    """
    Generate questions from text/PDF content.

    Args:
        prompt: The generation prompt
        total_questions: Expected number of questions for progress tracking
        model: Model identifier
        api_key: API key for the provider
        pdf_content: Base64 encoded PDF content
        thinking_enabled: Enable extended thinking (Claude/Gemini)
        thinking_budget: Token budget for thinking (Claude/Gemini)
        reasoning_effort: Reasoning effort level (OpenAI: "low", "medium", "high")

    Yields:
        dict with keys: yaml, count, progress, completed
    """
    canonical_model = canonicalize_model(model)
    if requires_explicit_confirmation(canonical_model):
        raise ValueError(
            f"{canonical_model} requires an explicit UI confirmation step before execution."
        )
    if content_type == "slide_deck":
        provider = get_provider(canonical_model)
        if provider != "gemini":
            raise ValueError(
                "Illustrated slide decks require a Gemini image-preview model."
            )
        supported, error_message = validate_model_support(
            canonical_model,
            "generated_image_output",
        )
        if not supported:
            raise ValueError(error_message)

    adapter = get_adapter(canonical_model)
    resolved_api_key = adapter.resolve_api_key(api_key)

    if not resolved_api_key:
        raise ValueError(f"API key not configured for {adapter.provider}")

    supported, error_msg = validate_model_support(canonical_model, "pdf")
    if not supported:
        raise ValueError(error_msg)

    request = TextQuestionsRequest(
        prompt=prompt,
        total_questions=total_questions,
        model=canonical_model,
        api_key=resolved_api_key,
        pdf_content=pdf_content,
        system_prompt=PromptPrefixGenerator.get_system_prompt(),
        thinking_enabled=thinking_enabled,
        thinking_budget=thinking_budget,
        reasoning_effort=reasoning_effort,
    )

    try:
        async for result in _retry_async_stream(
            provider=adapter.provider,
            operation_name="generate_text_questions",
            stream_factory=lambda: adapter.generate_text_questions(request),
        ):
            yield result
    except Exception as e:
        raise ProviderAdapter.normalize_error(adapter.provider, e) from e


async def generate_image_questions(
    prompt: str,
    image_data: bytes,
    image_format: str,
    model: str,
    api_key: str,
    thinking_enabled: bool = True,
    thinking_budget: int = 10000,
    reasoning_effort: str = "medium"
) -> str:
    """
    Generate questions from an image.

    Args:
        prompt: The generation prompt
        image_data: Raw image bytes
        image_format: Image format (jpeg, png, webp, gif)
        model: Model identifier
        api_key: API key for the provider
        thinking_enabled: Enable extended thinking (Claude/Gemini)
        thinking_budget: Token budget for thinking (Claude/Gemini)
        reasoning_effort: Reasoning effort level (OpenAI)

    Returns:
        YAML string of generated questions
    """
    canonical_model = canonicalize_model(model)
    if requires_explicit_confirmation(canonical_model):
        raise ValueError(
            f"{canonical_model} requires an explicit UI confirmation step before execution."
        )
    if content_type == "slide_deck":
        provider = get_provider(canonical_model)
        if provider != "gemini":
            raise ValueError(
                "Illustrated slide decks require a Gemini image-preview model."
            )
        supported, error_message = validate_model_support(
            canonical_model,
            "generated_image_output",
        )
        if not supported:
            raise ValueError(error_message)

    adapter = get_adapter(canonical_model)
    resolved_api_key = adapter.resolve_api_key(api_key)

    if not resolved_api_key:
        raise ValueError(f"API key not configured for {adapter.provider}")

    supported, error_msg = validate_model_support(canonical_model, "image")
    if not supported:
        raise ValueError(error_msg)

    request = ImageQuestionsRequest(
        prompt=prompt,
        image_data=image_data,
        image_format=image_format,
        model=canonical_model,
        api_key=resolved_api_key,
        system_prompt="You are a question generator outputting only valid YAML. Do not include ``` markers.",
        thinking_enabled=thinking_enabled,
        thinking_budget=thinking_budget,
        reasoning_effort=reasoning_effort,
    )

    try:
        return await _retry_async_call(
            provider=adapter.provider,
            operation_name="generate_image_questions",
            fn=lambda: adapter.generate_image_questions(request),
        )
    except Exception as e:
        raise ProviderAdapter.normalize_error(adapter.provider, e) from e


async def generate_reading_material(
    grade_level: str,
    topic: str,
    objectives: list[str],
    user_prompt: str,
    model: str,
    api_key: str,
    image_data: bytes | None = None,
    image_format: str | None = None,
    pdf_content: str | None = None,
    thinking_enabled: bool = True,
    thinking_budget: int = 10000,
    reasoning_effort: str = "high",
    content_type: str = "reading_material"
) -> str:
    """
    Generate educational reading material.

    Args:
        grade_level: Target grade level (e.g., "K-2", "6-8", "9-12")
        topic: Subject/topic of the reading material
        objectives: List of learning objectives
        user_prompt: Additional custom instructions
        model: Model identifier
        api_key: API key for the provider
        image_data: Optional image bytes to incorporate
        image_format: Image format if image_data provided
        pdf_content: Optional Base64 encoded PDF content
        thinking_enabled: Enable extended thinking (Claude/Gemini)
        thinking_budget: Token budget for thinking (Claude/Gemini)
        reasoning_effort: Reasoning effort level (OpenAI)

    Returns:
        Generated reading material text
    """
    canonical_model = canonicalize_model(model)
    if requires_explicit_confirmation(canonical_model):
        raise ValueError(
            f"{canonical_model} requires an explicit UI confirmation step before execution."
        )
    if content_type == "slide_deck":
        provider = get_provider(canonical_model)
        if provider != "gemini":
            raise ValueError(
                "Illustrated slide decks require a Gemini image-preview model."
            )
        supported, error_message = validate_model_support(
            canonical_model,
            "generated_image_output",
        )
        if not supported:
            raise ValueError(error_message)

    adapter = get_adapter(canonical_model)
    resolved_api_key = adapter.resolve_api_key(api_key)

    if not resolved_api_key:
        raise ValueError(f"API key not configured for {adapter.provider}")

    # Select the appropriate system prompt based on content type
    is_slide_deck = content_type == "slide_deck"
    system_prompt = SLIDE_DECK_PROMPT if is_slide_deck else READING_MATERIAL_ILLUSTRATED_PROMPT

    # Build the user prompt
    objectives_text = "\n".join(f"- {obj}" for obj in objectives) if objectives else "Not specified"
    content_label = "slide deck presentation" if is_slide_deck else "reading material"

    full_prompt = f"""Please generate an educational {content_label} with the following specifications:

Grade Level: {grade_level}
Topic: {topic}

Learning Objectives:
{objectives_text}

Additional Instructions:
{user_prompt if user_prompt else "None"}

Please generate engaging, age-appropriate content that addresses all the learning objectives."""

    user_content: list[dict] = []
    if image_data and image_format:
        user_content.append(
            {
                "type": "image_bytes",
                "data": image_data,
                "mime_type": f"image/{image_format}",
            }
        )
    if pdf_content:
        user_content.append(
            {
                "type": "pdf_bytes",
                "data": base64.b64decode(pdf_content),
                "mime_type": "application/pdf",
            }
        )
    user_content.append({"type": "text", "text": full_prompt})

    request = ReadingMaterialRequest(
        full_prompt=full_prompt,
        model=canonical_model,
        api_key=resolved_api_key,
        system_prompt=system_prompt,
        grade_level=grade_level,
        topic=topic,
        user_content=user_content,
        content_type=content_type,
        image_data=image_data,
        image_format=image_format,
        pdf_content=pdf_content,
        thinking_enabled=thinking_enabled,
        thinking_budget=thinking_budget,
        reasoning_effort=reasoning_effort,
    )

    try:
        return await _retry_async_call(
            provider=adapter.provider,
            operation_name="generate_reading_material",
            fn=lambda: adapter.generate_reading_material(request),
        )
    except Exception as e:
        raise ProviderAdapter.normalize_error(adapter.provider, e) from e


# =============================================================================
# Legacy/Helper Functions
# =============================================================================

def process_pdf_for_llm(pdf_data: bytes) -> str:
    """Process PDF data for LLM consumption - convert to Base64."""
    return base64.b64encode(pdf_data).decode('utf-8')


def validate_yaml_response(yaml_str: str) -> bool:
    """Validate that YAML response meets specific structure requirements."""
    import yaml
    try:
        questions = yaml.safe_load(yaml_str)
        if not isinstance(questions, list):
            return False

        for q in questions:
            if not isinstance(q, dict):
                return False

            # Required base fields
            if not {'type', 'identifier', 'title', 'prompt'}.issubset(q.keys()):
                return False

        return True

    except yaml.YAMLError:
        return False
    except Exception:
        return False


def fix_yaml_format(yaml_str: str) -> str:
    """Fix common YAML formatting issues."""
    # Remove any markdown code block markers
    yaml_str = yaml_str.replace('```yaml', '').replace('```', '')

    # Remove any explanatory text before the YAML content
    if not yaml_str.strip().startswith('- type:'):
        parts = yaml_str.split('---\n')
        yaml_str = parts[-1].strip()

    # Ensure proper list formatting
    if not yaml_str.startswith('- '):
        yaml_str = '- ' + yaml_str

    return yaml_str


# =============================================================================
# Backward Compatibility - Legacy function signatures
# =============================================================================

async def generate_openai_response(
    prompt: str, total_questions: int, api_key: str, pdf_content: str
):
    """Legacy function - wraps generate_text_questions for backward compatibility."""
    model = get_config_value("OPENAI_REASON_MODEL", DEFAULT_OPENAI_MODEL)
    async for result in generate_text_questions(
        prompt=prompt,
        total_questions=total_questions,
        model=model,
        api_key=api_key,
        pdf_content=pdf_content,
        thinking_enabled=True,
        reasoning_effort="high"
    ):
        yield result


def generate_anthropic_response(
    prompt: str, pdf_content: str, api_key: str, model: str = DEFAULT_ANTHROPIC_MODEL
) -> str:
    """Legacy function - wraps generate_text_questions for backward compatibility."""
    import asyncio

    async def _run():
        result = None
        async for r in generate_text_questions(
            prompt=prompt,
            total_questions=1,
            model=model,
            api_key=api_key,
            pdf_content=pdf_content,
            thinking_enabled=True,
            thinking_budget=10000
        ):
            result = r
        return result.get("yaml", "") if result else ""

    return asyncio.get_event_loop().run_until_complete(_run())
