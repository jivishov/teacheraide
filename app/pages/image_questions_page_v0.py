"""Legacy Image Questions V0 page."""

import reflex as rx

from app.components.layout_components import nav_menu, page_header
from app.components.model_switch_components import quick_model_switcher
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
    return handlers[index](rx.upload_files(upload_id=f"upload_slot_{index}"))


def image_delete_package_modal() -> rx.Component:
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
                        rx.dialog.title("Delete Image Questions", class_name="text-lg font-semibold text-gray-900"),
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


def _image_upload_slot(index: int) -> rx.Component:
    """Create a compact image upload card for 2-column grid."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                f"Q{index + 1}",
                class_name="text-sm font-bold text-gray-800",
            ),
            rx.cond(
                (index < ImageQuestionsState.uploaded_images.length())
                & (ImageQuestionsState.uploaded_images[index] != ""),
                rx.el.span(
                    class_name="w-2 h-2 rounded-full bg-green-500 ml-2",
                ),
                rx.el.span(
                    class_name="w-2 h-2 rounded-full bg-gray-300 ml-2",
                ),
            ),
            class_name="flex items-center mb-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label("Question Type", class_name="text-sm font-medium text-gray-700"),
                rx.el.select(
                    rx.el.option("Multiple choice", value="Multiple choice"),
                    rx.el.option("True/False", value="True/False"),
                    rx.el.option("Fill in blank", value="Fill in blank"),
                    rx.el.option("Matching", value="Matching"),
                    value=rx.cond(
                        index < ImageQuestionsState.question_types.length(),
                        ImageQuestionsState.question_types[index],
                        "Multiple choice",
                    ),
                    on_change=lambda value, i=index: ImageQuestionsState.set_question_type_at_index(i, value),
                    class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
                class_name="w-1/2",
            ),
            rx.el.div(
                rx.el.label("Image", class_name="text-sm font-medium text-gray-700 block"),
                rx.upload.root(
                    rx.box(
                        rx.icon(
                            tag="cloud_upload",
                            style={"width": "1rem", "height": "1rem", "color": "#2563eb"},
                        ),
                        rx.text(
                            "Upload",
                            style={"fontSize": "0.875rem", "color": "#374151", "marginLeft": "0.375rem"},
                        ),
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "padding": "0.5rem 1rem",
                        },
                    ),
                    id=f"upload_slot_{index}",
                    accept={"image/*": [".jpg", ".jpeg", ".png"]},
                    on_drop=_upload_handler_for_slot(index),
                    max_files=1,
                    style={
                        "marginTop": "0.25rem",
                        "backgroundColor": "white",
                        "border": "1px solid #d1d5db",
                        "borderRadius": "0.375rem",
                        "boxShadow": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
                        "cursor": "pointer",
                        "width": "100%",
                    },
                ),
                class_name="w-1/2",
            ),
            class_name="flex gap-3 items-end mb-2",
        ),
        rx.cond(
            (index < ImageQuestionsState.uploaded_images.length())
            & (ImageQuestionsState.uploaded_images[index] != ""),
            rx.el.div(
                rx.icon("square-check", class_name="w-4 h-4 text-green-600"),
                rx.el.span(
                    ImageQuestionsState.uploaded_images[index],
                    class_name="text-sm text-green-700 truncate ml-1.5",
                ),
                class_name="flex items-center mb-2 px-2 py-1.5 bg-green-50 border border-green-200 rounded-md",
            ),
            None,
        ),
        rx.el.div(
            rx.el.label("Prompt", class_name="text-sm font-medium text-gray-700"),
            rx.el.textarea(
                placeholder="Optional: Focus on specific aspects, relate to concepts, or provide context for the question...",
                value=rx.cond(
                    index < ImageQuestionsState.image_prompts.length(),
                    ImageQuestionsState.image_prompts[index],
                    "",
                ),
                on_change=lambda value, i=index: ImageQuestionsState.set_prompt_at_index(i, value),
                rows="8",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
        ),
        class_name="p-4 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow",
    )


def image_questions() -> rx.Component:
    return rx.fragment(
        image_delete_package_modal(),
        nav_menu(),
        rx.el.main(
            rx.el.div(
                page_header("image", "Image Questions V0", "Legacy question generation layout"),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.label("Subject Area", class_name="text-sm font-medium text-gray-700"),
                            rx.el.select(
                                rx.el.option("Biology", value="Biology"),
                                rx.el.option("Chemistry", value="Chemistry"),
                                rx.el.option("Physics", value="Physics"),
                                rx.el.option("Math", value="Math"),
                                rx.el.option("History", value="History"),
                                default_value=ImageQuestionsState.selected_subject,
                                on_change=ImageQuestionsState.set_selected_subject,
                                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                            ),
                        ),
                        rx.el.div(
                            rx.el.label("Assessment Type", class_name="text-sm font-medium text-gray-700"),
                            rx.el.select(
                                rx.el.option("Formative", value="Formative"),
                                rx.el.option("Summative", value="Summative"),
                                rx.el.option("Practice", value="Practice"),
                                default_value=ImageQuestionsState.assessment_type,
                                on_change=ImageQuestionsState.set_assessment_type,
                                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                            ),
                        ),
                        rx.el.div(
                            rx.el.label("Assessment Title", class_name="text-sm font-medium text-gray-700"),
                            rx.el.input(
                                placeholder="e.g., Biology Chapter 5 Quiz",
                                value=ImageQuestionsState.assessment_title,
                                on_change=ImageQuestionsState.set_assessment_title,
                                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                            ),
                        ),
                        class_name="grid gap-4 mb-4",
                        style={"gridTemplateColumns": "0.7fr 0.5fr 2.8fr"},
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Number of Questions", class_name="text-sm font-medium text-gray-700"
                        ),
                        rx.slider(
                            default_value=[ImageQuestionsState.num_questions],
                            min=1,
                            max=10,
                            on_change=ImageQuestionsState.set_num_questions_from_slider,
                            class_name="mt-2",
                        ),
                        rx.el.p(
                            f"Selected: {ImageQuestionsState.num_questions}",
                            class_name="text-sm text-gray-600 mt-1",
                        ),
                    ),
                    class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
                ),
                quick_model_switcher(
                    title="Model Selection",
                    selected_model=ImageQuestionsState.active_model,
                    default_model=ImageQuestionsState.default_model_snapshot,
                    openai_models=SettingsState.openai_models,
                    anthropic_models=SettingsState.anthropic_models,
                    gemini_models=SettingsState.gemini_models,
                    custom_models=SettingsState.custom_models,
                    on_select_handler=ImageQuestionsState.select_active_model,
                    persist_choice=ImageQuestionsState.persist_model_choice,
                    on_toggle_persist_handler=ImageQuestionsState.toggle_persist_model_choice,
                    on_reset_handler=ImageQuestionsState.reset_to_default_model,
                ),
                rx.el.div(
                    rx.cond(
                        ImageQuestionsState.num_questions >= 1,
                        _image_upload_slot(0),
                        rx.box(),
                    ),
                    rx.cond(
                        ImageQuestionsState.num_questions >= 2,
                        _image_upload_slot(1),
                        rx.box(),
                    ),
                    rx.cond(
                        ImageQuestionsState.num_questions >= 3,
                        _image_upload_slot(2),
                        rx.box(),
                    ),
                    rx.cond(
                        ImageQuestionsState.num_questions >= 4,
                        _image_upload_slot(3),
                        rx.box(),
                    ),
                    rx.cond(
                        ImageQuestionsState.num_questions >= 5,
                        _image_upload_slot(4),
                        rx.box(),
                    ),
                    rx.cond(
                        ImageQuestionsState.num_questions >= 6,
                        _image_upload_slot(5),
                        rx.box(),
                    ),
                    rx.cond(
                        ImageQuestionsState.num_questions >= 7,
                        _image_upload_slot(6),
                        rx.box(),
                    ),
                    rx.cond(
                        ImageQuestionsState.num_questions >= 8,
                        _image_upload_slot(7),
                        rx.box(),
                    ),
                    rx.cond(
                        ImageQuestionsState.num_questions >= 9,
                        _image_upload_slot(8),
                        rx.box(),
                    ),
                    rx.cond(
                        ImageQuestionsState.num_questions >= 10,
                        _image_upload_slot(9),
                        rx.box(),
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            f"Total Images Uploaded: {ImageQuestionsState.total_uploaded_images}",
                            class_name="text-lg font-semibold text-gray-900",
                        ),
                        rx.el.button(
                            rx.cond(
                                ImageQuestionsState.generating,
                                rx.spinner(class_name="mr-2"),
                                None,
                            ),
                            "Generate Questions",
                            on_click=ImageQuestionsState.handle_generate,
                            is_disabled=ImageQuestionsState.generating
                            | ~ImageQuestionsState.has_uploaded_images
                            | ~ImageQuestionsState.preflight_ready,
                            class_name="flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400",
                        ),
                        class_name="flex items-center justify-between",
                    ),
                    rx.el.div(
                        rx.el.p("Preflight", class_name="text-sm font-semibold text-gray-700"),
                        rx.el.div(
                            rx.el.span(
                                rx.cond(ImageQuestionsState.preflight_model_ready, "✅ Model selected", "❌ Model missing"),
                                class_name="text-xs text-gray-700",
                            ),
                            rx.el.span(
                                rx.cond(ImageQuestionsState.preflight_api_key_ready, "✅ API key ready", "❌ API key missing"),
                                class_name="text-xs text-gray-700",
                            ),
                            rx.el.span(
                                rx.cond(ImageQuestionsState.preflight_feature_ready, "✅ Model supports image input", "❌ Model lacks image support"),
                                class_name="text-xs text-gray-700",
                            ),
                            class_name="mt-2 flex flex-wrap gap-3",
                        ),
                        class_name="mt-4 p-3 bg-gray-50 rounded-md border border-gray-200",
                    ),
                    rx.cond(
                        ImageQuestionsState.generating,
                        rx.el.div(
                            rx.el.div(
                                f"{ImageQuestionsState.progress}%",
                                class_name="text-sm font-medium text-blue-700",
                            ),
                            rx.el.div(
                                rx.el.div(
                                    class_name="bg-blue-600 h-2.5 rounded-full",
                                    style={
                                        "width": ImageQuestionsState.progress.to(str) + "%"
                                    },
                                ),
                                class_name="w-full bg-gray-200 rounded-full h-2.5",
                            ),
                            class_name="w-full mt-4",
                        ),
                        None,
                    ),
                    rx.el.p(
                        rx.el.span(f"Stage: {ImageQuestionsState.generation_stage}"),
                        rx.el.span(" | Active model:", class_name="ml-2"),
                        rx.el.span(
                            rx.cond(
                                ImageQuestionsState.active_model != "",
                                ImageQuestionsState.active_model,
                                rx.cond(
                                    ImageQuestionsState.default_model_snapshot != "",
                                    ImageQuestionsState.default_model_snapshot,
                                    "Not selected",
                                ),
                            ),
                            class_name="font-medium text-gray-700",
                        ),
                        class_name="mt-3 text-sm text-gray-600 flex flex-wrap items-center gap-1",
                    ),
                    rx.cond(
                        ImageQuestionsState.error_message != "",
                        rx.el.div(
                            rx.el.div(
                                rx.icon(
                                    "flag_triangle_right", class_name="h-5 w-5 text-red-500"
                                ),
                                rx.el.span(
                                    ImageQuestionsState.error_message,
                                    class_name="text-sm text-red-600",
                                ),
                                rx.el.button(
                                    "Retry",
                                    on_click=ImageQuestionsState.handle_generate,
                                    is_disabled=ImageQuestionsState.generating | ~ImageQuestionsState.preflight_ready,
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
                                    custom_style={
                                        "maxHeight": "300px",
                                        "overflowY": "auto",
                                    },
                                ),
                                class_name="mt-2 p-2 bg-gray-50 rounded-md border",
                            ),
                            class_name="mt-4 p-3 bg-red-50 rounded-lg border border-red-200",
                        ),
                        None,
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
                        None,
                    ),
                    rx.cond(
                        ImageQuestionsState.package_ready,
                        rx.el.div(
                            rx.el.div(
                                rx.icon(
                                    "square_check", class_name="h-5 w-5 text-green-500"
                                ),
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
                                    lambda s: rx.el.div(
                                        rx.el.span(
                                            s["type"],
                                            class_name="text-xs font-medium text-gray-500",
                                        ),
                                        rx.el.span(
                                            s["count"].to_string(),
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
                        None,
                    ),
                    class_name="mt-6 p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
                ),
                class_name="p-6 space-y-6",
            ),
            class_name="min-h-screen bg-gray-50 font-['Inter']",
        ),
    )


image_questions_v0 = image_questions

__all__ = ["image_questions", "image_questions_v0"]
