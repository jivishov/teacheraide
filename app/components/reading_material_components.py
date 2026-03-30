"""
Reading Material Components

UI components for the reading material generation page.
Following CLAUDE.md guidelines for text color styling.
"""

import reflex as rx
from app.components.model_switch_components import quick_model_switcher
from app.states.reading_material_state import ReadingMaterialState
from app.states.settings_state import SettingsState


def content_type_selector() -> rx.Component:
    """Content type selector (Reading Material vs Slide Deck)."""
    return rx.el.div(
        rx.el.label(
            "Content Type",
            class_name="block text-sm font-medium text-gray-900 mb-2"
        ),
        rx.el.div(
            # Reading Material option
            rx.el.label(
                rx.el.input(
                    type="radio",
                    name="content-type",
                    value="Reading Material",
                    checked=~ReadingMaterialState.is_slide_deck,
                    on_change=ReadingMaterialState.set_content_type("Reading Material"),
                    class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer"
                ),
                rx.el.span("Reading Material", class_name="ml-2 text-sm text-gray-900"),
                class_name="flex items-center cursor-pointer"
            ),
            # Slide Deck option
            rx.el.label(
                rx.el.input(
                    type="radio",
                    name="content-type",
                    value="Slide Deck",
                    checked=ReadingMaterialState.is_slide_deck,
                    on_change=ReadingMaterialState.set_content_type("Slide Deck"),
                    class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer"
                ),
                rx.el.span("Slide Deck", class_name="ml-2 text-sm text-gray-900"),
                class_name="flex items-center cursor-pointer"
            ),
            class_name="flex gap-6"
        ),
        class_name="mb-4"
    )


def grade_level_selector() -> rx.Component:
    """Grade level dropdown selector."""
    return rx.el.div(
        rx.el.label(
            "Grade Level",
            html_for="grade-level",
            class_name="block text-sm font-medium text-gray-900"
        ),
        rx.el.select(
            rx.el.option("Select Grade Level...", value="", disabled=True),
            rx.foreach(
                ReadingMaterialState.grade_levels,
                lambda level: rx.el.option(level, value=level)
            ),
            id="grade-level",
            value=ReadingMaterialState.grade_level,
            on_change=ReadingMaterialState.set_grade_level,
            class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
        ),
        class_name="mb-4"
    )


def topic_input() -> rx.Component:
    """Topic text input."""
    return rx.el.div(
        rx.el.label(
            "Topic",
            html_for="topic",
            class_name="block text-sm font-medium text-gray-900"
        ),
        rx.el.input(
            id="topic",
            type="text",
            placeholder="e.g., Photosynthesis, American Revolution, Algebra Basics",
            value=ReadingMaterialState.topic,
            on_change=ReadingMaterialState.set_topic,
            class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
        ),
        class_name="mb-4"
    )


def objectives_input() -> rx.Component:
    """Learning objectives textarea."""
    return rx.el.div(
        rx.el.label(
            "Learning Objectives",
            html_for="objectives",
            class_name="block text-sm font-medium text-gray-900"
        ),
        rx.el.p(
            "Enter each objective on a new line or separate with commas",
            class_name="text-xs text-gray-600 mt-1"
        ),
        rx.el.textarea(
            id="objectives",
            placeholder="- Students will understand the process of photosynthesis\n- Students will identify the inputs and outputs\n- Students will explain why photosynthesis is important",
            value=ReadingMaterialState.objectives,
            on_change=ReadingMaterialState.set_objectives,
            rows=4,
            class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none"
        ),
        class_name="mb-4"
    )


def custom_instructions_input() -> rx.Component:
    """Additional instructions textarea."""
    return rx.el.div(
        rx.el.label(
            "Additional Instructions (Optional)",
            html_for="instructions",
            class_name="block text-sm font-medium text-gray-900"
        ),
        rx.el.textarea(
            id="instructions",
            placeholder="e.g., Include real-world examples, focus on visual descriptions, add discussion questions at the end...",
            value=ReadingMaterialState.user_prompt,
            on_change=ReadingMaterialState.set_user_prompt,
            rows=3,
            class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none"
        ),
        class_name="mb-4"
    )


