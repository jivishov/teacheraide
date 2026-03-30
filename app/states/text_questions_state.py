import reflex as rx
import logging
import base64
import json
import os
from io import BytesIO
from typing import Any, Coroutine, TypedDict
import xml.etree.ElementTree as ET
from app.states.material_state import MaterialState
from app.states.settings_state import SettingsState
from app.prompts.qti_prompts import (
    create_complete_prompt,
    create_pdf_question_conversion_prompt,
)
from app.utils.yaml_converter import YAMLtoQTIConverter
from app.utils.llm_handlers import (
    fix_yaml_format,
    generate_text_questions,
    get_provider,
    get_api_key_for_provider,
    validate_model_support,
)
from app.utils.local_storage import get_save_text_questions_script, get_clear_text_questions_script
from app.utils.generation_progress import progress_for_stage
from app.utils.input_limits import (
    MAX_LONG_TEXT_CHARS,
    enforce_text_limit,
    text_limit_error,
)
from app.utils.model_catalog import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OPENAI_MODEL,
)


def compress_pdf(pdf_bytes: bytes) -> bytes:
    return pdf_bytes


ASSESSMENT_PROFILE_PRESETS: dict[str, dict[str, Any]] = {
    "Formative": {
        "question_counts": {"mcq": 4, "mrq": 1, "tf": 2, "order": 0, "fib": 2, "essay": 1, "match": 0},
        "cognitive_distribution": {"basic": 20, "intermediate": 50, "high": 30},
    },
    "Summative": {
        "question_counts": {"mcq": 6, "mrq": 2, "tf": 2, "order": 1, "fib": 2, "essay": 2, "match": 1},
        "cognitive_distribution": {"basic": 15, "intermediate": 45, "high": 40},
    },
    "Quick-check": {
        "question_counts": {"mcq": 4, "mrq": 0, "tf": 3, "order": 0, "fib": 1, "essay": 0, "match": 0},
        "cognitive_distribution": {"basic": 55, "intermediate": 35, "high": 10},
    },
    "Homework": {
        "question_counts": {"mcq": 5, "mrq": 1, "tf": 2, "order": 1, "fib": 2, "essay": 1, "match": 1},
        "cognitive_distribution": {"basic": 30, "intermediate": 45, "high": 25},
    },
    # Backward compatibility alias for older saved sessions/UI labels.
    "Practice": {
        "question_counts": {"mcq": 4, "mrq": 0, "tf": 3, "order": 0, "fib": 1, "essay": 0, "match": 0},
        "cognitive_distribution": {"basic": 55, "intermediate": 35, "high": 10},
    },
}


def get_assessment_profile(profile_name: str) -> dict[str, dict[str, int]]:
    profile = ASSESSMENT_PROFILE_PRESETS.get(profile_name)
    if profile is None:
        profile = ASSESSMENT_PROFILE_PRESETS["Formative"]
    return {
        "question_counts": dict(profile["question_counts"]),
        "cognitive_distribution": dict(profile["cognitive_distribution"]),
    }


def build_prompt(
    content_type: str,
    assessment_type: str,
    counts: dict,
    instructions: str,
    cognitive_distribution: dict[str, int] | None = None,
) -> str:
    return create_complete_prompt(
        instructions,
        content_type,
        assessment_type,
        counts,
        cognitive_distribution=cognitive_distribution,
    )


def resolve_text_workflow_mode(intent: str | None) -> str:
    """Resolve text workflow mode from upload-page intent."""
    return "convert_pdf_questions" if intent == "convert_pdf_questions" else "generate"


def summarize_conversion_warnings(yaml_count: int, xml_count: int) -> tuple[int, str]:
    """Summarize skipped items after YAML -> XML conversion."""
    skipped = max(int(yaml_count) - int(xml_count), 0)
    if skipped <= 0:
        return 0, ""
    return (
        skipped,
        (
            f"Converted {xml_count} of {yaml_count} questions. "
            f"{skipped} were skipped due to invalid or unsupported structure."
        ),
    )


def validate_yaml(yaml_text: str) -> tuple[bool, str, list]:
    import yaml

    try:
        data = yaml.safe_load(yaml_text)
        if not isinstance(data, list):
            return (False, "YAML is not a list", [])
        return (True, "", data)
    except yaml.YAMLError as e:
        logging.exception(f"Error parsing YAML: {e}")
        return (False, f"Invalid YAML: {e}", [])


