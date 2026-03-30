"""Reading Material page — V2 layout matching text/image question pages."""

import reflex as rx

from app.components.layout_components import nav_menu, page_header
from app.components.model_switch_components import model_chip_group
from app.states.reading_material_state import ReadingMaterialState
from app.states.settings_state import SettingsState


def _generate_disabled() -> rx.Var[bool]:
    return ReadingMaterialState.generating | ~ReadingMaterialState.preflight_ready


def _content_type_toggle() -> rx.Component:
    """Two-button toggle for Reading Material / Slide Deck."""
    return rx.el.div(
        rx.el.button(
            "Reading Material",
            on_click=ReadingMaterialState.set_content_type("Reading Material"),
            class_name=rx.cond(
                ~ReadingMaterialState.is_slide_deck,
                "px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-l-lg transition-colors",
                "px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-l-lg transition-colors",
            ),
        ),
        rx.el.button(
            "Slide Deck",
            on_click=ReadingMaterialState.set_content_type("Slide Deck"),
            class_name=rx.cond(
                ReadingMaterialState.is_slide_deck,
                "px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-r-lg transition-colors",
                "px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-r-lg transition-colors",
            ),
        ),
        class_name="flex h-10",
    )


def _ready_dot_with_label(label: str, status: rx.Var[bool]) -> rx.Component:
    """Green/red dot with label shown when red."""
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


def _upload_section() -> rx.Component:
    """Reference materials — image and PDF upload side by side."""
    return rx.el.div(
        rx.el.label(
            "Reference Materials",
            rx.el.span("(Optional)", class_name="text-gray-400 font-normal ml-1"),
            class_name="text-sm font-medium text-gray-700 block mb-2",
        ),
        rx.el.div(
            # Image upload
            rx.cond(
                ReadingMaterialState.has_image,
                rx.el.div(
                    rx.icon("image", class_name="w-4 h-4 text-green-600 flex-shrink-0"),
                    rx.el.span(
                        ReadingMaterialState.uploaded_image_filename,
                        class_name="text-sm text-gray-900 truncate max-w-[120px]",
                    ),
                    rx.el.button(
                        "\u00d7",
                        on_click=ReadingMaterialState.clear_image,
                        class_name="ml-2 text-gray-500 hover:text-red-600 font-medium cursor-pointer",
                    ),
                    class_name="flex items-center px-3 py-2 bg-green-50 border border-green-200 rounded-md",
                ),
                rx.upload.root(
                    rx.el.div(
                        rx.icon("image", class_name="h-4 w-4 text-blue-600"),
                        rx.el.span(
                            "Upload Image",
                            class_name="text-sm text-gray-700 ml-1.5",
                        ),
                        class_name="flex items-center justify-center px-4 py-2",
                    ),
                    id="image-upload",
                    accept={
                        "image/png": [".png"],
                        "image/jpeg": [".jpg", ".jpeg"],
                        "image/gif": [".gif"],
                        "image/webp": [".webp"],
                    },
                    max_files=1,
                    on_drop=ReadingMaterialState.handle_image_upload(
                        rx.upload_files(upload_id="image-upload")
                    ),
                    class_name="bg-white border border-gray-300 rounded-md shadow-sm cursor-pointer hover:bg-gray-50 transition-colors",
                ),
            ),
            # PDF upload
            rx.cond(
                ReadingMaterialState.has_pdf,
                rx.el.div(
                    rx.icon("file-text", class_name="w-4 h-4 text-green-600 flex-shrink-0"),
                    rx.el.span(
                        ReadingMaterialState.uploaded_pdf_filename,
                        class_name="text-sm text-gray-900 truncate max-w-[120px]",
                    ),
                    rx.el.button(
                        "\u00d7",
                        on_click=ReadingMaterialState.clear_pdf,
                        class_name="ml-2 text-gray-500 hover:text-red-600 font-medium cursor-pointer",
                    ),
                    class_name="flex items-center px-3 py-2 bg-green-50 border border-green-200 rounded-md",
                ),
                rx.upload.root(
                    rx.el.div(
                        rx.icon("file-text", class_name="h-4 w-4 text-blue-600"),
                        rx.el.span(
                            "Upload PDF",
                            class_name="text-sm text-gray-700 ml-1.5",
                        ),
                        class_name="flex items-center justify-center px-4 py-2",
                    ),
                    id="pdf-upload",
                    accept={"application/pdf": [".pdf"]},
                    max_files=1,
                    on_drop=ReadingMaterialState.handle_pdf_upload(
                        rx.upload_files(upload_id="pdf-upload")
                    ),
                    class_name="bg-white border border-gray-300 rounded-md shadow-sm cursor-pointer hover:bg-gray-50 transition-colors",
                ),
            ),
            class_name="flex gap-4",
        ),
        class_name="mt-4",
    )


