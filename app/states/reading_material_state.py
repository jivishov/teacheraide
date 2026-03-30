"""
Reading Material State

State management for the reading material generation page.
"""

import reflex as rx
from typing import List
import base64
import os
import logging
import re

from app.states.settings_state import SettingsState
from app.utils.input_limits import (
    MAX_IMAGE_UPLOAD_BYTES,
    MAX_LONG_TEXT_CHARS,
    MAX_PDF_UPLOAD_BYTES,
    enforce_text_limit,
    exceeds_upload_limit,
    text_limit_error,
    upload_limit_error,
)
from app.utils.llm_handlers import (
    generate_reading_material,
    get_provider,
    get_api_key_for_provider,
    release_openai_cached_file,
    validate_model_support,
)
from app.utils.model_catalog import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OPENAI_MODEL,
)


_SLIDE_IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)")


def _split_slide_deck_markdown(content: str) -> list[dict[str, str]]:
    slides: list[dict[str, str]] = []
    current_title = ""
    current_lines: list[str] = []

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            if current_title or current_lines:
                slides.append(
                    {
                        "title": current_title or "Slide",
                        "body": "\n".join(current_lines).strip(),
                    }
                )
            current_title = line[3:].strip() or "Slide"
            current_lines = []
            continue
        current_lines.append(line)

    if current_title or current_lines:
        slides.append(
            {
                "title": current_title or "Slide",
                "body": "\n".join(current_lines).strip(),
            }
        )

    return [slide for slide in slides if slide["title"] or slide["body"]]


def _extract_first_slide_image(markdown_text: str) -> tuple[str | None, str | None, str]:
    match = _SLIDE_IMAGE_RE.search(markdown_text)
    if not match:
        return None, None, markdown_text.strip()

    remaining = (
        markdown_text[:match.start()] + markdown_text[match.end():]
    ).strip()
    return match.group("alt") or "Illustration", match.group("src"), remaining