def yaml_to_qti_xml_with_warnings(yaml_str: str) -> tuple[list[str], list[str]]:
    """Convert YAML to QTI XML and return non-fatal converter warnings."""
    try:
        converter = YAMLtoQTIConverter(templates_dir="app/templates")
        xml_questions, warnings = converter.convert_with_warnings(yaml_str)
        return xml_questions, warnings
    except Exception as e:
        logging.error(f"Error converting YAML to QTI: {e}")
        return [], [f"YAML to QTI conversion error: {str(e)}"]


def yaml_to_qti_xml(yaml_str: str) -> list[str]:
    """Backward-compatible conversion helper returning only XML questions."""
    xml_questions, _warnings = yaml_to_qti_xml_with_warnings(yaml_str)
    return xml_questions


class QuestionSummary(TypedDict):
    type: str
    count: int


async def generate_questions_unified(
    pdf_b64: str,
    prompt: str,
    total: int,
    model: str,
    api_key: str,
    thinking_enabled: bool = True,
    thinking_budget: int = 10000,
    reasoning_effort: str = "high"
) -> Coroutine[dict, None, None]:
    """Generate questions using unified LLM interface with streaming."""
    async for update in generate_text_questions(
        prompt=prompt,
        total_questions=total,
        model=model,
        api_key=api_key,
        pdf_content=pdf_b64,
        thinking_enabled=thinking_enabled,
        thinking_budget=thinking_budget,
        reasoning_effort=reasoning_effort
    ):
        yield update