def _action_bar() -> rx.Component:
    """Three-part bar: model indicator | ready dots | generate button."""
    disabled = _generate_disabled()
    return rx.el.div(
        # ---- left: model indicator ----
        rx.el.div(
            rx.el.span(
                "Model",
                class_name="text-xs font-medium text-gray-500 uppercase tracking-wider mr-2",
            ),
            rx.el.span(
                ReadingMaterialState.active_model_display,
                class_name="text-xs font-medium text-gray-800 bg-gray-50 px-2 py-1 rounded border border-gray-200",
            ),
            rx.el.button(
                "change",
                on_click=ReadingMaterialState.toggle_model_picker,
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
                _ready_dot_with_label(
                    "Model selected", ReadingMaterialState.preflight_model_ready
                ),
                _ready_dot_with_label(
                    "API key ready", ReadingMaterialState.preflight_api_key_ready
                ),
                _ready_dot_with_label(
                    "Feature support", ReadingMaterialState.preflight_feature_ready
                ),
                class_name="flex items-center gap-2.5",
            ),
            class_name="flex items-center",
        ),
        # ---- right: generate button ----
        rx.el.button(
            rx.cond(
                ReadingMaterialState.generating,
                rx.el.span(
                    rx.icon(
                        "loader-circle",
                        class_name="w-4 h-4 animate-spin mr-2 inline-block",
                    ),
                    "Generating\u2026",
                ),
                rx.cond(
                    ReadingMaterialState.is_slide_deck,
                    "Generate Slide Deck",
                    "Generate Reading Material",
                ),
            ),
            on_click=ReadingMaterialState.handle_generate,
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
        ReadingMaterialState.model_picker_open,
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    rx.cond(
                        ReadingMaterialState.persist_model_choice,
                        "Use as default: On",
                        "Use as default: Off",
                    ),
                    on_click=ReadingMaterialState.toggle_persist_model_choice,
                    type="button",
                    class_name=rx.cond(
                        ReadingMaterialState.persist_model_choice,
                        "px-3 py-1.5 text-xs rounded-md bg-blue-100 text-blue-800 border border-blue-300",
                        "px-3 py-1.5 text-xs rounded-md bg-gray-100 text-gray-700 border border-gray-300",
                    ),
                ),
                rx.el.button(
                    "Reset to default",
                    on_click=ReadingMaterialState.reset_to_default_model,
                    type="button",
                    class_name="px-3 py-1.5 text-xs rounded-md bg-white text-gray-700 border border-gray-300 hover:bg-gray-50",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                model_chip_group(
                    "OpenAI",
                    SettingsState.openai_models,
                    ReadingMaterialState.active_model,
                    ReadingMaterialState.select_active_model,
                ),
                model_chip_group(
                    "Anthropic",
                    SettingsState.anthropic_models,
                    ReadingMaterialState.active_model,
                    ReadingMaterialState.select_active_model,
                ),
                model_chip_group(
                    "Gemini",
                    SettingsState.gemini_models,
                    ReadingMaterialState.active_model,
                    ReadingMaterialState.select_active_model,
                ),
                model_chip_group(
                    "Custom",
                    SettingsState.custom_models,
                    ReadingMaterialState.active_model,
                    ReadingMaterialState.select_active_model,
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
        ReadingMaterialState.generating,
        rx.el.div(
            rx.el.div(
                f"{ReadingMaterialState.progress}%",
                class_name="text-xs font-medium text-blue-700 mb-1",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="bg-blue-600 h-2 rounded-full transition-all",
                    style={
                        "width": ReadingMaterialState.progress.to(str) + "%"
                    },
                ),
                class_name="w-full bg-gray-200 rounded-full h-2 overflow-hidden",
            ),
            rx.el.p(
                ReadingMaterialState.generation_stage,
                class_name="text-xs text-gray-500 mt-1",
            ),
            class_name="mt-3",
        ),
        rx.fragment(),
    )


def _main_card() -> rx.Component:
    """Primary content area — left column."""
    return rx.el.div(
        # ---- Header row ----
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Grade Level", class_name="text-sm font-medium text-gray-700"
                ),
                rx.el.select(
                    rx.el.option("", value="", disabled=True),
                    rx.el.option("K-2 (Ages 5-7)", value="K-2 (Ages 5-7)"),
                    rx.el.option("3-5 (Ages 8-10)", value="3-5 (Ages 8-10)"),
                    rx.el.option("6-8 (Ages 11-13)", value="6-8 (Ages 11-13)"),
                    rx.el.option("9-12 (Ages 14-18)", value="9-12 (Ages 14-18)"),
                    rx.el.option("College", value="College"),
                    rx.el.option("Adult/Professional", value="Adult/Professional"),
                    value=ReadingMaterialState.grade_level,
                    on_change=ReadingMaterialState.set_grade_level,
                    class_name="mt-1 h-10 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
            ),
            rx.el.div(
                rx.el.label(
                    "Topic", class_name="text-sm font-medium text-gray-700"
                ),
                rx.el.input(
                    placeholder="e.g., Photosynthesis, American Revolution, Algebra Basics",
                    value=ReadingMaterialState.topic,
                    on_change=ReadingMaterialState.set_topic,
                    class_name="mt-1 h-10 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
            ),
            rx.el.div(
                rx.el.label(
                    "Output Type",
                    class_name="text-sm font-medium text-gray-700 block mb-1",
                ),
                _content_type_toggle(),
            ),
            class_name="grid grid-cols-[0.7fr_2fr_auto] items-end gap-4 mb-6",
        ),
        rx.el.hr(class_name="border-gray-200 mb-5"),
        # ---- Learning Objectives ----
        rx.el.div(
            rx.el.label(
                "Learning Objectives",
                rx.el.span(
                    "Enter each on a new line or separate with commas",
                    class_name="text-xs text-gray-400 ml-2 font-normal",
                ),
                class_name="text-sm font-medium text-gray-700",
            ),
            rx.el.textarea(
                placeholder="e.g.,\nUnderstand the process of photosynthesis\nIdentify key components of plant cells",
                value=ReadingMaterialState.objectives,
                on_change=ReadingMaterialState.set_objectives,
                rows="4",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
        ),
        # ---- Reference Materials ----
        _upload_section(),
        # ---- Additional Instructions ----
        rx.el.div(
            rx.el.label(
                "Additional Instructions",
                rx.el.span("(Optional)", class_name="text-gray-400 font-normal ml-1"),
                class_name="text-sm font-medium text-gray-700",
            ),
            rx.el.textarea(
                placeholder="e.g., Include real-world examples, Use simple vocabulary",
                value=ReadingMaterialState.user_prompt,
                on_change=ReadingMaterialState.set_user_prompt,
                rows="3",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
            class_name="mt-4",
        ),
        # ---- Action bar / model picker / progress ----
        _action_bar(),
        _inline_model_picker(),
        _inline_progress(),
        class_name="flex-1 min-w-0 p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def _sidebar() -> rx.Component:
    """Right sidebar with status sections."""
    disabled = _generate_disabled()
    return rx.el.div(
        # Output Type
        rx.el.div(
            rx.el.span(
                "OUTPUT TYPE",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider",
            ),
            rx.el.span(
                ReadingMaterialState.content_type_display,
                class_name="mt-1 inline-block px-3 py-1 text-sm font-semibold text-blue-700 bg-blue-50 border border-blue-200 rounded-full",
            ),
            class_name="flex flex-col items-center text-center pb-4 border-b border-gray-200",
        ),
        # Reference Files
        rx.el.div(
            rx.el.span(
                "REFERENCE FILES",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2",
            ),
            rx.cond(
                ReadingMaterialState.has_image | ReadingMaterialState.has_pdf,
                rx.el.div(
                    rx.cond(
                        ReadingMaterialState.has_image,
                        rx.el.div(
                            rx.icon("image", class_name="w-3.5 h-3.5 text-blue-500 flex-shrink-0"),
                            rx.el.span(
                                ReadingMaterialState.uploaded_image_filename,
                                class_name="text-sm text-gray-700 truncate max-w-[160px]",
                            ),
                            class_name="flex items-center gap-1.5",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        ReadingMaterialState.has_pdf,
                        rx.el.div(
                            rx.icon("file-text", class_name="w-3.5 h-3.5 text-blue-500 flex-shrink-0"),
                            rx.el.span(
                                ReadingMaterialState.uploaded_pdf_filename,
                                class_name="text-sm text-gray-700 truncate max-w-[160px]",
                            ),
                            class_name="flex items-center gap-1.5",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex flex-col gap-1",
                ),
                rx.el.span("None", class_name="text-sm text-gray-400 italic"),
            ),
            class_name="flex flex-col items-center text-center py-4 border-b border-gray-200",
        ),
        # Model
        rx.el.div(
            rx.el.span(
                "MODEL",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider",
            ),
            rx.el.span(
                ReadingMaterialState.active_model_display,
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
            _checklist_item(ReadingMaterialState.preflight_model_ready, "Model selected"),
            _checklist_item(
                ReadingMaterialState.preflight_api_key_ready, "API key ready"
            ),
            _checklist_item(
                ReadingMaterialState.preflight_feature_ready, "Feature support"
            ),
            class_name="flex flex-col gap-1.5 py-4 border-b border-gray-200",
        ),
        # Generate button
        rx.el.button(
            rx.cond(
                ReadingMaterialState.generating,
                rx.el.span(
                    rx.icon(
                        "loader-circle",
                        class_name="w-4 h-4 animate-spin mr-2 inline-block",
                    ),
                    "Generating\u2026",
                ),
                rx.cond(
                    ReadingMaterialState.is_slide_deck,
                    "Generate Slide Deck",
                    "Generate Reading Material",
                ),
            ),
            on_click=ReadingMaterialState.handle_generate,
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
    """Error, success, and generated-content panels below the two-column layout."""
    disabled = _generate_disabled()
    return rx.el.div(
        # Error message
        rx.cond(
            ReadingMaterialState.error_message != "",
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "flag_triangle_right", class_name="h-5 w-5 text-red-500"
                    ),
                    rx.el.span(
                        ReadingMaterialState.error_message,
                        class_name="text-sm text-red-600",
                    ),
                    rx.el.button(
                        "Retry",
                        on_click=ReadingMaterialState.handle_generate,
                        disabled=disabled,
                        class_name="ml-auto px-3 py-1 text-xs font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:bg-gray-400",
                    ),
                    class_name="flex items-center gap-2",
                ),
                class_name="p-3 bg-red-50 rounded-lg border border-red-200",
            ),
            rx.fragment(),
        ),
        # Success message
        rx.cond(
            ReadingMaterialState.success_message != "",
            rx.el.div(
                rx.el.div(
                    rx.icon("square_check", class_name="h-5 w-5 text-green-500"),
                    rx.el.span(
                        ReadingMaterialState.success_message,
                        class_name="text-sm text-green-600 font-medium",
                    ),
                    class_name="flex items-center gap-2",
                ),
                class_name="p-3 bg-green-50 rounded-lg border border-green-200",
            ),
            rx.fragment(),
        ),
        # Generated content
        rx.cond(
            ReadingMaterialState.generated_content != "",
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        rx.cond(
                            ReadingMaterialState.is_slide_deck,
                            "Generated Slide Deck",
                            "Generated Reading Material",
                        ),
                        class_name="text-lg font-semibold text-gray-900",
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Copy",
                            on_click=rx.set_clipboard(
                                ReadingMaterialState.generated_content
                            ),
                            class_name="px-3 py-1.5 text-sm font-medium bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200",
                        ),
                        rx.el.button(
                            "Clear",
                            on_click=ReadingMaterialState.clear_output,
                            class_name="px-3 py-1.5 text-sm font-medium bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200",
                        ),
                        rx.el.button(
                            rx.cond(
                                ReadingMaterialState.downloading,
                                rx.el.span(
                                    rx.icon(
                                        "loader-circle",
                                        class_name="w-3.5 h-3.5 animate-spin mr-1.5 inline-block",
                                    ),
                                    "Downloading\u2026",
                                ),
                                "Download PDF",
                            ),
                            on_click=ReadingMaterialState.download_pdf,
                            disabled=ReadingMaterialState.downloading,
                            class_name=rx.cond(
                                ReadingMaterialState.downloading,
                                "px-3 py-1.5 text-sm font-medium bg-blue-400 text-white rounded-md cursor-not-allowed",
                                "px-3 py-1.5 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700",
                            ),
                        ),
                        class_name="flex gap-2",
                    ),
                    class_name="flex justify-between items-center mb-4",
                ),
                rx.el.div(
                    rx.markdown(
                        ReadingMaterialState.generated_content,
                        class_name="prose prose-sm max-w-none text-gray-900",
                    ),
                    class_name="p-4 bg-white border border-gray-200 rounded-md max-h-[600px] overflow-y-auto",
                ),
                class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
            ),
            rx.fragment(),
        ),
        class_name="max-w-7xl mx-auto mt-6 space-y-4",
    )


def reading_material() -> rx.Component:
    """Reading material generation page — V2 layout."""
    return rx.fragment(
        nav_menu(),
        rx.el.main(
            rx.el.div(
                page_header(
                    "book-open", "Reading Material", "Generate educational content"
                ),
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