def upload_buttons_section() -> rx.Component:
    """Image and PDF upload buttons side by side."""
    return rx.el.div(
        rx.el.label(
            "Reference Materials (Optional)",
            class_name="block text-sm font-medium text-gray-900 mb-2"
        ),
        rx.el.div(
            # Image upload button or filename chip
            rx.cond(
                ReadingMaterialState.has_image,
                # Show filename chip with remove button
                rx.el.div(
                    rx.el.span(
                        ReadingMaterialState.uploaded_image_filename,
                        class_name="text-sm text-gray-900 truncate max-w-[120px]"
                    ),
                    rx.el.button(
                        "×",
                        on_click=ReadingMaterialState.clear_image,
                        class_name="ml-2 text-gray-500 hover:text-red-600 font-medium"
                    ),
                    class_name="flex items-center px-3 py-2 bg-green-50 border border-green-200 rounded-md"
                ),
                # Show upload button
                rx.upload.root(
                    rx.el.div(
                        rx.icon("image", class_name="h-4 w-4 text-blue-600"),
                        rx.el.span("Upload Image", class_name="text-sm text-gray-700 ml-1.5"),
                        class_name="flex items-center justify-center px-4 py-2"
                    ),
                    id="image-upload",
                    accept={
                        "image/png": [".png"],
                        "image/jpeg": [".jpg", ".jpeg"],
                        "image/gif": [".gif"],
                        "image/webp": [".webp"],
                    },
                    max_files=1,
                    on_drop=ReadingMaterialState.handle_image_upload(rx.upload_files(upload_id="image-upload")),
                    class_name="bg-white border border-gray-300 rounded-md shadow-sm cursor-pointer hover:bg-gray-50 transition-colors"
                )
            ),
            # PDF upload button or filename chip
            rx.cond(
                ReadingMaterialState.has_pdf,
                # Show filename chip with remove button
                rx.el.div(
                    rx.el.span(
                        ReadingMaterialState.uploaded_pdf_filename,
                        class_name="text-sm text-gray-900 truncate max-w-[120px]"
                    ),
                    rx.el.button(
                        "×",
                        on_click=ReadingMaterialState.clear_pdf,
                        class_name="ml-2 text-gray-500 hover:text-red-600 font-medium"
                    ),
                    class_name="flex items-center px-3 py-2 bg-green-50 border border-green-200 rounded-md"
                ),
                # Show upload button
                rx.upload.root(
                    rx.el.div(
                        rx.icon("file-text", class_name="h-4 w-4 text-blue-600"),
                        rx.el.span("Upload PDF", class_name="text-sm text-gray-700 ml-1.5"),
                        class_name="flex items-center justify-center px-4 py-2"
                    ),
                    id="pdf-upload",
                    accept={
                        "application/pdf": [".pdf"],
                    },
                    max_files=1,
                    on_drop=ReadingMaterialState.handle_pdf_upload(rx.upload_files(upload_id="pdf-upload")),
                    class_name="bg-white border border-gray-300 rounded-md shadow-sm cursor-pointer hover:bg-gray-50 transition-colors"
                )
            ),
            class_name="flex justify-center gap-6"
        ),
        class_name="mb-4"
    )


def model_info_section() -> rx.Component:
    """Display current model configuration."""
    return rx.el.div(
        rx.el.div(
            rx.el.span("Model: ", class_name="text-sm text-gray-600"),
            rx.el.span(
                rx.cond(
                    ReadingMaterialState.active_model != "",
                    ReadingMaterialState.active_model,
                    ReadingMaterialState.default_model_snapshot,
                ),
                class_name="text-sm font-medium text-gray-900"
            ),
            rx.el.span(
                rx.cond(
                    ReadingMaterialState.has_image,
                    " (image context)",
                    " (text/pdf context)",
                ),
                class_name="text-sm text-green-600"
            ),
            class_name="flex items-center"
        ),
        class_name="mb-4 p-3 bg-gray-50 rounded-md"
    )


def preflight_checklist_section() -> rx.Component:
    """Display preflight readiness checklist for generation."""
    return rx.el.div(
        rx.el.p("Preflight", class_name="text-sm font-semibold text-gray-700"),
        rx.el.div(
            rx.el.span(
                rx.cond(ReadingMaterialState.preflight_model_ready, "✅ Model selected", "❌ Model missing"),
                class_name="text-xs text-gray-700",
            ),
            rx.el.span(
                rx.cond(ReadingMaterialState.preflight_api_key_ready, "✅ API key ready", "❌ API key missing"),
                class_name="text-xs text-gray-700",
            ),
            rx.el.span(
                rx.cond(ReadingMaterialState.preflight_feature_ready, "✅ Model supports current context", "❌ Model lacks required support"),
                class_name="text-xs text-gray-700",
            ),
            class_name="mt-2 flex flex-wrap gap-3",
        ),
        class_name="mb-4 p-3 bg-gray-50 rounded-md border border-gray-200",
    )