class TextQuestionsState(rx.State):
    content_type: str = "rm_q"
    workflow_mode: str = "generate"
    assessment_type: str = "Formative"
    selected_subject: str = "Biology"
    assessment_title: str = "TeacherAIde Text Assessment"
    special_instructions: str = ""
    v2_ui_mode: str = "quick"
    v2_active_preset: str = "Formative"
    question_counts: dict[str, int] = dict(
        ASSESSMENT_PROFILE_PRESETS["Formative"]["question_counts"]
    )
    cognitive_distribution: dict[str, int] = dict(
        ASSESSMENT_PROFILE_PRESETS["Formative"]["cognitive_distribution"]
    )
    generating: bool = False
    progress: int = 0
    total_questions: int = 0
    current_yaml: str = ""
    xml_questions: list[str] = []
    error_message: str = ""
    package_ready: bool = False
    question_summary: list[QuestionSummary] = []
    api_key: str = ""  # OpenAI API key (user should set from environment or UI)
    active_model: str = ""
    default_model_snapshot: str = ""
    persist_model_choice: bool = False
    generation_stage: str = "Idle"
    preflight_pdf_ready: bool = False
    preflight_model_ready: bool = False
    preflight_api_key_ready: bool = False
    preflight_feature_ready: bool = False
    profile_note: str = ""
    conversion_warning_count: int = 0
    conversion_warning_message: str = ""

    # UI toggles
    model_picker_open: bool = False
    # Package delete modal state
    delete_package_modal_open: bool = False
    _SPECIAL_INSTRUCTIONS_LIMIT_ERROR = text_limit_error(
        "Special instructions", MAX_LONG_TEXT_CHARS
    )

    @rx.var
    def calculated_total_questions(self) -> int:
        return sum(self.question_counts.values())

    @rx.var
    def cognitive_basic_percent(self) -> int:
        return int(self.cognitive_distribution.get("basic", 0))

    @rx.var
    def cognitive_intermediate_percent(self) -> int:
        return int(self.cognitive_distribution.get("intermediate", 0))

    @rx.var
    def cognitive_high_percent(self) -> int:
        return int(self.cognitive_distribution.get("high", 0))

    @rx.var
    def cognitive_distribution_summary(self) -> str:
        return (
            f"Basic {self.cognitive_basic_percent}% | "
            f"Intermediate {self.cognitive_intermediate_percent}% | "
            f"High {self.cognitive_high_percent}%"
        )

    @rx.var
    def preflight_ready(self) -> bool:
        count_ready = (
            True
            if self.workflow_mode == "convert_pdf_questions"
            else self.calculated_total_questions > 0
        )
        return (
            self.preflight_pdf_ready
            and self.preflight_model_ready
            and self.preflight_api_key_ready
            and self.preflight_feature_ready
            and count_ready
        )

    @rx.var
    def is_conversion_mode(self) -> bool:
        return self.workflow_mode == "convert_pdf_questions"

    @rx.var
    def is_v2_quick_mode(self) -> bool:
        return self.v2_ui_mode == "quick"

    @rx.var
    def v2_estimated_output_label(self) -> str:
        if self.is_conversion_mode:
            return "Questions are auto-detected from the uploaded PDF in conversion mode."
        return f"~{self.calculated_total_questions} questions, mixed difficulty"

    @rx.var
    def v2_active_model_display(self) -> str:
        if self.active_model.strip():
            return self.active_model
        if self.default_model_snapshot.strip():
            return self.default_model_snapshot
        return "Not selected"

    def _resolve_default_model(self, settings_state: SettingsState) -> str:
        """Resolve default model from settings assignment first, then provider fallbacks."""
        model = settings_state.get_default_text_questions_model()
        if model:
            return model

        if os.getenv("OPENAI_API_KEY"):
            return settings_state.selected_openai_model or os.getenv(
                "OPENAI_REASON_MODEL", DEFAULT_OPENAI_MODEL
            )
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

            # Essay questions can intentionally skip explicit correctResponse.
            is_essay = root.find(f".//{ns}extendedTextInteraction") is not None
            if not is_essay:
                values = root.findall(f".//{ns}correctResponse/{ns}value")
                if len(values) == 0:
                    return False, f"Question {i}: missing correct response."

        return True, ""

    async def _refresh_preflight(self, settings_state: SettingsState, material_state: MaterialState):
        model = self.active_model.strip() or self._resolve_default_model(settings_state)
        self.preflight_pdf_ready = bool(material_state.extracted_pdf_name)
        self.preflight_model_ready = bool(model)
        if model:
            provider = get_provider(model)
            self.preflight_api_key_ready = bool(self._resolve_api_key(provider, settings_state))
            self.preflight_feature_ready = validate_model_support(model, "pdf")[0]
        else:
            self.preflight_api_key_ready = False
            self.preflight_feature_ready = False

    @rx.event
    async def initialize_model_selection(self):
        """Initialize page-level model selection from Settings defaults."""
        settings_state = await self.get_state(SettingsState)
        material_state = await self.get_state(MaterialState)
        settings_state.load_settings_from_disk()
        self.workflow_mode = resolve_text_workflow_mode(
            material_state._consume_workflow_intent_once()
        )
        if self.workflow_mode == "convert_pdf_questions":
            self.content_type = "siml_q"
        self.profile_note = (
            "PDF question conversion mode: question counts are auto-detected from source PDF."
            if self.workflow_mode == "convert_pdf_questions"
            else ""
        )
        default_model = self._resolve_default_model(settings_state)
        self.default_model_snapshot = default_model
        self.active_model = default_model
        await self._refresh_preflight(settings_state, material_state)

    @rx.event
    async def select_active_model(self, model: str):
        """Set active model from quick-switch chips."""
        settings_state = await self.get_state(SettingsState)
        material_state = await self.get_state(MaterialState)
        self.active_model = model
        if self.persist_model_choice:
            settings_state.set_text_questions_model(model)
            self.default_model_snapshot = model
        await self._refresh_preflight(settings_state, material_state)

    @rx.event
    def toggle_persist_model_choice(self):
        """Toggle whether quick-switch should update Settings defaults."""
        self.persist_model_choice = not self.persist_model_choice

    @rx.event
    async def reset_to_default_model(self):
        """Reset active model to current Settings default."""
        settings_state = await self.get_state(SettingsState)
        material_state = await self.get_state(MaterialState)
        default_model = self._resolve_default_model(settings_state)
        self.default_model_snapshot = default_model
        self.active_model = default_model
        await self._refresh_preflight(settings_state, material_state)

    @rx.event
    async def refresh_preflight(self):
        """Refresh preflight checklist status."""
        settings_state = await self.get_state(SettingsState)
        material_state = await self.get_state(MaterialState)
        await self._refresh_preflight(settings_state, material_state)

    def _parse_qti_xml(self, xml_string: str) -> str:
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

    def _set_conversion_warnings(
        self,
        yaml_count: int,
        xml_count: int,
        converter_warnings: list[str],
    ):
        warning_count = len(converter_warnings)
        warning_messages: list[str] = []

        if converter_warnings:
            verb = "was" if len(converter_warnings) == 1 else "were"
            warning_messages.append(
                (
                    f"{len(converter_warnings)} question"
                    f"{'' if len(converter_warnings) == 1 else 's'}"
                    f" {verb} skipped due to conversion issues."
                )
            )

        if self.workflow_mode == "convert_pdf_questions":
            skipped_count, skipped_msg = summarize_conversion_warnings(yaml_count, xml_count)
            if skipped_count > warning_count:
                warning_count = skipped_count
                warning_messages = [skipped_msg]

        self.conversion_warning_count = warning_count
        self.conversion_warning_message = " ".join(warning_messages)

    def _set_custom_count_note(self):
        self.profile_note = (
            f"Using {self.assessment_type} cognitive mix ({self.cognitive_distribution_summary}) "
            "with custom question-count edits."
        )

    def _apply_profile(self, profile_name: str):
        profile = get_assessment_profile(profile_name)
        self.question_counts = profile["question_counts"]
        self.cognitive_distribution = profile["cognitive_distribution"]

    @rx.event
    def set_v2_ui_mode(self, mode: str):
        if mode in {"quick", "advanced"}:
            self.v2_ui_mode = mode

    @rx.event
    def apply_v2_preset(self, label: str):
        profile_name = {
            "Formative": "Formative",
            "Summative": "Summative",
            "Quick Check": "Practice",
            "Homework": "Homework",
            "Practice": "Practice",
        }.get(label)
        if profile_name is None:
            return
        self.v2_active_preset = label
        self.assessment_type = profile_name
        self._apply_profile(profile_name)
        self.profile_note = (
            f"Applied {label} preset. "
            f"Cognitive mix: {self.cognitive_distribution_summary}."
        )

    @rx.event
    def set_v2_content_type(self, value: str):
        if value in {"rm_q", "siml_q", "diffr_q", "sld_q"}:
            self.content_type = value

    @rx.event
    def increment_question_count(self, q_type: str):
        if q_type not in self.question_counts:
            return
        updated_counts = dict(self.question_counts)
        updated_counts[q_type] = min(20, int(updated_counts[q_type]) + 1)
        self.question_counts = updated_counts
        self._set_custom_count_note()

    @rx.event
    def decrement_question_count(self, q_type: str):
        if q_type not in self.question_counts:
            return
        updated_counts = dict(self.question_counts)
        updated_counts[q_type] = max(0, int(updated_counts[q_type]) - 1)
        self.question_counts = updated_counts
        self._set_custom_count_note()

    @rx.event
    def set_special_instructions(self, value: str):
        """Set special instructions with length guard."""
        limited, truncated = enforce_text_limit(value, MAX_LONG_TEXT_CHARS)
        self.special_instructions = limited
        if truncated:
            self.error_message = self._SPECIAL_INSTRUCTIONS_LIMIT_ERROR
            return
        if self.error_message == self._SPECIAL_INSTRUCTIONS_LIMIT_ERROR:
            self.error_message = ""

    @rx.event
    def set_question_count(self, q_type: str, count_str: str):
        try:
            count = int(count_str)
            if 0 <= count <= 20:
                updated_counts = dict(self.question_counts)
                updated_counts[q_type] = count
                self.question_counts = updated_counts
            self._set_custom_count_note()
        except (ValueError, TypeError) as e:
            logging.exception(f"Error setting question count: {e}")

    @rx.event
    def set_assessment_type(self, value: str):
        """Set assessment type and load its default cognitive mix."""
        self.assessment_type = value
        profile = get_assessment_profile(value)
        self.cognitive_distribution = profile["cognitive_distribution"]
        if value == "Formative":
            self.v2_active_preset = "Formative"
        elif value == "Summative":
            self.v2_active_preset = "Summative"
        elif value == "Practice" and self.v2_active_preset not in {"Quick Check", "Homework"}:
            self.v2_active_preset = "Quick Check"
        self.profile_note = (
            f"{value} profile selected. Click 'Apply Profile Preset' to use its "
            "recommended question-type distribution."
        )

    @rx.event
    def set_selected_subject(self, value: str):
        self.selected_subject = value

    @rx.event
    def set_assessment_title(self, value: str):
        self.assessment_title = value

    @rx.event
    def set_content_type(self, value: str):
        if value in {"rm_q", "sld_q", "siml_q"}:
            self.content_type = value

    @rx.event
    def apply_assessment_profile(self):
        """Apply default question distribution based on assessment type."""
        self._apply_profile(self.assessment_type)
        self.profile_note = (
            f"Applied {self.assessment_type} profile preset. "
            f"Cognitive mix: {self.cognitive_distribution_summary}."
        )

    @rx.event
    def download_text_package(self) -> rx.download:
        """Download text-only QTI package."""
        try:
            from app.utils.combined_questions import create_package_with_warnings
            from datetime import datetime

            if not self.xml_questions:
                logging.warning("No questions available to download")
                return rx.toast.error("No questions available to download")

            package_bytes, package_warnings = create_package_with_warnings(
                test_title="TeacherAIde Text Questions",
                questions=self.xml_questions,
                media_files=None,
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
                filename = f"text_questions_{timestamp}.zip"
                return rx.download(data=package_bytes, filename=filename)
            else:
                logging.error("Failed to create QTI package")
                return rx.toast.error("Failed to create package")

        except Exception as e:
            logging.exception(f"Error creating text package download: {e}")
            return rx.toast.error(f"Error: {str(e)}")

    @rx.event
    async def handle_generate(self):
        material_state = await self.get_state(MaterialState)
        settings_state = await self.get_state(SettingsState)
        self.generation_stage = "Validating"
        self.progress = progress_for_stage("Validating")
        await self._refresh_preflight(settings_state, material_state)

        if len(self.special_instructions or "") > MAX_LONG_TEXT_CHARS:
            self.error_message = self._SPECIAL_INSTRUCTIONS_LIMIT_ERROR
            self.generation_stage = "Failed"
            return

        if not material_state.extracted_pdf_name:
            self.error_message = (
                "No extracted PDF found. Go to Upload Material and extract a PDF first."
            )
            self.generation_stage = "Failed"
            return
        total = self.calculated_total_questions
        if self.workflow_mode != "convert_pdf_questions" and total == 0:
            self.error_message = "Please select at least one question to generate."
            self.generation_stage = "Failed"
            return
        effective_total = 1 if self.workflow_mode == "convert_pdf_questions" else total
        self.generating = True
        self.total_questions = effective_total
        self.error_message = ""
        self.package_ready = False
        self.question_summary = []
        self.conversion_warning_count = 0
        self.conversion_warning_message = ""
        self.current_yaml = ""
        self.xml_questions = []
        yield

        try:
            # Determine model from page-level quick switch, then Settings default.
            model = self.active_model.strip()
            if not model:
                model = self._resolve_default_model(settings_state)
                self.active_model = model
                self.default_model_snapshot = model

            if not model:
                self.error_message = (
                    "No model configured. Select a model here or in Settings."
                )
                self.generating = False
                self.generation_stage = "Failed"
                return

            if self.persist_model_choice and settings_state.text_questions_model != model:
                settings_state.set_text_questions_model(model)
                self.default_model_snapshot = model

            # Validate PDF support for the selected model
            supported, error_msg = validate_model_support(model, "pdf")
            if not supported:
                self.error_message = error_msg
                self.generating = False
                self.generation_stage = "Failed"
                return

            # Get API key for the provider
            provider = get_provider(model)
            api_key = self._resolve_api_key(provider, settings_state)

            if not api_key:
                self.error_message = f"API key not configured for {provider}. Open Settings and add the key."
                self.generating = False
                self.generation_stage = "Failed"
                return

            self.generation_stage = "Preparing"
            self.progress = progress_for_stage("Preparing")
            yield
            upload_dir = rx.get_upload_dir()
            pdf_path = upload_dir / material_state.extracted_pdf_name
            with pdf_path.open("rb") as f:
                pdf_bytes = f.read()
            compressed_pdf = compress_pdf(pdf_bytes)
            pdf_b64 = base64.b64encode(compressed_pdf).decode("utf-8")
            if self.workflow_mode == "convert_pdf_questions":
                prompt = create_pdf_question_conversion_prompt(self.special_instructions)
            else:
                prompt = build_prompt(
                    self.content_type,
                    self.assessment_type,
                    self.question_counts,
                    self.special_instructions,
                    self.cognitive_distribution,
                )

            self.generation_stage = "Generating"
            self.progress = progress_for_stage("Generating")
            yield
            async for update in generate_questions_unified(
                pdf_b64=pdf_b64,
                prompt=prompt,
                total=self.total_questions,
                model=model,
                api_key=api_key,
                thinking_enabled=settings_state.enable_thinking,
                thinking_budget=settings_state.thinking_budget,
                reasoning_effort=settings_state.reasoning_effort
            ):
                self.current_yaml = update["yaml"]
                yield

            self.generation_stage = "Parsing"
            self.progress = progress_for_stage("Parsing")
            yield
            valid, msg, questions_data = validate_yaml(self.current_yaml)
            if not valid:
                repaired_yaml = fix_yaml_format(self.current_yaml)
                valid, msg, questions_data = validate_yaml(repaired_yaml)
                if valid:
                    self.current_yaml = repaired_yaml
                else:
                    self.error_message = f"YAML validation failed after repair attempt: {msg}."
                    self.generating = False
                    self.generation_stage = "Failed"
                    return

            # Convert YAML to QTI XML using the real converter
            self.xml_questions, conversion_warnings = yaml_to_qti_xml_with_warnings(
                self.current_yaml
            )
            if not self.xml_questions:
                repaired_yaml = fix_yaml_format(self.current_yaml)
                if repaired_yaml != self.current_yaml:
                    self.current_yaml = repaired_yaml
                    repaired_xml, repaired_warnings = yaml_to_qti_xml_with_warnings(
                        self.current_yaml
                    )
                    self.xml_questions = repaired_xml
                    conversion_warnings.extend(repaired_warnings)
            self._set_conversion_warnings(
                len(questions_data),
                len(self.xml_questions),
                conversion_warnings,
            )

            quality_ok, quality_msg = self._quality_gate_xml(self.xml_questions)
            if not quality_ok:
                self.error_message = f"Quality check failed: {quality_msg}"
                self.generating = False
                self.generation_stage = "Failed"
                return

            self.generation_stage = "Packaging"
            self.progress = progress_for_stage("Packaging")
            yield
            summary_counts = {}
            for xml_q in self.xml_questions:
                q_type = self._parse_qti_xml(xml_q)
                summary_counts[q_type] = summary_counts.get(q_type, 0) + 1
            self.question_summary = [
                {"type": q_type, "count": count}
                for q_type, count in summary_counts.items()
            ]

            # Note: ReviewState.on_load will pull questions from here when the review page loads

            self.package_ready = True
            self.generation_stage = "Ready"
            self.progress = progress_for_stage("Ready")

            # Save to localStorage for cross-tab access
            yield TextQuestionsState.save_to_local_storage
        except Exception as e:
            logging.exception(f"Error during question generation: {e}")
            self.error_message = f"An unexpected error occurred: {str(e)}"
            self.generation_stage = "Failed"
        finally:
            self.generating = False

    @rx.event
    def toggle_model_picker(self):
        """Toggle the inline model picker visibility."""
        self.model_picker_open = not self.model_picker_open

    @rx.event
    def open_delete_package_modal(self):
        """Open delete confirmation modal for text package."""
        self.delete_package_modal_open = True

    @rx.event
    def close_delete_package_modal(self):
        """Close delete modal without deleting."""
        self.delete_package_modal_open = False

    @rx.event
    def confirm_delete_package(self):
        """Delete all text questions and clear localStorage."""
        self.current_yaml = ""
        self.xml_questions = []
        self.question_summary = []
        self.package_ready = False
        self.progress = 0
        self.error_message = ""
        self.delete_package_modal_open = False
        # Clear localStorage for cross-tab consistency
        return rx.call_script(get_clear_text_questions_script())

    @rx.event
    def save_to_local_storage(self):
        """Save generated questions to localStorage for cross-tab access."""
        if self.xml_questions:
            questions_json = json.dumps(self.xml_questions)
            return rx.call_script(get_save_text_questions_script(questions_json))

    @rx.event
    def clear_local_storage(self):
        """Clear text questions from localStorage."""
        return rx.call_script(get_clear_text_questions_script())
