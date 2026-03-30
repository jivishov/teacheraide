"""Active Image Questions page backed by the V2 layout."""

import reflex as rx

from app.components.layout_components import nav_menu, page_header
from app.components.model_switch_components import model_chip_group
from app.states.image_questions_state import ImageQuestionsState
from app.states.settings_state import SettingsState


def _upload_handler_for_slot(index: int):
    handlers = [
        ImageQuestionsState.handle_upload_0,
        ImageQuestionsState.handle_upload_1,
        ImageQuestionsState.handle_upload_2,
        ImageQuestionsState.handle_upload_3,
        ImageQuestionsState.handle_upload_4,
        ImageQuestionsState.handle_upload_5,
        ImageQuestionsState.handle_upload_6,
        ImageQuestionsState.handle_upload_7,
        ImageQuestionsState.handle_upload_8,
        ImageQuestionsState.handle_upload_9,
    ]
    return handlers[index](rx.upload_files(upload_id=f"upload_slot_v2_{index}"))


def _batch_upload_handler():
    return ImageQuestionsState.handle_v2_batch_upload(
        rx.upload_files(upload_id="upload_batch_v2")
    )


def _generate_disabled() -> rx.Var[bool]:
    return (
        ImageQuestionsState.generating
        | ~ImageQuestionsState.has_uploaded_images
        | ~ImageQuestionsState.preflight_ready
    )


