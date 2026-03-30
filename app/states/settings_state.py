import json
import logging
from pathlib import Path
import reflex as rx
from typing import List
from app.utils.model_catalog import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_ANTHROPIC_MODELS,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GEMINI_MODELS,
    DEFAULT_GEMINI_SLIDE_DECK_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_OPENAI_MODELS,
    DEFAULT_OPENAI_REASONING_EFFORT,
    OPENAI_REASONING_EFFORT_OPTIONS,
    PROVIDER_MODEL_CATALOG_REVISION,
    canonicalize_model,
    validate_model_support,
)
from app.utils.secure_storage import (
    API_KEY_FIELDS,
    load_api_keys,
    save_api_keys,
)


class SettingsState(rx.State):
    """State for managing API keys, model selection, and function assignments."""

    # API Keys (stored in secure OS keyring when available)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    # Selected models for each provider
    selected_openai_model: str = DEFAULT_OPENAI_MODEL
    selected_anthropic_model: str = DEFAULT_ANTHROPIC_MODEL
    selected_gemini_model: str = DEFAULT_GEMINI_MODEL

    # Available models for each provider
    openai_models: List[str] = list(DEFAULT_OPENAI_MODELS)
    anthropic_models: List[str] = list(DEFAULT_ANTHROPIC_MODELS)
    gemini_models: List[str] = list(DEFAULT_GEMINI_MODELS)
    new_openai_model_input: str = ""
    new_anthropic_model_input: str = ""
    new_gemini_model_input: str = ""

    # Custom models management
    custom_models: List[str] = []
    new_model_input: str = ""

    # Function assignments
    reading_material_model: str = ""
    reading_material_with_image_model: str = ""
    slide_deck_model: str = ""
    text_questions_model: str = ""
    image_questions_model: str = ""
    student_remediation_model: str = ""

    # Thinking/Reasoning settings
    enable_thinking: bool = True
    thinking_budget: int = 10000
    reasoning_effort: str = DEFAULT_OPENAI_REASONING_EFFORT
    reasoning_effort_options: List[str] = list(OPENAI_REASONING_EFFORT_OPTIONS)

    # UI state
    show_openai_key: bool = False
    show_anthropic_key: bool = False
    show_gemini_key: bool = False
    settings_loaded: bool = False
    settings_status: str = ""
    settings_file_path: str = ".teacheraide_settings.json"

    @rx.var
    def all_available_models(self) -> List[str]:
        """Returns all available models from all providers plus custom models."""
        return (
            self.openai_models
            + self.anthropic_models
            + self.gemini_models
            + self.custom_models
        )

    @rx.var
    def masked_openai_key(self) -> str:
        """Returns masked version of OpenAI API key."""
        if not self.openai_api_key:
            return ""
        if len(self.openai_api_key) <= 8:
            return "*" * len(self.openai_api_key)
        return self.openai_api_key[:4] + "*" * (len(self.openai_api_key) - 8) + self.openai_api_key[-4:]

    @rx.var
    def masked_anthropic_key(self) -> str:
        """Returns masked version of Anthropic API key."""
        if not self.anthropic_api_key:
            return ""
        if len(self.anthropic_api_key) <= 8:
            return "*" * len(self.anthropic_api_key)
        return self.anthropic_api_key[:4] + "*" * (len(self.anthropic_api_key) - 8) + self.anthropic_api_key[-4:]

    @rx.var
    def masked_gemini_key(self) -> str:
        """Returns masked version of Gemini API key."""
        if not self.gemini_api_key:
            return ""
        if len(self.gemini_api_key) <= 8:
            return "*" * len(self.gemini_api_key)
        return self.gemini_api_key[:4] + "*" * (len(self.gemini_api_key) - 8) + self.gemini_api_key[-4:]

    def toggle_openai_key_visibility(self):
        """Toggle OpenAI API key visibility."""
        self.show_openai_key = not self.show_openai_key

    def toggle_anthropic_key_visibility(self):
        """Toggle Anthropic API key visibility."""
        self.show_anthropic_key = not self.show_anthropic_key

    def toggle_gemini_key_visibility(self):
        """Toggle Gemini API key visibility."""
        self.show_gemini_key = not self.show_gemini_key

    def set_openai_api_key(self, value: str):
        """Set OpenAI API key."""
        self.openai_api_key = value
        self._save_settings_to_disk()

    def set_anthropic_api_key(self, value: str):
        """Set Anthropic API key."""
        self.anthropic_api_key = value
        self._save_settings_to_disk()

    def set_gemini_api_key(self, value: str):
        """Set Gemini API key."""
        self.gemini_api_key = value
        self._save_settings_to_disk()

    def set_selected_openai_model(self, value: str):
        """Set selected OpenAI model."""
        model_name = canonicalize_model(value)
        if model_name in self.openai_models:
            self.selected_openai_model = model_name
            self._save_settings_to_disk()

    def set_selected_anthropic_model(self, value: str):
        """Set selected Anthropic model."""
        model_name = canonicalize_model(value)
        if model_name in self.anthropic_models:
            self.selected_anthropic_model = model_name
            self._save_settings_to_disk()

    def set_selected_gemini_model(self, value: str):
        """Set selected Gemini model."""
        model_name = canonicalize_model(value)
        if model_name in self.gemini_models:
            self.selected_gemini_model = model_name
            self._save_settings_to_disk()

    def set_new_openai_model_input(self, value: str):
        self.new_openai_model_input = value

    def set_new_anthropic_model_input(self, value: str):
        self.new_anthropic_model_input = value

    def set_new_gemini_model_input(self, value: str):
        self.new_gemini_model_input = value

    def add_openai_model(self):
        model_name = canonicalize_model(self.new_openai_model_input.strip())
        if not model_name or model_name in self.openai_models:
            return
        self.openai_models = self.openai_models + [model_name]
        if not self.selected_openai_model:
            self.selected_openai_model = model_name
        self.new_openai_model_input = ""
        self._save_settings_to_disk()

    def add_anthropic_model(self):
        model_name = canonicalize_model(self.new_anthropic_model_input.strip())
        if not model_name or model_name in self.anthropic_models:
            return
        self.anthropic_models = self.anthropic_models + [model_name]
        if not self.selected_anthropic_model:
            self.selected_anthropic_model = model_name
        self.new_anthropic_model_input = ""
        self._save_settings_to_disk()

    def add_gemini_model(self):
        model_name = canonicalize_model(self.new_gemini_model_input.strip())
        if not model_name or model_name in self.gemini_models:
            return
        self.gemini_models = self.gemini_models + [model_name]
        if not self.selected_gemini_model:
            self.selected_gemini_model = model_name
        self.new_gemini_model_input = ""
        self._save_settings_to_disk()

    def remove_openai_model(self, model_name: str):
        model_name = canonicalize_model(model_name)
        if model_name not in self.openai_models:
            return
        self.openai_models = [m for m in self.openai_models if m != model_name]
        if self.selected_openai_model == model_name:
            self.selected_openai_model = self.openai_models[0] if self.openai_models else ""
        if self.reading_material_model == model_name:
            self.reading_material_model = ""
        if self.reading_material_with_image_model == model_name:
            self.reading_material_with_image_model = ""
        if self.slide_deck_model == model_name:
            self.slide_deck_model = ""
        if self.text_questions_model == model_name:
            self.text_questions_model = ""
        if self.image_questions_model == model_name:
            self.image_questions_model = ""
        if self.student_remediation_model == model_name:
            self.student_remediation_model = ""
        self._save_settings_to_disk()

    def remove_anthropic_model(self, model_name: str):
        model_name = canonicalize_model(model_name)
        if model_name not in self.anthropic_models:
            return
        self.anthropic_models = [m for m in self.anthropic_models if m != model_name]
        if self.selected_anthropic_model == model_name:
            self.selected_anthropic_model = (
                self.anthropic_models[0] if self.anthropic_models else ""
            )
        if self.reading_material_model == model_name:
            self.reading_material_model = ""
        if self.reading_material_with_image_model == model_name:
            self.reading_material_with_image_model = ""
        if self.slide_deck_model == model_name:
            self.slide_deck_model = ""
        if self.text_questions_model == model_name:
            self.text_questions_model = ""
        if self.image_questions_model == model_name:
            self.image_questions_model = ""
        if self.student_remediation_model == model_name:
            self.student_remediation_model = ""
        self._save_settings_to_disk()

    def remove_gemini_model(self, model_name: str):
        model_name = canonicalize_model(model_name)
        if model_name not in self.gemini_models:
            return
        self.gemini_models = [m for m in self.gemini_models if m != model_name]
        if self.selected_gemini_model == model_name:
            self.selected_gemini_model = self.gemini_models[0] if self.gemini_models else ""
        if self.reading_material_model == model_name:
            self.reading_material_model = ""
        if self.reading_material_with_image_model == model_name:
            self.reading_material_with_image_model = ""
        if self.slide_deck_model == model_name:
            self.slide_deck_model = ""
        if self.text_questions_model == model_name:
            self.text_questions_model = ""
        if self.image_questions_model == model_name:
            self.image_questions_model = ""
        if self.student_remediation_model == model_name:
            self.student_remediation_model = ""
        self._save_settings_to_disk()

    def set_new_model_input(self, value: str):
        """Set the new model name input."""
        self.new_model_input = value

    def add_custom_model(self):
        """Add a new custom model."""
        if self.new_model_input.strip() and self.new_model_input.strip() not in self.custom_models:
            self.custom_models = self.custom_models + [self.new_model_input.strip()]
            self.new_model_input = ""
            self._save_settings_to_disk()

    def remove_custom_model(self, model_name: str):
        """Remove a custom model."""
        self.custom_models = [m for m in self.custom_models if m != model_name]
        # Clear function assignments if they used this model
        if self.reading_material_model == model_name:
            self.reading_material_model = ""
        if self.reading_material_with_image_model == model_name:
            self.reading_material_with_image_model = ""
        if self.slide_deck_model == model_name:
            self.slide_deck_model = ""
        if self.text_questions_model == model_name:
            self.text_questions_model = ""
        if self.image_questions_model == model_name:
            self.image_questions_model = ""
        if self.student_remediation_model == model_name:
            self.student_remediation_model = ""
        self._save_settings_to_disk()

    def set_reading_material_model(self, value: str):
        """Set model for generating reading material without image."""
        self.reading_material_model = canonicalize_model(value)
        self._save_settings_to_disk()

    def set_reading_material_with_image_model(self, value: str):
        """Set model for generating reading material with image."""
        self.reading_material_with_image_model = canonicalize_model(value)
        self._save_settings_to_disk()

    def set_slide_deck_model(self, value: str):
        """Set model for generating illustrated slide decks."""
        self.slide_deck_model = canonicalize_model(value)
        self._save_settings_to_disk()

    def set_text_questions_model(self, value: str):
        """Set model for generating text-only questions."""
        self.text_questions_model = canonicalize_model(value)
        self._save_settings_to_disk()

    def set_image_questions_model(self, value: str):
        """Set model for generating image-based questions."""
        self.image_questions_model = canonicalize_model(value)
        self._save_settings_to_disk()

    def set_student_remediation_model(self, value: str):
        """Set model for student remediation generation."""
        self.student_remediation_model = canonicalize_model(value)
        self._save_settings_to_disk()

    def _fallback_selected_model(self) -> str:
        """Choose a reasonable selected model fallback when no assignment exists."""
        if self.openai_api_key and self.selected_openai_model:
            return self.selected_openai_model
        if self.anthropic_api_key and self.selected_anthropic_model:
            return self.selected_anthropic_model
        if self.gemini_api_key and self.selected_gemini_model:
            return self.selected_gemini_model

        # If no key is configured yet, keep a deterministic default.
        if self.selected_openai_model:
            return self.selected_openai_model
        if self.selected_anthropic_model:
            return self.selected_anthropic_model
        if self.selected_gemini_model:
            return self.selected_gemini_model
        return ""

    def get_default_text_questions_model(self) -> str:
        """Resolve default model for text questions action page."""
        if self.text_questions_model:
            return self.text_questions_model
        return self._fallback_selected_model()

    def get_default_image_questions_model(self) -> str:
        """Resolve default model for image questions action page."""
        if self.image_questions_model:
            return self.image_questions_model
        return self._fallback_selected_model()

    def get_default_reading_material_model(self) -> str:
        """Resolve default model for reading material without image."""
        if self.reading_material_model:
            return self.reading_material_model
        return self._fallback_selected_model()

    def get_default_reading_material_with_image_model(self) -> str:
        """Resolve default model for reading material when image context is used."""
        if self.reading_material_with_image_model:
            return self.reading_material_with_image_model
        return self._fallback_selected_model()

    def get_default_slide_deck_model(self) -> str:
        """Resolve default model for slide decks with generated illustrations."""
        if self.slide_deck_model:
            return self.slide_deck_model
        if self.selected_gemini_model and validate_model_support(
            self.selected_gemini_model,
            "generated_image_output",
        )[0]:
            return self.selected_gemini_model
        for model_name in self.gemini_models:
            if validate_model_support(model_name, "generated_image_output")[0]:
                return model_name
        return DEFAULT_GEMINI_SLIDE_DECK_MODEL

    def get_default_student_remediation_model(self) -> str:
        """Resolve default model for student remediation generation."""
        if self.student_remediation_model:
            return self.student_remediation_model
        return self._fallback_selected_model()

    def set_enable_thinking(self, value: bool):
        """Toggle extended thinking mode."""
        self.enable_thinking = value
        self._save_settings_to_disk()

    def toggle_thinking(self):
        """Toggle extended thinking mode."""
        self.enable_thinking = not self.enable_thinking
        self._save_settings_to_disk()

    def set_thinking_budget(self, value: str | float | int):
        """Set thinking budget tokens (1024-32768)."""
        try:
            budget = int(float(value))
            self.thinking_budget = max(1024, min(32768, budget))
            self._save_settings_to_disk()
        except (ValueError, TypeError):
            pass

    def set_reasoning_effort(self, value: str):
        """Set OpenAI reasoning effort level."""
        if value in self.reasoning_effort_options:
            self.reasoning_effort = value
            self._save_settings_to_disk()

    def _settings_file(self) -> Path:
        return Path(self.settings_file_path)

    def _api_keys_payload(self) -> dict[str, str]:
        return {
            "openai_api_key": self.openai_api_key,
            "anthropic_api_key": self.anthropic_api_key,
            "gemini_api_key": self.gemini_api_key,
        }

    def _set_api_keys_from_payload(self, payload: dict[str, str]):
        self.openai_api_key = str(payload.get("openai_api_key", "") or "")
        self.anthropic_api_key = str(payload.get("anthropic_api_key", "") or "")
        self.gemini_api_key = str(payload.get("gemini_api_key", "") or "")

    def _extract_legacy_plaintext_keys(self, payload: dict) -> dict[str, str]:
        legacy_keys: dict[str, str] = {}
        for field in API_KEY_FIELDS:
            value = payload.get(field, "")
            if isinstance(value, str) and value:
                legacy_keys[field] = value
        return legacy_keys

    def _serialize_settings(self) -> dict:
        return {
            "provider_model_catalog_revision": PROVIDER_MODEL_CATALOG_REVISION,
            "selected_openai_model": self.selected_openai_model,
            "selected_anthropic_model": self.selected_anthropic_model,
            "selected_gemini_model": self.selected_gemini_model,
            "openai_models": self.openai_models,
            "anthropic_models": self.anthropic_models,
            "gemini_models": self.gemini_models,
            "custom_models": self.custom_models,
            "reading_material_model": self.reading_material_model,
            "reading_material_with_image_model": self.reading_material_with_image_model,
            "slide_deck_model": self.slide_deck_model,
            "text_questions_model": self.text_questions_model,
            "image_questions_model": self.image_questions_model,
            "student_remediation_model": self.student_remediation_model,
            "enable_thinking": self.enable_thinking,
            "thinking_budget": self.thinking_budget,
            "reasoning_effort": self.reasoning_effort,
        }

    def _apply_provider_model_catalog_migration(self, payload: dict) -> bool:
        raw_revision = payload.get("provider_model_catalog_revision", 0)
        try:
            saved_revision = int(raw_revision)
        except (TypeError, ValueError):
            saved_revision = 0

        if saved_revision >= PROVIDER_MODEL_CATALOG_REVISION:
            return False

        self.openai_models = list(DEFAULT_OPENAI_MODELS)
        self.anthropic_models = list(DEFAULT_ANTHROPIC_MODELS)

        if self.selected_openai_model not in self.openai_models:
            self.selected_openai_model = self.openai_models[0] if self.openai_models else ""
        if self.selected_anthropic_model not in self.anthropic_models:
            self.selected_anthropic_model = (
                self.anthropic_models[0] if self.anthropic_models else ""
            )

        return True

    def _apply_settings_payload(self, payload: dict) -> bool:
        def normalize_model_list(values: list) -> List[str]:
            normalized: List[str] = []
            for value in values:
                model_name = canonicalize_model(str(value).strip())
                if model_name and model_name not in normalized:
                    normalized.append(model_name)
            return normalized

        openai_models = payload.get("openai_models")
        if isinstance(openai_models, list):
            self.openai_models = normalize_model_list(openai_models)

        anthropic_models = payload.get("anthropic_models")
        if isinstance(anthropic_models, list):
            self.anthropic_models = normalize_model_list(anthropic_models)

        gemini_models = payload.get("gemini_models")
        if isinstance(gemini_models, list):
            self.gemini_models = normalize_model_list(gemini_models)

        self.selected_openai_model = canonicalize_model(
            payload.get("selected_openai_model", self.selected_openai_model)
        )
        self.selected_anthropic_model = canonicalize_model(
            payload.get("selected_anthropic_model", self.selected_anthropic_model)
        )
        self.selected_gemini_model = canonicalize_model(
            payload.get("selected_gemini_model", self.selected_gemini_model)
        )

        custom_models = payload.get("custom_models", self.custom_models)
        if isinstance(custom_models, list):
            self.custom_models = normalize_model_list(custom_models)

        self.reading_material_model = canonicalize_model(
            payload.get("reading_material_model", self.reading_material_model)
        )
        self.reading_material_with_image_model = canonicalize_model(
            payload.get(
                "reading_material_with_image_model",
                self.reading_material_with_image_model,
            )
        )
        self.slide_deck_model = canonicalize_model(
            payload.get("slide_deck_model", self.slide_deck_model)
        )
        self.text_questions_model = canonicalize_model(
            payload.get("text_questions_model", self.text_questions_model)
        )
        self.image_questions_model = canonicalize_model(
            payload.get("image_questions_model", self.image_questions_model)
        )
        self.student_remediation_model = canonicalize_model(
            payload.get("student_remediation_model", self.student_remediation_model)
        )

        self.enable_thinking = bool(payload.get("enable_thinking", self.enable_thinking))
        self.thinking_budget = int(payload.get("thinking_budget", self.thinking_budget))

        reasoning_effort = str(payload.get("reasoning_effort", self.reasoning_effort))
        if reasoning_effort in self.reasoning_effort_options:
            self.reasoning_effort = reasoning_effort

        provider_catalog_migrated = self._apply_provider_model_catalog_migration(payload)

        if self.selected_openai_model and self.selected_openai_model not in self.openai_models:
            self.selected_openai_model = self.openai_models[0] if self.openai_models else ""
        if self.selected_anthropic_model and self.selected_anthropic_model not in self.anthropic_models:
            self.selected_anthropic_model = (
                self.anthropic_models[0] if self.anthropic_models else ""
            )
        if self.selected_gemini_model and self.selected_gemini_model not in self.gemini_models:
            self.selected_gemini_model = self.gemini_models[0] if self.gemini_models else ""

        available_models = (
            self.openai_models
            + self.anthropic_models
            + self.gemini_models
            + self.custom_models
        )
        if self.reading_material_model and self.reading_material_model not in available_models:
            self.reading_material_model = ""
        if (
            self.reading_material_with_image_model
            and self.reading_material_with_image_model not in available_models
        ):
            self.reading_material_with_image_model = ""
        if self.slide_deck_model and self.slide_deck_model not in available_models:
            self.slide_deck_model = ""
        if self.text_questions_model and self.text_questions_model not in available_models:
            self.text_questions_model = ""
        if self.image_questions_model and self.image_questions_model not in available_models:
            self.image_questions_model = ""
        if (
            self.student_remediation_model
            and self.student_remediation_model not in available_models
        ):
            self.student_remediation_model = ""

        return provider_catalog_migrated

    def _write_settings_file(self):
        settings_file = self._settings_file()
        settings_file.write_text(
            json.dumps(self._serialize_settings(), indent=2),
            encoding="utf-8",
        )

    def load_settings_from_disk(self):
        """Load persisted settings file if present."""
        settings_file = self._settings_file()
        payload: dict = {}
        legacy_plaintext_keys: dict[str, str] = {}
        provider_catalog_migrated = False

        if not settings_file.exists():
            secure_keys, secure_available, secure_warnings = load_api_keys()
            if secure_available:
                self._set_api_keys_from_payload(secure_keys)
            self.settings_loaded = True
            if secure_warnings:
                self.settings_status = "Settings loaded with secure-storage warnings"
            return

        try:
            payload = json.loads(settings_file.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                legacy_plaintext_keys = self._extract_legacy_plaintext_keys(payload)
                provider_catalog_migrated = self._apply_settings_payload(payload)

            secure_keys, secure_available, secure_warnings = load_api_keys()
            secure_warning_messages = list(secure_warnings)

            if secure_available:
                self._set_api_keys_from_payload(secure_keys)

            migrated_from_plaintext = False
            if legacy_plaintext_keys:
                if secure_available:
                    if not self.openai_api_key and legacy_plaintext_keys.get("openai_api_key"):
                        self.openai_api_key = legacy_plaintext_keys["openai_api_key"]
                        migrated_from_plaintext = True
                    if not self.anthropic_api_key and legacy_plaintext_keys.get("anthropic_api_key"):
                        self.anthropic_api_key = legacy_plaintext_keys["anthropic_api_key"]
                        migrated_from_plaintext = True
                    if not self.gemini_api_key and legacy_plaintext_keys.get("gemini_api_key"):
                        self.gemini_api_key = legacy_plaintext_keys["gemini_api_key"]
                        migrated_from_plaintext = True

                    if migrated_from_plaintext:
                        migrated_ok, _secure_available, migrate_warnings = save_api_keys(
                            self._api_keys_payload()
                        )
                        secure_warning_messages.extend(migrate_warnings)
                        if not migrated_ok:
                            secure_warning_messages.append(
                                "Legacy API keys could not be fully migrated to secure storage."
                            )
                else:
                    # Backward compatibility when keyring is unavailable:
                    # allow this session to keep legacy plaintext keys in memory.
                    self.openai_api_key = legacy_plaintext_keys.get("openai_api_key", "")
                    self.anthropic_api_key = legacy_plaintext_keys.get("anthropic_api_key", "")
                    self.gemini_api_key = legacy_plaintext_keys.get("gemini_api_key", "")
                    secure_warning_messages.append(
                        "Secure key storage unavailable; API keys were loaded from legacy plaintext settings for this session only."
                    )

                # Remove legacy plaintext keys from settings file on disk.
                try:
                    self._write_settings_file()
                except Exception as scrub_error:
                    logging.warning(
                        "Failed to scrub legacy plaintext API keys from settings file: %s",
                        str(scrub_error),
                    )
            elif provider_catalog_migrated:
                try:
                    self._write_settings_file()
                except Exception as migration_error:
                    logging.warning(
                        "Failed to persist provider model catalog migration: %s",
                        str(migration_error),
                    )

            self.settings_loaded = True
            if secure_warning_messages:
                self.settings_status = "Settings loaded with secure-storage warnings"
            elif migrated_from_plaintext:
                self.settings_status = "Settings loaded and API keys migrated to secure storage"
            else:
                self.settings_status = "Settings loaded"
        except Exception as e:
            logging.exception(f"Failed to load settings: {e}")
            self.settings_loaded = True
            self.settings_status = "Failed to load settings"

    def _save_settings_to_disk(self):
        """Persist settings to disk."""
        try:
            secure_saved, secure_available, secure_warnings = save_api_keys(
                self._api_keys_payload()
            )
            self._write_settings_file()

            if secure_available and secure_saved and not secure_warnings:
                self.settings_status = "Settings saved"
            elif secure_available:
                self.settings_status = "Settings saved with secure-storage warnings"
            else:
                self.settings_status = (
                    "Settings saved. API keys are session-only until secure storage is available."
                )
        except Exception as e:
            logging.exception(f"Failed to save settings: {e}")
            self.settings_status = "Failed to save settings"

    @rx.event
    def load_settings(self):
        """Load settings on page/app startup."""
        self.load_settings_from_disk()

    @rx.event
    def save_settings(self):
        """Save all settings immediately to disk."""
        self._save_settings_to_disk()
        return rx.toast.success("Settings saved")

    def clear_openai_key(self):
        """Clear OpenAI API key."""
        self.openai_api_key = ""
        self._save_settings_to_disk()

    def clear_anthropic_key(self):
        """Clear Anthropic API key."""
        self.anthropic_api_key = ""
        self._save_settings_to_disk()

    def clear_gemini_key(self):
        """Clear Gemini API key."""
        self.gemini_api_key = ""
        self._save_settings_to_disk()