def generate_button() -> rx.Component:
    """Generate button."""
    return rx.el.div(
        rx.el.button(
            rx.cond(
                ReadingMaterialState.generating,
                rx.el.span(
                    rx.el.span(class_name="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"),
                    "Generating...",
                    class_name="flex items-center"
                ),
                "Generate Reading Material"
            ),
            on_click=ReadingMaterialState.handle_generate,
            disabled=rx.cond(
                ReadingMaterialState.generating,
                True,
                ~ReadingMaterialState.preflight_ready
            ),
            class_name=rx.cond(
                ReadingMaterialState.generating | ~ReadingMaterialState.preflight_ready,
                "w-full py-3 px-4 bg-gray-400 text-white font-medium rounded-md cursor-not-allowed",
                "w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            )
        ),
        rx.el.p(
            rx.el.span(f"Stage: {ReadingMaterialState.generation_stage}"),
            rx.el.span(" | Active model:", class_name="ml-2"),
            rx.el.span(
                rx.cond(
                    ReadingMaterialState.active_model != "",
                    ReadingMaterialState.active_model,
                    rx.cond(
                        ReadingMaterialState.default_model_snapshot != "",
                        ReadingMaterialState.default_model_snapshot,
                        "Not selected",
                    ),
                ),
                class_name="font-medium text-gray-700",
            ),
            class_name="mt-3 text-sm text-gray-600 flex flex-wrap items-center gap-1",
        ),
        class_name="mb-4"
    )


def error_message() -> rx.Component:
    """Error message display."""
    return rx.cond(
        ReadingMaterialState.error_message != "",
        rx.el.div(
            ReadingMaterialState.error_message,
            class_name="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md mb-4"
        ),
        rx.fragment()
    )


def success_message() -> rx.Component:
    """Success message display."""
    return rx.cond(
        ReadingMaterialState.success_message != "",
        rx.el.div(
            ReadingMaterialState.success_message,
            class_name="p-3 bg-green-50 border border-green-200 text-green-700 rounded-md mb-4"
        ),
        rx.fragment()
    )


def output_section() -> rx.Component:
    """Generated content output section."""
    return rx.cond(
        ReadingMaterialState.generated_content != "",
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    rx.cond(
                        ReadingMaterialState.is_slide_deck,
                        "Generated Slide Deck",
                        "Generated Reading Material"
                    ),
                    class_name="text-lg font-semibold text-gray-900"
                ),
                rx.el.div(
                    rx.el.button(
                        "Copy",
                        on_click=rx.set_clipboard(ReadingMaterialState.generated_content),
                        class_name="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    ),
                    rx.el.button(
                        "Clear",
                        on_click=ReadingMaterialState.clear_output,
                        class_name="ml-2 px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    ),
                    rx.el.button(
                        rx.cond(
                            ReadingMaterialState.downloading,
                            rx.el.span(
                                rx.el.span(class_name="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full mr-1"),
                                "Downloading...",
                                class_name="flex items-center"
                            ),
                            "Download PDF"
                        ),
                        on_click=ReadingMaterialState.download_pdf,
                        disabled=ReadingMaterialState.downloading,
                        class_name=rx.cond(
                            ReadingMaterialState.downloading,
                            "ml-2 px-3 py-1 text-sm bg-blue-400 text-white rounded cursor-not-allowed",
                            "ml-2 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        )
                    ),
                    class_name="flex"
                ),
                class_name="flex justify-between items-center mb-3"
            ),
            rx.el.div(
                rx.markdown(
                    ReadingMaterialState.generated_content,
                    class_name="prose prose-sm max-w-none text-gray-900"
                ),
                class_name="p-4 bg-white border border-gray-200 rounded-md max-h-[600px] overflow-y-auto"
            ),
            class_name="mt-6"
        ),
        rx.fragment()
    )


def reading_material_form() -> rx.Component:
    """Main form component."""
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                rx.cond(
                    ReadingMaterialState.is_slide_deck,
                    "Generate Slide Deck",
                    "Generate Reading Material"
                ),
                class_name="text-2xl font-bold text-gray-900 mb-2"
            ),
            rx.el.p(
                rx.cond(
                    ReadingMaterialState.is_slide_deck,
                    "Create an illustrated slide deck for presentations.",
                    "Create educational reading material tailored to your students' grade level and learning objectives."
                ),
                class_name="text-gray-600 mb-6"
            ),
            class_name="mb-6"
        ),
        content_type_selector(),
        grade_level_selector(),
        topic_input(),
        objectives_input(),
        custom_instructions_input(),
        upload_buttons_section(),
        quick_model_switcher(
            title="Model Selection",
            selected_model=ReadingMaterialState.active_model,
            default_model=ReadingMaterialState.default_model_snapshot,
            openai_models=SettingsState.openai_models,
            anthropic_models=SettingsState.anthropic_models,
            gemini_models=SettingsState.gemini_models,
            custom_models=SettingsState.custom_models,
            on_select_handler=ReadingMaterialState.select_active_model,
            persist_choice=ReadingMaterialState.persist_model_choice,
            on_toggle_persist_handler=ReadingMaterialState.toggle_persist_model_choice,
            on_reset_handler=ReadingMaterialState.reset_to_default_model,
        ),
        preflight_checklist_section(),
        success_message(),
        model_info_section(),
        generate_button(),
        error_message(),
        output_section(),
        class_name="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-sm"
    )


def reading_material_page() -> rx.Component:
    """Full page component."""
    return rx.el.div(
        rx.el.div(
            reading_material_form(),
            class_name="container mx-auto py-8 px-4"
        ),
        class_name="min-h-screen bg-gray-50"
    )