def image_delete_package_modal_v2() -> rx.Component:
    """Modal for image package delete confirmation."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon("triangle-alert", class_name="h-6 w-6 text-red-600"),
                        class_name="flex items-center justify-center w-12 h-12 rounded-full bg-red-100",
                    ),
                    rx.el.div(
                        rx.dialog.title(
                            "Delete Image Questions",
                            class_name="text-lg font-semibold text-gray-900",
                        ),
                        rx.dialog.description(
                            "Are you sure you want to delete all generated image questions? This action cannot be undone.",
                            class_name="mt-2 text-sm text-gray-500",
                        ),
                        class_name="ml-4",
                    ),
                    class_name="flex items-start",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=ImageQuestionsState.close_delete_package_modal,
                        class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50",
                    ),
                    rx.el.button(
                        "Delete All",
                        on_click=ImageQuestionsState.confirm_delete_package,
                        class_name="ml-3 px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700",
                    ),
                    class_name="mt-6 flex justify-end",
                ),
                class_name="p-6",
            ),
            class_name="max-w-md mx-auto bg-white rounded-lg shadow-xl",
        ),
        open=ImageQuestionsState.delete_package_modal_open,
    )


def _mode_toggle() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            "Quick",
            on_click=ImageQuestionsState.set_v2_ui_mode("quick"),
            class_name=rx.cond(
                ImageQuestionsState.v2_is_quick_mode,
                "px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-l-lg transition-colors",
                "px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-l-lg transition-colors",
            ),
        ),
        rx.el.button(
            "Advanced",
            on_click=ImageQuestionsState.set_v2_ui_mode("advanced"),
            class_name=rx.cond(
                ~ImageQuestionsState.v2_is_quick_mode,
                "px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-r-lg transition-colors",
                "px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-r-lg transition-colors",
            ),
        ),
        class_name="flex h-10",
    )


def _ready_dot_with_label(label: str, status: rx.Var[bool]) -> rx.Component:
    """Show a dot; if red, also show the label text next to it."""
    return rx.el.span(
        rx.el.span(
            class_name=rx.cond(
                status,
                "w-2.5 h-2.5 rounded-full bg-green-500 inline-block cursor-help",
                "w-2.5 h-2.5 rounded-full bg-red-400 inline-block cursor-help",
            ),
            title=label,
        ),
        rx.cond(
            ~status,
            rx.el.span(label, class_name="text-xs text-red-600 ml-1"),
            rx.fragment(),
        ),
        class_name="inline-flex items-center",
    )


def _checklist_item(status: rx.Var[bool], label: str) -> rx.Component:
    return rx.el.div(
        rx.cond(
            status,
            rx.icon("check", class_name="w-4 h-4 text-green-500"),
            rx.icon("x", class_name="w-4 h-4 text-red-400"),
        ),
        rx.el.span(
            label,
            class_name=rx.cond(
                status,
                "text-sm text-gray-700",
                "text-sm text-red-500",
            ),
        ),
        class_name="flex items-center gap-2",
    )


def _action_bar() -> rx.Component:
    disabled = _generate_disabled()
    return rx.el.div(
        # ---- left: model indicator ----
        rx.el.div(
            rx.el.span(
                "Model",
                class_name="text-xs font-medium text-gray-500 uppercase tracking-wider mr-2",
            ),
            rx.el.span(
                ImageQuestionsState.v2_active_model_display,
                class_name="text-xs font-medium text-gray-800 bg-gray-50 px-2 py-1 rounded border border-gray-200",
            ),
            rx.el.button(
                "change",
                on_click=ImageQuestionsState.toggle_model_picker,
                class_name="ml-2 text-xs text-blue-600 hover:text-blue-800 underline underline-offset-2 cursor-pointer",
            ),
            class_name="flex items-center",
        ),
        # ---- center: ready-to-go dots ----
        rx.el.div(
            rx.el.span(
                "Ready to go",
                class_name="text-xs font-medium text-gray-500 uppercase tracking-wider mr-2",
            ),
            rx.el.div(
                _ready_dot_with_label("Images uploaded", ImageQuestionsState.has_uploaded_images),
                _ready_dot_with_label("Model selected", ImageQuestionsState.preflight_model_ready),
                _ready_dot_with_label("API key ready", ImageQuestionsState.preflight_api_key_ready),
                _ready_dot_with_label("Model supports images", ImageQuestionsState.preflight_feature_ready),
                class_name="flex items-center gap-2.5",
            ),
            class_name="flex items-center",
        ),
        # ---- right: generate button ----
        rx.el.button(
            rx.cond(
                ImageQuestionsState.generating,
                rx.el.span(
                    rx.icon("loader-circle", class_name="w-4 h-4 animate-spin mr-2 inline-block"),
                    "Generating...",
                ),
                "Generate Questions",
            ),
            on_click=ImageQuestionsState.handle_generate,
            disabled=disabled,
            class_name=rx.cond(
                ~disabled,
                "py-2.5 px-5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors cursor-pointer",
                "py-2.5 px-5 text-sm font-semibold text-white bg-gray-400 rounded-lg shadow-sm cursor-not-allowed",
            ),
        ),
        class_name="flex items-center justify-between pt-5 mt-5 border-t border-gray-200",
    )


def _inline_model_picker() -> rx.Component:
    """Expandable model chip groups shown when 'change' is clicked."""
    return rx.cond(
        ImageQuestionsState.model_picker_open,
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    rx.cond(
                        ImageQuestionsState.persist_model_choice,
                        "Use as default: On",
                        "Use as default: Off",
                    ),
                    on_click=ImageQuestionsState.toggle_persist_model_choice,
                    type="button",
                    class_name=rx.cond(
                        ImageQuestionsState.persist_model_choice,
                        "px-3 py-1.5 text-xs rounded-md bg-blue-100 text-blue-800 border border-blue-300",
                        "px-3 py-1.5 text-xs rounded-md bg-gray-100 text-gray-700 border border-gray-300",
                    ),
                ),
                rx.el.button(
                    "Reset to default",
                    on_click=ImageQuestionsState.reset_to_default_model,
                    type="button",
                    class_name="px-3 py-1.5 text-xs rounded-md bg-white text-gray-700 border border-gray-300 hover:bg-gray-50",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                model_chip_group(
                    "OpenAI",
                    SettingsState.openai_models,
                    ImageQuestionsState.active_model,
                    ImageQuestionsState.select_active_model,
                ),
                model_chip_group(
                    "Anthropic",
                    SettingsState.anthropic_models,
                    ImageQuestionsState.active_model,
                    ImageQuestionsState.select_active_model,
                ),
                model_chip_group(
                    "Gemini",
                    SettingsState.gemini_models,
                    ImageQuestionsState.active_model,
                    ImageQuestionsState.select_active_model,
                ),
                model_chip_group(
                    "Custom",
                    SettingsState.custom_models,
                    ImageQuestionsState.active_model,
                    ImageQuestionsState.select_active_model,
                ),
                class_name="mt-3 space-y-3",
            ),
            class_name="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200",
        ),
        rx.fragment(),
    )


def _inline_progress() -> rx.Component:
    """Progress bar + stage text shown only when generating."""
    return rx.cond(
        ImageQuestionsState.generating,
        rx.el.div(
            rx.el.div(
                f"{ImageQuestionsState.progress}%",
                class_name="text-xs font-medium text-blue-700 mb-1",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="bg-blue-600 h-2 rounded-full transition-all",
                    style={"width": ImageQuestionsState.progress.to(str) + "%"},
                ),
                class_name="w-full bg-gray-200 rounded-full h-2 overflow-hidden",
            ),
            rx.el.p(
                ImageQuestionsState.generation_stage,
                class_name="text-xs text-gray-500 mt-1",
            ),
            class_name="mt-3",
        ),
        rx.fragment(),
    )


def _assessment_preset_chip(label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=ImageQuestionsState.apply_v2_preset(label),
        class_name=rx.cond(
            ImageQuestionsState.v2_active_preset == label,
            "px-3 py-1.5 text-sm font-semibold text-white bg-blue-600 border border-blue-600 rounded-full shadow-sm transition-colors",
            "px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-full hover:bg-blue-100 transition-colors",
        ),
    )


def _controls_panel() -> rx.Component:
    """Unified three-zone controls panel with vertical dividers."""
    return rx.el.div(
        rx.upload.root(
            rx.el.div(
                rx.icon("image-plus", class_name="w-5 h-5 text-blue-400 flex-shrink-0"),
                rx.el.div(
                    rx.el.p(
                        "Drop images or click to browse",
                        class_name="text-sm font-medium text-gray-700",
                    ),
                    rx.el.p(
                        "JPG, PNG \u00b7 max 10 images",
                        class_name="text-xs text-gray-400 mt-0.5",
                    ),
                ),
                class_name="flex items-center gap-3",
            ),
            id="upload_batch_v2",
            accept={"image/*": [".jpg", ".jpeg", ".png"]},
            max_files=10,
            on_drop=_batch_upload_handler(),
            class_name="flex-1 flex items-center px-5 py-4 bg-gray-50 hover:bg-blue-50 cursor-pointer transition-colors",
        ),
        rx.el.div(class_name="w-px self-stretch bg-gray-200"),
        rx.el.div(
            rx.el.label(
                "Question Type",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-2",
            ),
            rx.el.select(
                rx.el.option("Multiple choice", value="Multiple choice"),
                rx.el.option("True/False", value="True/False"),
                rx.el.option("Fill in blank", value="Fill in blank"),
                rx.el.option("Matching", value="Matching"),
                value=ImageQuestionsState.v2_batch_question_type,
                on_change=ImageQuestionsState.set_v2_batch_question_type,
                class_name="px-3 py-1.5 bg-white text-gray-900 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500",
            ),
            class_name="flex-shrink-0 flex flex-col justify-center px-5 py-4",
        ),
        rx.el.div(class_name="w-px self-stretch bg-gray-200"),
        rx.el.div(
            rx.el.label(
                "Assessment Type",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-2",
            ),
            rx.el.div(
                _assessment_preset_chip("Formative"),
                _assessment_preset_chip("Summative"),
                _assessment_preset_chip("Quick Check"),
                _assessment_preset_chip("Homework"),
                class_name="flex flex-wrap gap-1.5",
            ),
            class_name="flex-shrink-0 flex flex-col justify-center px-5 py-4",
        ),
        class_name="flex items-stretch border border-gray-200 rounded-lg overflow-hidden",
    )


def _simple_file_row(index: int) -> rx.Component:
    has_image = (index < ImageQuestionsState.uploaded_images.length()) & (
        ImageQuestionsState.uploaded_images[index] != ""
    )
    filename = rx.cond(
        has_image,
        ImageQuestionsState.uploaded_images[index],
        "(empty slot)",
    )

    return rx.el.div(
        rx.el.span(
            class_name=rx.cond(
                has_image,
                "w-2.5 h-2.5 rounded-full bg-green-500 flex-shrink-0",
                "w-2.5 h-2.5 rounded-full bg-gray-300 flex-shrink-0",
            ),
        ),
        rx.el.span(
            filename,
            class_name=rx.cond(
                has_image,
                "text-sm text-gray-900 truncate flex-1",
                "text-sm text-gray-400 italic truncate flex-1",
            ),
        ),
        rx.upload.root(
            rx.el.button(
                "Replace",
                class_name="px-2 py-1 text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100",
            ),
            id=f"upload_slot_v2_{index}",
            accept={"image/*": [".jpg", ".jpeg", ".png"]},
            max_files=1,
            on_drop=_upload_handler_for_slot(index),
        ),
        rx.el.button(
            rx.icon("x", class_name="w-3.5 h-3.5"),
            on_click=ImageQuestionsState.remove_v2_slot(index),
            class_name="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded flex-shrink-0",
        ),
        class_name="flex items-center gap-3 py-2 px-3 hover:bg-gray-50 rounded transition-colors",
    )


def _simple_file_list() -> rx.Component:
    return rx.el.div(
        rx.cond(ImageQuestionsState.v2_total_slots >= 1, _simple_file_row(0), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 2, _simple_file_row(1), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 3, _simple_file_row(2), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 4, _simple_file_row(3), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 5, _simple_file_row(4), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 6, _simple_file_row(5), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 7, _simple_file_row(6), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 8, _simple_file_row(7), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 9, _simple_file_row(8), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 10, _simple_file_row(9), rx.fragment()),
        class_name="border border-gray-200 rounded-lg divide-y divide-gray-100 bg-white",
    )


def _table_header() -> rx.Component:
    return rx.el.div(
        rx.el.span("#", class_name="w-8 text-xs font-semibold text-gray-500 text-center"),
        rx.el.span("Preview", class_name="w-14 text-xs font-semibold text-gray-500 text-center"),
        rx.el.span("Filename", class_name="flex-1 text-xs font-semibold text-gray-500"),
        rx.el.span("Type", class_name="w-36 text-xs font-semibold text-gray-500"),
        rx.el.span("Status", class_name="w-24 text-xs font-semibold text-gray-500 text-center"),
        rx.el.span("", class_name="w-28"),
        class_name="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-t-lg border border-gray-200 border-b-0",
    )


def _table_row(index: int) -> rx.Component:
    has_image = (index < ImageQuestionsState.uploaded_images.length()) & (
        ImageQuestionsState.uploaded_images[index] != ""
    )
    is_expanded = ImageQuestionsState.v2_expanded_slot == index
    filename = rx.cond(
        has_image,
        ImageQuestionsState.uploaded_images[index],
        "(no image)",
    )

    return rx.el.div(
        rx.el.div(
            rx.el.span(
                f"{index + 1}",
                class_name="w-8 text-sm font-medium text-gray-700 text-center",
            ),
            rx.el.div(
                rx.cond(
                    has_image,
                    rx.el.div(
                        rx.icon("image", class_name="w-5 h-5 text-blue-500"),
                        class_name="w-10 h-10 flex items-center justify-center bg-blue-50 rounded",
                    ),
                    rx.el.div(
                        rx.icon("image-off", class_name="w-5 h-5 text-gray-300"),
                        class_name="w-10 h-10 flex items-center justify-center bg-gray-50 rounded",
                    ),
                ),
                class_name="w-14 flex justify-center",
            ),
            rx.el.span(
                filename,
                class_name=rx.cond(
                    has_image,
                    "flex-1 text-sm text-gray-900 truncate",
                    "flex-1 text-sm text-gray-400 italic truncate",
                ),
            ),
            rx.el.select(
                rx.el.option("Multiple choice", value="Multiple choice"),
                rx.el.option("True/False", value="True/False"),
                rx.el.option("Fill in blank", value="Fill in blank"),
                rx.el.option("Matching", value="Matching"),
                value=rx.cond(
                    index < ImageQuestionsState.question_types.length(),
                    ImageQuestionsState.question_types[index],
                    ImageQuestionsState.v2_batch_question_type,
                ),
                on_change=lambda value, i=index: ImageQuestionsState.set_question_type_at_index(i, value),
                class_name="w-36 px-2 py-1 bg-white text-gray-900 border border-gray-300 rounded text-sm focus:ring-blue-500 focus:border-blue-500",
            ),
            rx.el.div(
                rx.icon(
                    rx.cond(has_image, "check", "clock"),
                    class_name="w-3.5 h-3.5 mr-1",
                ),
                rx.el.span(
                    rx.cond(has_image, "Ready", "Awaiting"),
                    class_name="text-xs font-medium",
                ),
                class_name=rx.cond(
                    has_image,
                    "w-24 flex items-center justify-center px-2 py-1 rounded-full text-green-700 bg-green-50 text-xs",
                    "w-24 flex items-center justify-center px-2 py-1 rounded-full text-gray-500 bg-gray-50 text-xs",
                ),
            ),
            rx.el.div(
                rx.upload.root(
                    rx.el.button(
                        "Replace",
                        class_name="px-2 py-1 text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100",
                    ),
                    id=f"upload_slot_v2_{index}",
                    accept={"image/*": [".jpg", ".jpeg", ".png"]},
                    max_files=1,
                    on_drop=_upload_handler_for_slot(index),
                ),
                rx.el.button(
                    rx.icon(
                        rx.cond(is_expanded, "chevron-up", "chevron-down"),
                        class_name="w-4 h-4",
                    ),
                    on_click=ImageQuestionsState.toggle_v2_slot(index),
                    class_name="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded",
                ),
                rx.el.button(
                    rx.icon("x", class_name="w-4 h-4"),
                    on_click=ImageQuestionsState.remove_v2_slot(index),
                    class_name="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded",
                ),
                class_name="w-28 flex items-center justify-end gap-1",
            ),
            class_name="flex items-center gap-2 px-3 py-2.5 hover:bg-gray-50 transition-colors",
        ),
        rx.cond(
            is_expanded,
            rx.el.div(
                rx.el.label(
                    "Prompt", class_name="text-sm font-medium text-gray-700 block mb-1"
                ),
                rx.el.textarea(
                    placeholder="Describe what to focus on in this image...",
                    value=rx.cond(
                        index < ImageQuestionsState.image_prompts.length(),
                        ImageQuestionsState.image_prompts[index],
                        "",
                    ),
                    on_change=lambda value, i=index: ImageQuestionsState.set_prompt_at_index(i, value),
                    rows="3",
                    class_name="w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
                ),
                class_name="px-3 py-3 bg-blue-50/30 border-t border-gray-100",
            ),
            rx.fragment(),
        ),
        class_name="border-x border-b border-gray-200 last:rounded-b-lg",
    )


def _add_slot_button() -> rx.Component:
    return rx.el.button(
        rx.icon("plus", class_name="w-4 h-4 mr-1.5"),
        "Add Image Slot",
        on_click=ImageQuestionsState.add_v2_slot,
        class_name="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors mt-3",
    )


def _full_image_table() -> rx.Component:
    return rx.el.div(
        _table_header(),
        rx.cond(ImageQuestionsState.v2_total_slots >= 1, _table_row(0), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 2, _table_row(1), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 3, _table_row(2), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 4, _table_row(3), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 5, _table_row(4), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 6, _table_row(5), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 7, _table_row(6), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 8, _table_row(7), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 9, _table_row(8), rx.fragment()),
        rx.cond(ImageQuestionsState.v2_total_slots >= 10, _table_row(9), rx.fragment()),
        _add_slot_button(),
    )


def _quick_mode_content() -> rx.Component:
    return rx.el.div(
        _controls_panel(),
        rx.el.div(
            rx.el.label(
                "Uploaded Images", class_name="text-sm font-medium text-gray-700 block mb-2"
            ),
            _simple_file_list(),
            _add_slot_button(),
            class_name="mt-4",
        ),
        rx.el.div(
            rx.el.label(
                "Special Instructions", class_name="text-sm font-medium text-gray-700"
            ),
            rx.el.textarea(
                placeholder="e.g., Focus on labeling the diagram parts.",
                value=ImageQuestionsState.v2_special_instructions,
                on_change=ImageQuestionsState.set_v2_special_instructions,
                rows="2",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
            class_name="mt-4",
        ),
    )


def _advanced_mode_content() -> rx.Component:
    return rx.el.div(
        _controls_panel(),
        rx.el.div(
            _full_image_table(),
            class_name="mt-4",
        ),
        rx.el.div(
            rx.el.label(
                "Special Instructions", class_name="text-sm font-medium text-gray-700"
            ),
            rx.el.textarea(
                placeholder="e.g., Focus on labeling the diagram parts.",
                value=ImageQuestionsState.v2_special_instructions,
                on_change=ImageQuestionsState.set_v2_special_instructions,
                rows="2",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
            class_name="mt-4",
        ),
    )


def _main_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.label("Subject", class_name="text-sm font-medium text-gray-700"),
                rx.el.select(
                    rx.el.option("Biology", value="Biology"),
                    rx.el.option("Chemistry", value="Chemistry"),
                    rx.el.option("Physics", value="Physics"),
                    rx.el.option("Math", value="Math"),
                    rx.el.option("History", value="History"),
                    value=ImageQuestionsState.selected_subject,
                    on_change=ImageQuestionsState.set_selected_subject,
                    class_name="mt-1 h-10 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
            ),
            rx.el.div(
                rx.el.label(
                    "Assessment Title", class_name="text-sm font-medium text-gray-700"
                ),
                rx.el.input(
                    placeholder="e.g., Cell Diagram Quiz",
                    value=ImageQuestionsState.assessment_title,
                    on_change=ImageQuestionsState.set_assessment_title,
                    class_name="mt-1 h-10 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
            ),
            rx.el.div(
                rx.el.label("Mode", class_name="text-sm font-medium text-gray-700 block mb-1"),
                _mode_toggle(),
            ),
            class_name="grid grid-cols-[0.7fr_2fr_auto] items-end gap-4 mb-6",
        ),
        rx.el.hr(class_name="border-gray-200 mb-5"),
        rx.cond(
            ImageQuestionsState.v2_is_quick_mode,
            _quick_mode_content(),
            _advanced_mode_content(),
        ),
        _action_bar(),
        _inline_model_picker(),
        _inline_progress(),
        class_name="flex-1 min-w-0 p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def _sidebar() -> rx.Component:
    disabled = _generate_disabled()
    return rx.el.div(
        # Images Ready
        rx.el.div(
            rx.el.span(
                "IMAGES READY",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider",
            ),
            rx.el.span(
                ImageQuestionsState.v2_images_ready_count.to(str),
                class_name="text-3xl font-bold text-gray-900 mt-1",
            ),
            rx.el.span(
                rx.el.span("of ", class_name="text-sm text-gray-500"),
                rx.el.span(
                    ImageQuestionsState.v2_total_slots.to(str),
                    class_name="text-sm text-gray-500",
                ),
                rx.el.span(" slots", class_name="text-sm text-gray-500"),
            ),
            class_name="flex flex-col items-center text-center pb-4 border-b border-gray-200",
        ),
        # Assessment badge
        rx.el.div(
            rx.el.span(
                "ASSESSMENT",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider",
            ),
            rx.el.span(
                ImageQuestionsState.v2_active_preset,
                class_name="mt-1 inline-block px-3 py-1 text-sm font-semibold text-blue-700 bg-blue-50 border border-blue-200 rounded-full",
            ),
            class_name="flex flex-col items-center text-center py-4 border-b border-gray-200",
        ),
        # Model badge
        rx.el.div(
            rx.el.span(
                "MODEL",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider",
            ),
            rx.el.span(
                ImageQuestionsState.v2_active_model_display,
                class_name="mt-1 inline-block px-3 py-1 text-sm font-medium text-gray-800 bg-gray-50 border border-gray-200 rounded-full",
            ),
            class_name="flex flex-col items-center text-center py-4 border-b border-gray-200",
        ),
        # Ready to go checklist
        rx.el.div(
            rx.el.span(
                "READY TO GO",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2",
            ),
            _checklist_item(ImageQuestionsState.has_uploaded_images, "Images uploaded"),
            _checklist_item(ImageQuestionsState.preflight_model_ready, "Model selected"),
            _checklist_item(ImageQuestionsState.preflight_api_key_ready, "API key ready"),
            _checklist_item(ImageQuestionsState.preflight_feature_ready, "Supports images"),
            class_name="flex flex-col gap-1.5 py-4 border-b border-gray-200",
        ),
        # Generate button
        rx.el.button(
            rx.cond(
                ImageQuestionsState.generating,
                rx.el.span(
                    rx.icon("loader-circle", class_name="w-4 h-4 animate-spin mr-2 inline-block"),
                    "Generating\u2026",
                ),
                "Generate Questions",
            ),
            on_click=ImageQuestionsState.handle_generate,
            disabled=disabled,
            class_name=rx.cond(
                disabled,
                "mt-4 w-full py-2.5 px-5 text-sm font-semibold text-white bg-gray-400 rounded-lg shadow-sm cursor-not-allowed",
                "mt-4 w-full py-2.5 px-5 text-sm font-semibold text-white bg-blue-600 rounded-lg shadow-sm hover:bg-blue-700 cursor-pointer",
            ),
        ),
        class_name="w-full lg:w-72 flex-shrink-0 p-4 bg-white rounded-xl border border-gray-200 shadow-sm h-fit lg:sticky lg:top-20",
    )


def _status_panel() -> rx.Component:
    disabled = _generate_disabled()
    return rx.el.div(
        rx.cond(
            ImageQuestionsState.error_message != "",
            rx.el.div(
                rx.el.div(
                    rx.icon("flag_triangle_right", class_name="h-5 w-5 text-red-500"),
                    rx.el.span(
                        ImageQuestionsState.error_message,
                        class_name="text-sm text-red-600",
                    ),
                    rx.el.button(
                        "Retry",
                        on_click=ImageQuestionsState.handle_generate,
                        disabled=disabled,
                        class_name="ml-auto px-3 py-1 text-xs font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:bg-gray-400",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.details(
                    rx.el.summary(
                        "Debug Information: View YAML Output",
                        class_name="text-sm font-medium text-gray-600 cursor-pointer mt-2",
                    ),
                    rx.code_block(
                        ImageQuestionsState.current_yaml,
                        language="yaml",
                        show_line_numbers=True,
                        can_copy=True,
                        custom_style={"maxHeight": "300px", "overflowY": "auto"},
                    ),
                    class_name="mt-2 p-2 bg-gray-50 rounded-md border",
                ),
                class_name="mt-4 p-3 bg-red-50 rounded-lg border border-red-200",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ImageQuestionsState.conversion_warning_message != "",
            rx.el.div(
                rx.el.div(
                    rx.icon("triangle-alert", class_name="h-5 w-5 text-amber-600"),
                    rx.el.span(
                        ImageQuestionsState.conversion_warning_message,
                        class_name="text-sm text-amber-800",
                    ),
                    class_name="flex items-center gap-2",
                ),
                class_name="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ImageQuestionsState.package_ready,
            rx.el.div(
                rx.el.div(
                    rx.icon("square_check", class_name="h-5 w-5 text-green-500"),
                    rx.el.span(
                        "Generation complete! You can now review your questions.",
                        class_name="text-sm text-green-600 font-medium",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h4(
                    "Question Summary",
                    class_name="text-md font-semibold text-gray-800 mt-4 mb-2",
                ),
                rx.el.div(
                    rx.foreach(
                        ImageQuestionsState.question_summary,
                        lambda summary_item: rx.el.div(
                            rx.el.span(
                                summary_item["type"],
                                class_name="text-xs font-medium text-gray-500",
                            ),
                            rx.el.span(
                                summary_item["count"].to_string(),
                                class_name="text-base font-bold text-gray-900",
                            ),
                            class_name="flex flex-col items-center justify-center p-1.5 bg-gray-50 rounded-md border",
                        ),
                    ),
                    class_name="grid grid-cols-7 gap-2",
                ),
                rx.el.div(
                    rx.button(
                        "Download Image Questions Package (.zip)",
                        on_click=ImageQuestionsState.download_image_package,
                        class_name="flex-1",
                        color_scheme="blue",
                    ),
                    rx.el.a(
                        rx.button(
                            "Review All Questions",
                            rx.icon("arrow-right", class_name="ml-2"),
                            class_name="w-full",
                            variant="outline",
                        ),
                        href="/review-download",
                        class_name="flex-1",
                    ),
                    rx.el.button(
                        rx.icon("trash-2", class_name="h-4 w-4"),
                        on_click=ImageQuestionsState.open_delete_package_modal,
                        class_name="p-2 text-red-600 bg-white border border-red-300 rounded-md hover:bg-red-50",
                        title="Delete all image questions",
                    ),
                    class_name="flex gap-4 mt-4 items-center",
                ),
                class_name="mt-4 p-4 bg-green-50 rounded-lg border border-green-200",
            ),
            rx.fragment(),
        ),
        class_name="max-w-7xl mx-auto mt-6 space-y-4",
    )


def image_questions_v2() -> rx.Component:
    return rx.fragment(
        image_delete_package_modal_v2(),
        nav_menu(),
        rx.el.main(
            rx.el.div(
                page_header("image", "Image Questions", "Quick/Advanced generation workspace"),
                rx.el.div(
                    _main_card(),
                    _sidebar(),
                    class_name="flex flex-col lg:flex-row gap-6 max-w-7xl mx-auto mt-6",
                ),
                _status_panel(),
                class_name="p-6 space-y-0",
            ),
            class_name="min-h-screen bg-gray-50 font-['Inter']",
        ),
    )


image_questions = image_questions_v2

__all__ = ["image_questions", "image_questions_v2"]
