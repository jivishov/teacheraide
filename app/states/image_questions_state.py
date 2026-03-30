"""
Image Questions State

Handles image-based question generation workflow.
Adapted from Streamlit version - integrated with Reflex state management.
"""

import reflex as rx
import logging
import base64
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Optional, TypedDict
import xml.etree.ElementTree as ET
from app.states.settings_state import SettingsState
from app.utils.image_questions import load_prompts_from_xml
from app.utils.yaml_converter import YAMLtoQTIConverter
from app.utils.llm_handlers import (
    fix_yaml_format,
    generate_image_questions,
    get_provider,
    get_api_key_for_provider,
    validate_model_support,
)
from app.utils.local_storage import get_save_image_questions_script, get_clear_image_questions_script
from app.utils.generation_progress import progress_for_stage
from app.utils.input_limits import (
    MAX_IMAGE_UPLOAD_BYTES,
    MAX_LONG_TEXT_CHARS,
    enforce_text_limit,
    exceeds_upload_limit,
    text_limit_error,
    upload_limit_error,
)
from app.utils.model_catalog import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OPENAI_MODEL,
)


class QuestionSummary(TypedDict):
    type: str
    count: int


class ImageQuestionsState(rx.State):
    """State for managing image-based question generation."""

    selected_subject: str = "Biology"
    assessment_type: str = "Formative"
    v2_active_preset: str = "Formative"
    assessment_title: str = "TeacherAIde Image-based Assessment"
    num_questions: int = 3
    generating: bool = False
    progress: int = 0
    error_message: str = ""
    package_ready: bool = False
    api_key: str = ""  # OpenAI API key
    active_model: str = ""
    default_model_snapshot: str = ""
    persist_model_choice: bool = False
    generation_stage: str = "Idle"
    preflight_model_ready: bool = False
    preflight_api_key_ready: bool = False
    preflight_feature_ready: bool = False
    v2_ui_mode: str = "quick"
    v2_expanded_slot: int = -1
    v2_batch_question_type: str = "Multiple choice"
    v2_special_instructions: str = ""
    model_picker_open: bool = False

    # Image upload tracking (per-image - max 10 slots)
    uploaded_images: List[str] = []  # List of uploaded image filenames (max 10)
    question_types: List[str] = []   # Question type for each image (max 10)
    image_prompts: List[str] = []    # User prompt for each image (max 10)

    # Generated data
    current_yaml: str = ""
    xml_questions: List[str] = []
    media_files: Dict[str, bytes] = {}
    question_summary: List[QuestionSummary] = []
    conversion_warning_count: int = 0
    conversion_warning_message: str = ""

    # Package delete modal state
    delete_package_modal_open: bool = False

    _PROMPT_LIMIT_ERROR = text_limit_error("Image prompt", MAX_LONG_TEXT_CHARS)
    _V2_SPECIAL_INSTRUCTIONS_LIMIT_ERROR = text_limit_error(
        "Special instructions", MAX_LONG_TEXT_CHARS
    )

    @rx.var
    def has_uploaded_images(self) -> bool:
        """Check if any images have been uploaded."""
        return any(img for img in self.uploaded_images if img)

    @rx.var
    def total_uploaded_images(self) -> int:
        """Count total number of uploaded images."""
        return sum(1 for img in self.uploaded_images if img)

    @rx.var
    def preflight_ready(self) -> bool:
        return (
            self.preflight_model_ready
            and self.preflight_api_key_ready
            and self.preflight_feature_ready
            and self.total_uploaded_images > 0
        )

    @rx.var
    def v2_is_quick_mode(self) -> bool:
        return self.v2_ui_mode == "quick"

    @rx.var
    def v2_total_slots(self) -> int:
        try:
            count = int(self.num_questions)
        except (TypeError, ValueError):
            count = 1
        return max(1, min(10, count))

    @rx.var
    def v2_images_ready_count(self) -> int:
        slots = self.v2_total_slots
        return sum(
            1
            for i in range(slots)
            if i < len(self.uploaded_images) and bool(self.uploaded_images[i])
        )

    @rx.var
    def v2_can_generate(self) -> bool:
        return (
            self.preflight_model_ready
            and self.preflight_api_key_ready
            and self.preflight_feature_ready
            and self.v2_images_ready_count > 0
            and not self.generating
        )

    @rx.var
    def v2_active_model_display(self) -> str:
        if self.active_model.strip():
            return self.active_model
        if self.default_model_snapshot.strip():
            return self.default_model_snapshot
        return "Not selected"

    def _resolve_default_model(self, settings_state: SettingsState) -> str:
        """Resolve default model for image questions from settings, then env-aware fallback."""
        model = settings_state.get_default_image_questions_model()
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

    def _quality_gate_xml(self, xml_questions: list[str]) -> tuple[bool, str]:
        """Basic quality gate for generated XML questions."""
        if not xml_questions:
            return False, "No XML questions were produced."

        ns = "{http://www.imsglobal.org/xsd/imsqti_v2p2}"
        for i, xml_str in enumerate(xml_questions, 1):
            if "__IMAGE_HTML_PLACEHOLDER__" in xml_str:
                return False, f"Question {i}: unresolved media placeholder."
            try:
                root = ET.fromstring(xml_str)
            except Exception:
                return False, f"Question {i}: invalid XML."

            prompt_el = root.find(f".//{ns}prompt")
            if prompt_el is not None:
                prompt_text = "".join(prompt_el.itertext()).strip()
            else:
                # FIB templates place prompt text directly inside itemBody <p> without a <prompt> tag.
                item_body = root.find(f".//{ns}itemBody")
                prompt_text = "".join(item_body.itertext()).strip() if item_body is not None else ""

            if not prompt_text:
                return False, f"Question {i}: missing prompt text."

            is_essay = root.find(f".//{ns}extendedTextInteraction") is not None
            if not is_essay:
                values = root.findall(f".//{ns}correctResponse/{ns}value")
                if len(values) == 0:
                    return False, f"Question {i}: missing correct response."

        return True, ""

    async def _refresh_preflight(self, settings_state: SettingsState):
        model = self.active_model.strip() or self._resolve_default_model(settings_state)
        self.preflight_model_ready = bool(model)
        if model:
            provider = get_provider(model)
            self.preflight_api_key_ready = bool(self._resolve_api_key(provider, settings_state))
            self.preflight_feature_ready = validate_model_support(model, "image")[0]
        else:
            self.preflight_api_key_ready = False
            self.preflight_feature_ready = False

    @rx.event
    async def initialize_model_selection(self):
        """Initialize page-level model selection from Settings defaults."""
        settings_state = await self.get_state(SettingsState)
        settings_state.load_settings_from_disk()
        default_model = self._resolve_default_model(settings_state)
        self.default_model_snapshot = default_model
        self.active_model = default_model
        await self._refresh_preflight(settings_state)

    @rx.event
    async def select_active_model(self, model: str):
        """Set active model from quick-switch chips."""
        settings_state = await self.get_state(SettingsState)
        self.active_model = model
        if self.persist_model_choice:
            settings_state.set_image_questions_model(model)
            self.default_model_snapshot = model
        await self._refresh_preflight(settings_state)

    @rx.event
    def toggle_persist_model_choice(self):
        """Toggle whether quick-switch should update Settings defaults."""
        self.persist_model_choice = not self.persist_model_choice

    @rx.event
    def toggle_model_picker(self):
        """Toggle the inline model picker visibility."""
        self.model_picker_open = not self.model_picker_open

    @rx.event
    async def reset_to_default_model(self):
        """Reset active model to current Settings default."""
        settings_state = await self.get_state(SettingsState)
        default_model = self._resolve_default_model(settings_state)
        self.default_model_snapshot = default_model
        self.active_model = default_model
        await self._refresh_preflight(settings_state)

    @rx.event
    async def refresh_preflight(self):
        """Refresh preflight checklist status."""
        settings_state = await self.get_state(SettingsState)
        await self._refresh_preflight(settings_state)

    @rx.event
    def set_selected_subject(self, value: str):
        self.selected_subject = value

    @rx.event
    def set_assessment_type(self, value: str):
        self.assessment_type = value

    @rx.event
    def apply_v2_preset(self, label: str):
        """Apply an assessment profile preset."""
        name_map = {"Quick Check": "Practice"}
        internal = name_map.get(label, label)
        self.v2_active_preset = label
        self.assessment_type = internal

    @rx.event
    def set_assessment_title(self, value: str):
        self.assessment_title = value

    def _parse_qti_xml(self, xml_string: str) -> str:
        """Parse QTI XML to determine question type."""
        try:
            ns = {"qti": "http://www.imsglobal.org/xsd/imsqti_v2p2"}
            root = ET.fromstring(xml_string)

            # Check baseType for T/F questions first
            resp_decl = root.find(".//qti:responseDeclaration", ns)
            if resp_decl is not None and resp_decl.get("baseType") == "boolean":
                return "TF"

            # Then check interaction types
            interaction = root.find(".//qti:itemBody", ns).find("*[1]")
            if interaction is not None:
                return interaction.tag.split("}")[-1].replace("Interaction", "")
        except Exception as e:
            logging.exception(f"Failed to parse QTI XML for type: {e}")
        return "Unknown"

    def _set_conversion_warnings(self, converter_warnings: list[str]):
        count = len(converter_warnings)
        self.conversion_warning_count = count
        if count > 0:
            self.conversion_warning_message = (
                f"{count} question{' was' if count == 1 else 's were'} skipped due to conversion issues."
            )
        else:
            self.conversion_warning_message = ""

    def set_num_questions_from_slider(self, value: List[float]):
        """Set number of questions from slider (converts list[float] to int)."""
        if value and len(value) > 0:
            self.num_questions = max(1, min(10, int(value[0])))
            if self.v2_expanded_slot >= self.num_questions:
                self.v2_expanded_slot = -1

    @rx.event
    def set_v2_ui_mode(self, mode: str):
        if mode in {"quick", "advanced"}:
            self.v2_ui_mode = mode

    @rx.event
    def toggle_v2_slot(self, index: int):
        if index < 0 or index >= self.v2_total_slots:
            return
        if self.v2_expanded_slot == index:
            self.v2_expanded_slot = -1
        else:
            self.v2_expanded_slot = index

    @rx.event
    def add_v2_slot(self):
        current_slots = self.v2_total_slots
        if current_slots >= 10:
            return
        self.num_questions = current_slots + 1

        while len(self.uploaded_images) < self.num_questions:
            self.uploaded_images.append("")
        while len(self.question_types) < self.num_questions:
            self.question_types.append(self.v2_batch_question_type)
        while len(self.image_prompts) < self.num_questions:
            self.image_prompts.append("")

    @rx.event
    def remove_v2_slot(self, index: int):
        current_slots = self.v2_total_slots
        if current_slots <= 1 or index < 0 or index >= current_slots:
            return

        if index < len(self.uploaded_images):
            self.uploaded_images.pop(index)
        if index < len(self.question_types):
            self.question_types.pop(index)
        if index < len(self.image_prompts):
            self.image_prompts.pop(index)

        self.num_questions = current_slots - 1

        if self.v2_expanded_slot == index:
            self.v2_expanded_slot = -1
        elif self.v2_expanded_slot > index:
            self.v2_expanded_slot -= 1
        elif self.v2_expanded_slot >= self.num_questions:
            self.v2_expanded_slot = -1

    @rx.event
    def set_v2_batch_question_type(self, value: str):
        self.v2_batch_question_type = value
        for idx in range(self.v2_total_slots):
            while len(self.question_types) <= idx:
                self.question_types.append(value)
            self.question_types[idx] = value

    @rx.event
    def set_v2_special_instructions(self, value: str):
        limited, truncated = enforce_text_limit(value, MAX_LONG_TEXT_CHARS)
        self.v2_special_instructions = limited
        if truncated:
            self.error_message = self._V2_SPECIAL_INSTRUCTIONS_LIMIT_ERROR
            return
        if self.error_message == self._V2_SPECIAL_INSTRUCTIONS_LIMIT_ERROR:
            self.error_message = ""

    # Helper methods for managing per-image data
    async def _handle_upload_at_index(self, files: List[rx.UploadFile], index: int):
        """Common upload logic for a specific index."""
        if not files:
            return

        try:
            upload_file = files[0]
            upload_data = await upload_file.read()
            if exceeds_upload_limit(len(upload_data), MAX_IMAGE_UPLOAD_BYTES):
                self.error_message = upload_limit_error("Image", MAX_IMAGE_UPLOAD_BYTES)
                return

            # Save to upload directory
            upload_dir = rx.get_upload_dir()
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / upload_file.name
            with file_path.open("wb") as f:
                f.write(upload_data)

            # Ensure lists are long enough
            while len(self.uploaded_images) <= index:
                self.uploaded_images.append("")
            while len(self.question_types) <= index:
                self.question_types.append("Multiple choice")
            while len(self.image_prompts) <= index:
                self.image_prompts.append("")

            self.uploaded_images[index] = upload_file.name
            self.error_message = ""
            logging.info(f"Uploaded image at slot {index}: {upload_file.name}")

        except Exception as e:
            logging.error(f"Error uploading image at slot {index}: {e}")
            self.error_message = f"Failed to upload image: {str(e)}"

    def _set_question_type_at_index(self, value: str, index: int):
        """Set question type at specific index."""
        while len(self.question_types) <= index:
            self.question_types.append("Multiple choice")
        self.question_types[index] = value

    def _set_prompt_at_index(self, value: str, index: int):
        """Set prompt at specific index."""
        while len(self.image_prompts) <= index:
            self.image_prompts.append("")
        limited, truncated = enforce_text_limit(value, MAX_LONG_TEXT_CHARS)
        self.image_prompts[index] = limited
        if truncated:
            self.error_message = self._PROMPT_LIMIT_ERROR
            return
        if self.error_message == self._PROMPT_LIMIT_ERROR:
            self.error_message = ""

    @rx.event
    async def handle_upload_at_index(self, files: List[rx.UploadFile], index: int):
        """Generic upload handler for any slot index."""
        await self._handle_upload_at_index(files, index)

    @rx.event
    async def handle_upload_0(self, files: List[rx.UploadFile]):
        await self._handle_upload_at_index(files, 0)

    @rx.event
    async def handle_upload_1(self, files: List[rx.UploadFile]):
        await self._handle_upload_at_index(files, 1)

    @rx.event
    async def handle_upload_2(self, files: List[rx.UploadFile]):
        await self._handle_upload_at_index(files, 2)

    @rx.event
    async def handle_upload_3(self, files: List[rx.UploadFile]):
        await self._handle_upload_at_index(files, 3)

    @rx.event
    async def handle_upload_4(self, files: List[rx.UploadFile]):
        await self._handle_upload_at_index(files, 4)

    @rx.event
    async def handle_upload_5(self, files: List[rx.UploadFile]):
        await self._handle_upload_at_index(files, 5)

    @rx.event
    async def handle_upload_6(self, files: List[rx.UploadFile]):
        await self._handle_upload_at_index(files, 6)

    @rx.event
    async def handle_upload_7(self, files: List[rx.UploadFile]):
        await self._handle_upload_at_index(files, 7)

    @rx.event
    async def handle_upload_8(self, files: List[rx.UploadFile]):
        await self._handle_upload_at_index(files, 8)

    @rx.event
    async def handle_upload_9(self, files: List[rx.UploadFile]):
        await self._handle_upload_at_index(files, 9)

    @rx.event
    async def handle_v2_batch_upload(self, files: List[rx.UploadFile]):
        """Handle batch uploads from v2 top dropzone."""
        if not files:
            return

        current_slots = self.v2_total_slots
        skipped_count = 0
        max_slots = 10

        for upload_file in files:
            target_index = -1

            for idx in range(current_slots):
                if idx >= len(self.uploaded_images) or not self.uploaded_images[idx]:
                    target_index = idx
                    break

            if target_index == -1:
                if current_slots >= max_slots:
                    skipped_count += 1
                    continue
                self.num_questions = current_slots + 1
                current_slots += 1
                target_index = current_slots - 1

            await self._handle_upload_at_index([upload_file], target_index)
            if target_index < len(self.question_types):
                self.question_types[target_index] = self.v2_batch_question_type

        if skipped_count > 0:
            self.error_message = (
                f"Reached maximum of {max_slots} image slots. "
                f"Skipped {skipped_count} additional image"
                f"{'' if skipped_count == 1 else 's'}."
            )

    @rx.event
    def set_question_type_at_index(self, index: int, value: str):
        """Generic question type setter for any slot index."""
        self._set_question_type_at_index(value, index)

    @rx.event
    def set_prompt_at_index(self, index: int, value: str):
        """Generic prompt setter for any slot index."""
        self._set_prompt_at_index(value, index)

    @rx.event
    async def handle_generate(self):
        """Generate questions from uploaded images."""
        self.generation_stage = "Validating"
        self.progress = progress_for_stage("Validating")
        yield
        settings_state = await self.get_state(SettingsState)
        await self._refresh_preflight(settings_state)
        # Validation
        valid_images = [img for img in self.uploaded_images if img]
        if not valid_images:
            self.error_message = "Please upload at least one image."
            self.generation_stage = "Failed"
            return

        # Determine model from page-level quick switch, then Settings default.
        model = self.active_model.strip()
        if not model:
            model = self._resolve_default_model(settings_state)
            self.active_model = model
            self.default_model_snapshot = model

        if not model:
            self.error_message = "No model configured. Select a model here or in Settings."
            self.generation_stage = "Failed"
            return

        if self.persist_model_choice and settings_state.image_questions_model != model:
            settings_state.set_image_questions_model(model)
            self.default_model_snapshot = model

        # Get API key for the provider
        provider = get_provider(model)
        supported, error_msg = validate_model_support(model, "image")
        if not supported:
            self.error_message = error_msg
            self.generation_stage = "Failed"
            return

        api_key = self._resolve_api_key(provider, settings_state)

        if not api_key:
            self.error_message = f"API key not configured for {provider}. Open Settings and add the key."
            self.generation_stage = "Failed"
            return

        self.generating = True
        self.progress = 0
        self.error_message = ""
        self.package_ready = False
        self.question_summary = []
        self.current_yaml = ""
        self.xml_questions = []
        self.media_files = {}
        self.conversion_warning_count = 0
        self.conversion_warning_message = ""
        self.generation_stage = "Preparing"
        self.progress = progress_for_stage("Preparing")
        yield

        try:
            # Load prompts from XML file
            prompts_file_path = Path("app/assets/prompts/image_quest_prompts.xml").resolve()
            prompts = load_prompts_from_xml(str(prompts_file_path))

            if not prompts:
                self.error_message = "Could not load prompts. Aborting generation."
                self.generating = False
                return

            # Type mapping
            type_map = {
                "Multiple choice": "mcq",
                "True/False": "tf",
                "Fill in blank": "fib",
                "Matching": "match"
            }

            yaml_questions = []
            upload_dir = rx.get_upload_dir()
            num_valid_uploads = len(valid_images)

            # Process each uploaded image
            self.generation_stage = "Generating"
            self.progress = progress_for_stage("Generating")
            yield
            for i, image_filename in enumerate(valid_images, 1):
                logging.info(f"Processing image {i}/{num_valid_uploads}: {image_filename}")

                # Keep progress inside the Generating step window while images are processed.
                generating_progress = progress_for_stage("Generating")
                parsing_progress = progress_for_stage("Parsing")
                progress_span = max(parsing_progress - generating_progress - 1, 0)
                if progress_span > 0 and num_valid_uploads > 0:
                    self.progress = generating_progress + int(i / num_valid_uploads * progress_span)
                else:
                    self.progress = generating_progress
                yield

                # Get question type and prompt for this specific image
                q_type = self.question_types[i-1] if i-1 < len(self.question_types) else "Multiple choice"
                img_prompt = self.image_prompts[i-1] if i-1 < len(self.image_prompts) else ""
                global_special = (self.v2_special_instructions or "").strip()
                if global_special:
                    if img_prompt.strip():
                        img_prompt = (
                            f"{img_prompt.strip()}\n\n"
                            f"Global special instructions: {global_special}"
                        )
                    else:
                        img_prompt = f"Global special instructions: {global_special}"

                mapped_type = type_map.get(q_type)
                prompt_template = prompts.get(mapped_type)

                if not mapped_type or not prompt_template:
                    logging.warning(f"Skipping image {image_filename}: No prompt found for type '{mapped_type}'.")
                    continue

                # Load image data
                image_path = upload_dir / image_filename
                with image_path.open("rb") as f:
                    image_data = f.read()

                self.media_files[image_filename] = image_data

                # Determine image format from filename
                filename_lower = image_filename.lower()
                if filename_lower.endswith('.png'):
                    image_format = 'png'
                elif filename_lower.endswith('.gif'):
                    image_format = 'gif'
                elif filename_lower.endswith('.webp'):
                    image_format = 'webp'
                else:
                    image_format = 'jpeg'

                # Format the instruction prompt
                try:
                    instruction = prompt_template.format(
                        i=i,
                        selected_subject=self.selected_subject,
                        img_prompt=img_prompt
                    )
                except KeyError as e:
                    logging.error(f"Missing placeholder {e} in prompt template for type '{mapped_type}'.")
                    continue

                # Inject assessment type guidance
                assessment_guidance = {
                    "Formative": "This is a FORMATIVE assessment — focus on checking understanding, use moderate difficulty, and aim to identify misconceptions.",
                    "Summative": "This is a SUMMATIVE assessment — create rigorous, evaluative questions that test deep knowledge and analytical thinking.",
                    "Practice": "This is a PRACTICE / quick-check assessment — use simple recall and basic comprehension, keep it straightforward.",
                    "Homework": "This is a HOMEWORK assessment — blend practice with moderate challenge, suitable for independent work.",
                }
                guidance = assessment_guidance.get(self.assessment_type, "")
                if guidance:
                    instruction += f"\n\nASSESSMENT CONTEXT: {guidance}"

                # Call unified image question generator
                try:
                    yaml_text = await generate_image_questions(
                        prompt=instruction,
                        image_data=image_data,
                        image_format=image_format,
                        model=model,
                        api_key=api_key,
                        thinking_enabled=settings_state.enable_thinking,
                        thinking_budget=settings_state.thinking_budget,
                        reasoning_effort=settings_state.reasoning_effort
                    )
                except Exception as e:
                    logging.error(f"Error generating question for image {image_filename}: {e}")
                    continue

                # Post-process YAML: replace image placeholder
                actual_image_html = f'<p><img src="media/{image_filename}" alt="Question related image {i}" width="400"/></p>'
                placeholder = "__IMAGE_HTML_PLACEHOLDER__"

                yaml_text = yaml_text.replace(f"'{placeholder}'", f"'{actual_image_html}'")
                yaml_text = yaml_text.replace(f'"{placeholder}"', f'"{actual_image_html}"')

                if placeholder in yaml_text:
                    logging.warning(f"Placeholder '{placeholder}' still found in YAML for image {i} after replacement.")

                # Clean markdown fences
                if yaml_text.startswith("```yaml"):
                    yaml_text = yaml_text.replace("```yaml", "").replace("```", "").strip()

                yaml_questions.append(yaml_text)

            if not yaml_questions:
                self.error_message = "No questions were generated or processed successfully."
                self.generating = False
                self.generation_stage = "Failed"
                return

            # Combine all YAML questions
            combined_yaml = "\n---\n".join(yaml_questions)
            self.current_yaml = combined_yaml

            # Convert YAML to QTI XML
            try:
                self.generation_stage = "Parsing"
                self.progress = progress_for_stage("Parsing")
                yield
                converter = YAMLtoQTIConverter(templates_dir="app/templates")
                xml_questions, conversion_warnings = converter.convert_with_warnings(combined_yaml)
                if not xml_questions:
                    repaired_yaml = fix_yaml_format(combined_yaml)
                    if repaired_yaml != combined_yaml:
                        self.current_yaml = repaired_yaml
                        repaired_xml, repaired_warnings = converter.convert_with_warnings(
                            repaired_yaml
                        )
                        xml_questions = repaired_xml
                        conversion_warnings.extend(repaired_warnings)
                self._set_conversion_warnings(conversion_warnings)

                if xml_questions:
                    self.xml_questions = xml_questions

                    quality_ok, quality_msg = self._quality_gate_xml(self.xml_questions)
                    if not quality_ok:
                        self.error_message = f"Quality check failed: {quality_msg}"
                        self.generating = False
                        self.generation_stage = "Failed"
                        return

                    # Note: ReviewState.on_load will pull questions from here when the review page loads

                    self.generation_stage = "Packaging"
                    self.progress = progress_for_stage("Packaging")
                    yield
                    # Generate question summary
                    summary_counts = {}
                    for xml_q in self.xml_questions:
                        q_type = self._parse_qti_xml(xml_q)
                        summary_counts[q_type] = summary_counts.get(q_type, 0) + 1
                    self.question_summary = [
                        {"type": q_type, "count": count}
                        for q_type, count in summary_counts.items()
                    ]

                    self.package_ready = True
                    self.generation_stage = "Ready"
                    self.progress = progress_for_stage("Ready")
                    logging.info("Image questions generated successfully!")

                    # Save to localStorage for cross-tab access
                    yield ImageQuestionsState.save_to_local_storage
                else:
                    self.error_message = "No valid QTI questions were generated after conversion."
                    logging.error("YAML to XML conversion produced no questions")
                    self.generation_stage = "Failed"

            except Exception as e:
                logging.exception(f"Error converting YAML to QTI or creating package: {str(e)}")
                self.error_message = f"Error converting YAML to QTI: {str(e)}"
                self.generation_stage = "Failed"

        except Exception as e:
            logging.exception(f"Error during image question generation: {e}")
            self.error_message = f"An unexpected error occurred: {str(e)}"
            self.generation_stage = "Failed"
        finally:
            self.generating = False

    @rx.event
    def download_image_package(self) -> rx.download:
        """Download image questions QTI package."""
        from app.utils.combined_questions import create_package_with_warnings
        from datetime import datetime

        if not self.xml_questions:
            return rx.toast.error("No questions available to download")

        package_bytes, package_warnings = create_package_with_warnings(
            test_title=self.assessment_title or "TeacherAIde Image Questions",
            questions=self.xml_questions,
            media_files=self.media_files,
            question_types='all',
            templates_dir="app/templates"
        )
        if package_warnings:
            self.conversion_warning_count = len(package_warnings)
            self.conversion_warning_message = (
                f"{len(package_warnings)} packaging warning"
                f"{'' if len(package_warnings) == 1 else 's'} detected."
            )

        if package_bytes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_questions_{timestamp}.zip"
            return rx.download(data=package_bytes, filename=filename)
        else:
            return rx.toast.error("Failed to create package")

    @rx.event
    def open_delete_package_modal(self):
        """Open delete confirmation modal for image package."""
        self.delete_package_modal_open = True

    @rx.event
    def close_delete_package_modal(self):
        """Close delete modal without deleting."""
        self.delete_package_modal_open = False

    @rx.event
    def confirm_delete_package(self):
        """Delete all image questions and media files, and clear localStorage."""
        self.current_yaml = ""
        self.xml_questions = []
        self.media_files = {}
        self.question_summary = []
        self.package_ready = False
        self.progress = 0
        self.conversion_warning_count = 0
        self.conversion_warning_message = ""
        self.error_message = ""
        self.delete_package_modal_open = False
        # Clear localStorage for cross-tab consistency
        return rx.call_script(get_clear_image_questions_script())

    @rx.event
    def save_to_local_storage(self):
        """Save generated questions and filenames to localStorage for cross-tab access."""
        if self.xml_questions:
            questions_json = json.dumps(self.xml_questions)
            filenames_json = json.dumps(list(self.media_files.keys()))
            return rx.call_script(get_save_image_questions_script(questions_json, filenames_json))

    @rx.event
    def clear_local_storage(self):
        """Clear image questions from localStorage."""
        return rx.call_script(get_clear_image_questions_script())