def _render_slide_deck_html(content: str) -> str:
    import markdown as md

    slides = _split_slide_deck_markdown(content)
    slide_sections: list[str] = []

    for slide in slides:
        alt_text, image_src, body_markdown = _extract_first_slide_image(slide["body"])
        body_html = md.markdown(body_markdown, extensions=["tables", "fenced_code"])
        visual_html = (
            f'<img src="{image_src}" alt="{alt_text or "Illustration"}" class="slide-image" />'
            if image_src
            else '<div class="slide-image-fallback">Illustration unavailable</div>'
        )
        slide_sections.append(
            f"""
            <section class="slide">
                <div class="slide-title">{slide["title"]}</div>
                <table class="slide-layout">
                    <tr>
                        <td class="slide-copy">{body_html or "<p>&nbsp;</p>"}</td>
                        <td class="slide-visual">{visual_html}</td>
                    </tr>
                </table>
            </section>
            """
        )

    css_style = """
        @page { size: landscape; margin: 0.45in; }
        body { font-family: Helvetica, Arial, sans-serif; color: #1f2937; }
        .slide {
            page-break-after: always;
        }
        .slide:last-child { page-break-after: auto; }
        .slide-title {
            font-size: 24pt;
            font-weight: bold;
            color: #1d4ed8;
            border-bottom: 2pt solid #bfdbfe;
            padding-bottom: 10pt;
            margin-bottom: 18pt;
        }
        .slide-layout {
            width: 100%;
            border-collapse: collapse;
        }
        .slide-copy {
            width: 58%;
            vertical-align: top;
            padding-right: 14pt;
            font-size: 14pt;
            line-height: 1.45;
        }
        .slide-copy h1, .slide-copy h2, .slide-copy h3 {
            color: #1e3a8a;
            margin: 0 0 8pt 0;
        }
        .slide-copy ul {
            margin: 0;
            padding-left: 18pt;
        }
        .slide-copy li {
            margin-bottom: 8pt;
        }
        .slide-visual {
            width: 42%;
            vertical-align: top;
            text-align: center;
            background: #f8fafc;
            border: 1pt solid #dbeafe;
            border-radius: 12pt;
            padding: 12pt;
        }
        .slide-image {
            width: 300pt;
            height: auto;
        }
        .slide-image-fallback {
            font-size: 13pt;
            color: #6b7280;
            border: 1pt dashed #cbd5e1;
            border-radius: 10pt;
            padding: 40pt 12pt;
            background: #ffffff;
        }
    """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><style>{css_style}</style></head>
    <body>{"".join(slide_sections)}</body>
    </html>
    """


class ReadingMaterialState(rx.State):
    """State for generating educational reading material."""

    # Input fields
    grade_level: str = ""
    topic: str = ""
    objectives: str = ""  # Comma or newline separated
    user_prompt: str = ""

    # Optional image
    uploaded_image_data: bytes = b""
    uploaded_image_filename: str = ""
    uploaded_image_format: str = ""

    # Optional PDF
    uploaded_pdf_data: bytes = b""
    uploaded_pdf_filename: str = ""

    # Content type selection
    content_type: str = "reading_material"  # "reading_material" or "slide_deck"
    content_types: List[str] = ["Reading Material", "Slide Deck"]

    # Output
    generated_content: str = ""
    generating: bool = False
    downloading: bool = False
    error_message: str = ""
    success_message: str = ""
    active_model: str = ""
    default_model_snapshot: str = ""
    persist_model_choice: bool = False
    model_picker_open: bool = False
    generation_stage: str = "Idle"
    progress: int = 0
    preflight_model_ready: bool = False
    preflight_api_key_ready: bool = False
    preflight_feature_ready: bool = False

    # Grade level options
    grade_levels: List[str] = [
        "K-2 (Ages 5-7)",
        "3-5 (Ages 8-10)",
        "6-8 (Ages 11-13)",
        "9-12 (Ages 14-18)",
        "College",
        "Adult/Professional"
    ]

    _TOPIC_LIMIT_ERROR = text_limit_error("Topic", MAX_LONG_TEXT_CHARS)
    _OBJECTIVES_LIMIT_ERROR = text_limit_error("Learning objectives", MAX_LONG_TEXT_CHARS)
    _PROMPT_LIMIT_ERROR = text_limit_error("Additional instructions", MAX_LONG_TEXT_CHARS)

    async def _release_cached_openai_pdf(self):
        if not self.uploaded_pdf_data:
            return

        settings_state = await self.get_state(SettingsState)
        api_key = get_api_key_for_provider("openai") or settings_state.openai_api_key
        if not api_key:
            return

        await release_openai_cached_file(api_key, self.uploaded_pdf_data)

    @rx.var
    def has_image(self) -> bool:
        """Check if an image has been uploaded."""
        return len(self.uploaded_image_data) > 0

    @rx.var
    def has_pdf(self) -> bool:
        """Check if a PDF has been uploaded."""
        return len(self.uploaded_pdf_data) > 0

    @rx.var
    def can_generate(self) -> bool:
        """Check if required fields are filled."""
        return bool(self.grade_level and self.topic)

    @rx.var
    def preflight_ready(self) -> bool:
        return (
            self.can_generate
            and self.preflight_model_ready
            and self.preflight_api_key_ready
            and self.preflight_feature_ready
        )

    @rx.var
    def objectives_list(self) -> List[str]:
        """Parse objectives into a list."""
        if not self.objectives:
            return []
        # Split by newlines or commas
        items = self.objectives.replace('\n', ',').split(',')
        return [item.strip() for item in items if item.strip()]

    @rx.var
    def is_slide_deck(self) -> bool:
        """Check if slide deck mode is selected."""
        return self.content_type == "slide_deck"

    @rx.var
    def active_model_display(self) -> str:
        """Display name for the active model."""
        if self.active_model.strip():
            return self.active_model
        if self.default_model_snapshot.strip():
            return self.default_model_snapshot
        return "Not selected"

    @rx.var
    def content_type_display(self) -> str:
        """Display name for the content type."""
        if self.content_type == "slide_deck":
            return "Slide Deck"
        return "Reading Material"

    @rx.event
    async def set_content_type(self, value: str):
        """Set the content type."""
        if value == "Slide Deck":
            self.content_type = "slide_deck"
        else:
            self.content_type = "reading_material"
        self.error_message = ""
        settings_state = await self.get_state(SettingsState)
        if self.content_type == "slide_deck":
            current_model = self.active_model.strip() or self.default_model_snapshot.strip()
            supported, _ = validate_model_support(current_model, "generated_image_output")
            if not supported:
                slide_model = settings_state.get_default_slide_deck_model()
                self.active_model = slide_model
                self.default_model_snapshot = slide_model
        else:
            default_model = self._resolve_default_model(
                settings_state, len(self.uploaded_image_data) > 0
            )
            self.default_model_snapshot = default_model
            if not self.active_model.strip():
                self.active_model = default_model
        await self._refresh_preflight(settings_state)

    def set_grade_level(self, value: str):
        """Set the grade level."""
        self.grade_level = value
        self.error_message = ""

    def set_topic(self, value: str):
        """Set the topic."""
        limited, truncated = enforce_text_limit(value, MAX_LONG_TEXT_CHARS)
        self.topic = limited
        if truncated:
            self.error_message = self._TOPIC_LIMIT_ERROR
            return
        if self.error_message == self._TOPIC_LIMIT_ERROR:
            self.error_message = ""

    def set_objectives(self, value: str):
        """Set the objectives."""
        limited, truncated = enforce_text_limit(value, MAX_LONG_TEXT_CHARS)
        self.objectives = limited
        if truncated:
            self.error_message = self._OBJECTIVES_LIMIT_ERROR
            return
        if self.error_message == self._OBJECTIVES_LIMIT_ERROR:
            self.error_message = ""

    def set_user_prompt(self, value: str):
        """Set additional instructions."""
        limited, truncated = enforce_text_limit(value, MAX_LONG_TEXT_CHARS)
        self.user_prompt = limited
        if truncated:
            self.error_message = self._PROMPT_LIMIT_ERROR
            return
        if self.error_message == self._PROMPT_LIMIT_ERROR:
            self.error_message = ""

    def _resolve_default_model(self, settings_state: SettingsState, use_image_context: bool) -> str:
        """Resolve default model from settings assignment for current context."""
        if self.content_type == "slide_deck":
            return settings_state.get_default_slide_deck_model()
        if use_image_context:
            model = settings_state.get_default_reading_material_with_image_model()
        else:
            model = settings_state.get_default_reading_material_model()
        if model:
            return model

        if os.getenv("OPENAI_API_KEY"):
            return settings_state.selected_openai_model or DEFAULT_OPENAI_MODEL
        if os.getenv("CLAUDE_API_KEY"):
            return settings_state.selected_anthropic_model or DEFAULT_ANTHROPIC_MODEL
        if os.getenv("GEMINI_API_KEY"):
            return settings_state.selected_gemini_model or DEFAULT_GEMINI_MODEL
        return ""

    def _resolve_api_key(self, provider: str, settings_state: SettingsState) -> str:
        """Resolve API key from env first, then in-app settings."""
        api_key = get_api_key_for_provider(provider)
        if api_key:
            return api_key
        if provider == "openai":
            return settings_state.openai_api_key
        if provider == "anthropic":
            return settings_state.anthropic_api_key
        if provider == "gemini":
            return settings_state.gemini_api_key
        return ""

    async def _refresh_preflight(self, settings_state: SettingsState):
        use_image_context = len(self.uploaded_image_data) > 0
        model = self.active_model.strip() or self._resolve_default_model(
            settings_state, use_image_context
        )
        required_feature = "generated_image_output" if self.content_type == "slide_deck" else (
            "image" if use_image_context else "pdf"
        )
        self.preflight_model_ready = bool(model)
        if model:
            provider = get_provider(model)
            self.preflight_api_key_ready = bool(self._resolve_api_key(provider, settings_state))
            self.preflight_feature_ready = validate_model_support(model, required_feature)[0]
        else:
            self.preflight_api_key_ready = False
            self.preflight_feature_ready = False

    @rx.event
    async def initialize_model_selection(self):
        """Initialize page-level model selection from Settings defaults."""
        settings_state = await self.get_state(SettingsState)
        settings_state.load_settings_from_disk()
        use_image_context = len(self.uploaded_image_data) > 0
        default_model = self._resolve_default_model(settings_state, use_image_context)
        self.default_model_snapshot = default_model
        self.active_model = default_model
        await self._refresh_preflight(settings_state)

    @rx.event
    async def select_active_model(self, model: str):
        """Set active model from quick-switch chips."""
        settings_state = await self.get_state(SettingsState)
        self.active_model = model
        if self.persist_model_choice:
            if self.content_type == "slide_deck":
                settings_state.set_slide_deck_model(model)
            elif len(self.uploaded_image_data) > 0:
                settings_state.set_reading_material_with_image_model(model)
            else:
                settings_state.set_reading_material_model(model)
            self.default_model_snapshot = model
        await self._refresh_preflight(settings_state)

    @rx.event
    def toggle_persist_model_choice(self):
        """Toggle whether quick-switch should update Settings defaults."""
        self.persist_model_choice = not self.persist_model_choice

    @rx.event
    def toggle_model_picker(self):
        """Toggle inline model picker visibility."""
        self.model_picker_open = not self.model_picker_open

    @rx.event
    async def reset_to_default_model(self):
        """Reset active model to current Settings default."""
        settings_state = await self.get_state(SettingsState)
        use_image_context = len(self.uploaded_image_data) > 0
        default_model = self._resolve_default_model(settings_state, use_image_context)
        self.default_model_snapshot = default_model
        self.active_model = default_model
        await self._refresh_preflight(settings_state)

    @rx.event
    async def refresh_preflight(self):
        """Refresh preflight checklist status."""
        settings_state = await self.get_state(SettingsState)
        await self._refresh_preflight(settings_state)

    async def handle_image_upload(self, files: List[rx.UploadFile]):
        """Handle image file upload."""
        if not files:
            return

        file = files[0]
        upload_data = await file.read()
        if exceeds_upload_limit(len(upload_data), MAX_IMAGE_UPLOAD_BYTES):
            self.error_message = upload_limit_error("Image", MAX_IMAGE_UPLOAD_BYTES)
            self.success_message = ""
            return

        # Determine image format from filename
        filename = file.filename.lower()
        if filename.endswith('.png'):
            img_format = 'png'
        elif filename.endswith('.gif'):
            img_format = 'gif'
        elif filename.endswith('.webp'):
            img_format = 'webp'
        else:
            img_format = 'jpeg'

        self.uploaded_image_data = upload_data
        self.uploaded_image_filename = file.filename
        self.uploaded_image_format = img_format
        self.error_message = ""
        self.success_message = f"Image '{file.filename}' uploaded successfully."
        settings_state = await self.get_state(SettingsState)
        await self._refresh_preflight(settings_state)

    def clear_image(self):
        """Clear the uploaded image."""
        self.uploaded_image_data = b""
        self.uploaded_image_filename = ""
        self.uploaded_image_format = ""
        self.success_message = ""

    async def handle_pdf_upload(self, files: List[rx.UploadFile]):
        """Handle PDF file upload."""
        if not files:
            return

        file = files[0]
        if self.uploaded_pdf_data:
            await self._release_cached_openai_pdf()
        upload_data = await file.read()
        if exceeds_upload_limit(len(upload_data), MAX_PDF_UPLOAD_BYTES):
            self.error_message = upload_limit_error("PDF", MAX_PDF_UPLOAD_BYTES)
            self.success_message = ""
            return

        self.uploaded_pdf_data = upload_data
        self.uploaded_pdf_filename = file.filename
        self.error_message = ""
        self.success_message = f"PDF '{file.filename}' uploaded successfully."
        settings_state = await self.get_state(SettingsState)
        await self._refresh_preflight(settings_state)

    @rx.event
    async def clear_pdf(self):
        """Clear the uploaded PDF."""
        await self._release_cached_openai_pdf()
        self.uploaded_pdf_data = b""
        self.uploaded_pdf_filename = ""
        self.success_message = ""

    def clear_output(self):
        """Clear generated content."""
        self.generated_content = ""
        self.error_message = ""
        self.success_message = ""

    @rx.event
    async def clear_all(self):
        """Clear all fields."""
        await self._release_cached_openai_pdf()
        self.grade_level = ""
        self.topic = ""
        self.objectives = ""
        self.user_prompt = ""
        self.uploaded_image_data = b""
        self.uploaded_image_filename = ""
        self.uploaded_image_format = ""
        self.uploaded_pdf_data = b""
        self.uploaded_pdf_filename = ""
        self.generated_content = ""
        self.error_message = ""
        self.success_message = ""

    @rx.event(background=True)
    async def handle_generate(self):
        """Generate reading material."""
        try:
            async with self:
                self.generation_stage = "Validating"
                self.progress = 10

                # Validation
                if not self.grade_level:
                    self.error_message = "Please select a grade level."
                    self.generation_stage = "Failed"
                    self.progress = 0
                    return

                if not self.topic:
                    self.error_message = "Please enter a topic."
                    self.generation_stage = "Failed"
                    self.progress = 0
                    return

                self.generating = True
                self.error_message = ""
                self.success_message = ""
                self.generated_content = ""

                # Get settings state (must be within async with self)
                settings_state = await self.get_state(SettingsState)
                await self._refresh_preflight(settings_state)

                # Extract all needed values from settings
                openai_api_key = settings_state.openai_api_key
                anthropic_api_key = settings_state.anthropic_api_key
                gemini_api_key = settings_state.gemini_api_key
                enable_thinking = settings_state.enable_thinking
                thinking_budget = settings_state.thinking_budget
                reasoning_effort = settings_state.reasoning_effort

                # Extract current state values
                grade_level = self.grade_level
                topic = self.topic
                objectives_list = self.objectives_list
                user_prompt = self.user_prompt
                content_type = self.content_type
                image_data = self.uploaded_image_data if self.has_image else None
                image_format = self.uploaded_image_format if self.has_image else None
                # Base64 encode PDF if present
                pdf_content = base64.b64encode(self.uploaded_pdf_data).decode("utf-8") if self.has_pdf else None
                use_image_context = len(self.uploaded_image_data) > 0
                default_model = self._resolve_default_model(settings_state, use_image_context)
                selected_model = self.active_model.strip() or default_model
                self.default_model_snapshot = default_model
                if not self.active_model and selected_model:
                    self.active_model = selected_model
                persist_choice = self.persist_model_choice

                if persist_choice and selected_model:
                    if content_type == "slide_deck":
                        settings_state.set_slide_deck_model(selected_model)
                    elif use_image_context:
                        settings_state.set_reading_material_with_image_model(selected_model)
                    else:
                        settings_state.set_reading_material_model(selected_model)

            # Yield to update UI with spinner before long API call
            async with self:
                self.generation_stage = "Preparing"
                self.progress = 25
            yield

            model = selected_model
            if not model:
                async with self:
                    self.error_message = "No model configured. Select a model here or in Settings."
                    self.generating = False
                    self.generation_stage = "Failed"
                    self.progress = 0
                return

            provider = get_provider(model)
            required_feature = "generated_image_output" if content_type == "slide_deck" else (
                "image" if image_data else "pdf"
            )
            supported, error_msg = validate_model_support(model, required_feature)
            if not supported:
                async with self:
                    self.error_message = error_msg
                    self.generating = False
                    self.generation_stage = "Failed"
                    self.progress = 0
                return

            api_key = get_api_key_for_provider(provider)
            if not api_key:
                if provider == "openai":
                    api_key = openai_api_key
                elif provider == "anthropic":
                    api_key = anthropic_api_key
                elif provider == "gemini":
                    api_key = gemini_api_key

            if not api_key:
                async with self:
                    self.error_message = f"{provider.capitalize()} API key not configured. Open Settings and add the key."
                    self.generating = False
                    self.generation_stage = "Failed"
                    self.progress = 0
                return

            try:
                # Generate content based on type
                async with self:
                    self.generation_stage = "Generating"
                    self.progress = 50
                content = await generate_reading_material(
                    grade_level=grade_level,
                    topic=topic,
                    objectives=objectives_list,
                    user_prompt=user_prompt,
                    model=model,
                    api_key=api_key,
                    image_data=image_data,
                    image_format=image_format,
                    pdf_content=pdf_content,
                    thinking_enabled=enable_thinking,
                    thinking_budget=thinking_budget,
                    reasoning_effort=reasoning_effort,
                    content_type=content_type
                )

                content_label = "Slide deck" if content_type == "slide_deck" else "Reading material"
                async with self:
                    self.generated_content = content
                    self.success_message = f"{content_label} generated successfully using {model}."
                    self.generating = False
                    self.generation_stage = "Ready"
                    self.progress = 100

            except Exception as e:
                async with self:
                    self.error_message = f"Generation failed: {str(e)}"
                    self.generating = False
                    self.generation_stage = "Failed"
                    self.progress = 0
        except Exception as e:
            logging.exception("Unexpected error during reading-material generation")
            async with self:
                self.error_message = f"An unexpected error occurred: {str(e)}"
                self.generating = False
                self.generation_stage = "Failed"
                self.progress = 0

    def copy_to_clipboard(self):
        """Copy generated content to clipboard (handled by frontend)."""
        # This will be handled by the frontend JavaScript
        pass

    @rx.event(background=True)
    async def download_pdf(self):
        """Download generated content as PDF."""
        import markdown as md
        from xhtml2pdf import pisa
        from io import BytesIO
        from datetime import datetime

        async with self:
            if not self.generated_content:
                return
            self.downloading = True
            content = self.generated_content
            is_slide = self.is_slide_deck

        yield  # Update UI to show spinner

        if is_slide:
            full_html = _render_slide_deck_html(content)
            file_prefix = "slide_deck"
        else:
            # Convert markdown to HTML
            html_content = md.markdown(
                content,
                extensions=['tables', 'fenced_code']
            )
            css_style = """
                @page { size: letter; margin: 1in; }
                body { font-family: Georgia, serif; font-size: 12pt; line-height: 1.6; }
                h1 { font-size: 20pt; color: #333; margin-top: 20pt; }
                h2 { font-size: 16pt; color: #333; margin-top: 16pt; }
                h3 { font-size: 14pt; color: #333; margin-top: 14pt; }
                img { max-width: 100%; height: auto; margin: 10pt 0; }
                p { margin-bottom: 10pt; }
            """
            file_prefix = "reading_material"
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head><style>{css_style}</style></head>
            <body>{html_content}</body>
            </html>
            """

        # Generate PDF
        pdf_buffer = BytesIO()
        pisa.CreatePDF(full_html, dest=pdf_buffer)
        pdf_bytes = pdf_buffer.getvalue()

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{file_prefix}_{timestamp}.pdf"

        async with self:
            self.downloading = False

        yield rx.download(data=pdf_bytes, filename=filename)
