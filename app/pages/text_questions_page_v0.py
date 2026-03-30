"""Legacy Text Questions V0 page."""

import reflex as rx

from app.components.layout_components import nav_menu, page_header
from app.components.model_switch_components import quick_model_switcher
from app.components.text_question_components import question_type_card
from app.states.settings_state import SettingsState
from app.states.text_questions_state import TextQuestionsState


def text_delete_package_modal() -> rx.Component:
    """Modal for text package delete confirmation."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon("triangle-alert", class_name="h-6 w-6 text-red-600"),
                        class_name="flex items-center justify-center w-12 h-12 rounded-full bg-red-100",
                    ),
                    rx.el.div(
                        rx.dialog.title("Delete Text Questions", class_name="text-lg font-semibold text-gray-900"),
                        rx.dialog.description(
                            "Are you sure you want to delete all generated text questions? This action cannot be undone.",
                            class_name="mt-2 text-sm text-gray-500",
                        ),
                        class_name="ml-4",
                    ),
                    class_name="flex items-start",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=TextQuestionsState.close_delete_package_modal,
                        class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50",
                    ),
                    rx.el.button(
                        "Delete All",
                        on_click=TextQuestionsState.confirm_delete_package,
                        class_name="ml-3 px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700",
                    ),
                    class_name="mt-6 flex justify-end",
                ),
                class_name="p-6",
            ),
            class_name="max-w-md mx-auto bg-white rounded-lg shadow-xl",
        ),
        open=TextQuestionsState.delete_package_modal_open,
    )


def text_questions() -> rx.Component:
    question_types = [
        {
            "icon": "list-checks",
            "q_type": "mcq",
            "name": "MCQ",
            "desc": "Multiple Choice",
        },
        {
            "icon": "check-check",
            "q_type": "mrq",
            "name": "MRQ",
            "desc": "Multiple Response",
        },
        {"icon": "toggle-right", "q_type": "tf", "name": "T/F", "desc": "True/False"},
        {
            "icon": "pilcrow",
            "q_type": "fib",
            "name": "FIB",
            "desc": "Fill-in-Blank",
        },
        {
            "icon": "pencil-ruler",
            "q_type": "essay",
            "name": "Essay",
            "desc": "Essay",
        },
        {
            "icon": "shuffle",
            "q_type": "match",
            "name": "Match",
            "desc": "Matching",
        },
        {
            "icon": "arrow-down-up",
            "q_type": "order",
            "name": "Order",
            "desc": "Ordering",
        },
    ]
    return rx.fragment(
        text_delete_package_modal(),
        nav_menu(),
        rx.el.main(
            rx.el.div(
                page_header("file-text", "Text Questions V0", "Legacy question generation layout"),
                rx.cond(
                    TextQuestionsState.is_conversion_mode,
                    rx.el.div(
                        rx.icon("list-checks", class_name="w-5 h-5 text-emerald-600"),
                        rx.el.div(
                            rx.el.p(
                                "PDF Question Conversion Mode",
                                class_name="text-sm font-semibold text-emerald-800",
                            ),
                            rx.el.p(
                                "This run extracts existing questions from the uploaded PDF into YAML and QTI. "
                                "Question counts are auto-detected from the source file.",
                                class_name="text-xs text-emerald-700",
                            ),
                        ),
                        class_name="flex items-start gap-3 p-3 bg-emerald-50 rounded-md border border-emerald-200",
                    ),
                    rx.fragment(),
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.label("Subject Area", class_name="text-sm font-medium text-gray-700"),
                            rx.el.select(
                                rx.el.option("Biology", value="Biology"),
                                rx.el.option("Chemistry", value="Chemistry"),
                                rx.el.option("Physics", value="Physics"),
                                rx.el.option("Math", value="Math"),
                                rx.el.option("PLTW Medical Interventions", value="PLTW Medical Interventions"),
                                default_value=TextQuestionsState.selected_subject,
                                on_change=TextQuestionsState.set_selected_subject,
                                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                            ),
                        ),
                        rx.el.div(
                            rx.el.label("Assessment Type", class_name="text-sm font-medium text-gray-700"),
                            rx.el.select(
                                rx.el.option("Formative", value="Formative"),
                                rx.el.option("Summative", value="Summative"),
                                rx.el.option("Practice", value="Practice"),
                                default_value=TextQuestionsState.assessment_type,
                                on_change=TextQuestionsState.set_assessment_type,
                                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                            ),
                        ),
                        rx.el.div(
                            rx.el.label("Assessment Title", class_name="text-sm font-medium text-gray-700"),
                            rx.el.input(
                                placeholder="e.g., Biology Chapter 5 Quiz",
                                value=TextQuestionsState.assessment_title,
                                on_change=TextQuestionsState.set_assessment_title,
                                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                            ),
                        ),
                        class_name="grid gap-4 mb-4",
                        style={"gridTemplateColumns": "0.7fr 0.5fr 2.8fr"},
                    ),
                    rx.cond(
                        ~TextQuestionsState.is_conversion_mode,
                        rx.el.div(
                            rx.el.h3(
                                "Content Type",
                                class_name="text-lg font-semibold text-gray-900 mb-2",
                            ),
                            rx.el.div(
                                rx.el.label(
                                    rx.el.input(
                                        type="radio",
                                        name="content_type",
                                        value="rm_q",
                                        checked=TextQuestionsState.content_type == "rm_q",
                                        on_change=TextQuestionsState.set_content_type,
                                        class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer",
                                    ),
                                    " Reading Material",
                                    class_name="flex items-center gap-2 text-gray-700",
                                ),
                                rx.el.label(
                                    rx.el.input(
                                        type="radio",
                                        name="content_type",
                                        value="siml_q",
                                        checked=TextQuestionsState.content_type == "siml_q",
                                        on_change=TextQuestionsState.set_content_type,
                                        class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer",
                                    ),
                                    " Paraphrase",
                                    class_name="flex items-center gap-2 text-gray-700",
                                ),
                                rx.el.label(
                                    rx.el.input(
                                        type="radio",
                                        name="content_type",
                                        value="diffr_q",
                                        checked=TextQuestionsState.content_type == "diffr_q",
                                        on_change=TextQuestionsState.set_content_type,
                                        class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer",
                                    ),
                                    " Different Content",
                                    class_name="flex items-center gap-2 text-gray-700",
                                ),
                                class_name="flex items-center gap-4",
                            ),
                            class_name="mb-4",
                        ),
                        rx.el.div(
                            rx.el.h3(
                                "Content Type",
                                class_name="text-lg font-semibold text-gray-900 mb-2",
                            ),
                            rx.el.p(
                                "Locked to conversion mode for this workflow.",
                                class_name="text-sm text-gray-600",
                            ),
                            class_name="mb-4",
                        ),
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Special Instructions", class_name="text-sm font-medium text-gray-700"
                        ),
                        rx.el.textarea(
                            default_value=TextQuestionsState.special_instructions,
                            on_change=TextQuestionsState.set_special_instructions,
                            placeholder="e.g., Focus on chapter 3.",
                            class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                            rows="2",
                        ),
                        class_name="mb-4",
                    ),
                    rx.cond(
                        ~TextQuestionsState.is_conversion_mode,
                        rx.fragment(
                            rx.el.h3(
                                "Question Types",
                                class_name="text-lg font-semibold text-gray-900 mb-3",
                            ),
                            rx.el.div(
                                rx.foreach(
                                    question_types,
                                    lambda qt: question_type_card(
                                        qt["icon"], qt["q_type"], qt["name"], qt["desc"]
                                    ),
                                ),
                                class_name="grid grid-cols-7 gap-2",
                            ),
                        ),
                        rx.el.div(
                            rx.el.p(
                                "Question counts are not used in conversion mode. "
                                "The app will convert all valid questions found in the uploaded PDF.",
                                class_name="text-sm text-gray-600",
                            ),
                            class_name="p-3 bg-gray-50 rounded-md border border-gray-200",
                        ),
                    ),
                    class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
                ),
                quick_model_switcher(
                    title="Model Selection",
                    selected_model=TextQuestionsState.active_model,
                    default_model=TextQuestionsState.default_model_snapshot,
                    openai_models=SettingsState.openai_models,
                    anthropic_models=SettingsState.anthropic_models,
                    gemini_models=SettingsState.gemini_models,
                    custom_models=SettingsState.custom_models,
                    on_select_handler=TextQuestionsState.select_active_model,
                    persist_choice=TextQuestionsState.persist_model_choice,
                    on_toggle_persist_handler=TextQuestionsState.toggle_persist_model_choice,
                    on_reset_handler=TextQuestionsState.reset_to_default_model,
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.cond(
                                TextQuestionsState.is_conversion_mode,
                                "Total Questions: Auto-detect from PDF",
                                f"Total Questions: {TextQuestionsState.calculated_total_questions}",
                            ),
                            class_name="text-lg font-semibold text-gray-900",
                        ),
                        rx.el.button(
                            rx.cond(
                                TextQuestionsState.generating,
                                rx.spinner(class_name="mr-2"),
                                None,
                            ),
                            rx.cond(
                                TextQuestionsState.is_conversion_mode,
                                "Convert Questions",
                                "Generate Questions",
                            ),
                            on_click=TextQuestionsState.handle_generate,
                            is_disabled=TextQuestionsState.generating
                            | (
                                ~TextQuestionsState.is_conversion_mode
                                & (TextQuestionsState.calculated_total_questions == 0)
                            )
                            | ~TextQuestionsState.preflight_ready,
                            class_name="flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400",
                        ),
                        class_name="flex items-center justify-between",
                    ),
                    rx.el.div(
                        rx.el.p("Preflight", class_name="text-sm font-semibold text-gray-700"),
                        rx.el.div(
                            rx.el.span(
                                rx.cond(TextQuestionsState.preflight_pdf_ready, "✅ PDF loaded", "❌ PDF missing"),
                                class_name="text-xs text-gray-700",
                            ),
                            rx.el.span(
                                rx.cond(TextQuestionsState.preflight_model_ready, "✅ Model selected", "❌ Model missing"),
                                class_name="text-xs text-gray-700",
                            ),
                            rx.el.span(
                                rx.cond(TextQuestionsState.preflight_api_key_ready, "✅ API key ready", "❌ API key missing"),
                                class_name="text-xs text-gray-700",
                            ),
                            rx.el.span(
                                rx.cond(TextQuestionsState.preflight_feature_ready, "✅ Model supports PDF", "❌ Model lacks PDF support"),
                                class_name="text-xs text-gray-700",
                            ),
                            class_name="mt-2 flex flex-wrap gap-3",
                        ),
                        class_name="mt-4 p-3 bg-gray-50 rounded-md border border-gray-200",
                    ),
                    rx.cond(
                        TextQuestionsState.generating,
                        rx.el.div(
                            rx.el.div(
                                f"{TextQuestionsState.progress}%",
                                class_name="text-sm font-medium text-blue-700",
                            ),
                            rx.el.div(
                                rx.el.div(
                                    class_name="bg-blue-600 h-2.5 rounded-full",
                                    style={
                                        "width": TextQuestionsState.progress.to(str) + "%"
                                    },
                                ),
                                class_name="w-full bg-gray-200 rounded-full h-2.5",
                            ),
                            class_name="w-full mt-4",
                        ),
                        None,
                    ),
                    rx.el.p(
                        rx.el.span(f"Stage: {TextQuestionsState.generation_stage}"),
                        rx.el.span(" | Active model:", class_name="ml-2"),
                        rx.el.span(
                            rx.cond(
                                TextQuestionsState.active_model != "",
                                TextQuestionsState.active_model,
                                rx.cond(
                                    TextQuestionsState.default_model_snapshot != "",
                                    TextQuestionsState.default_model_snapshot,
                                    "Not selected",
                                ),
                            ),
                            class_name="font-medium text-gray-700",
                        ),
                        class_name="mt-3 text-sm text-gray-600 flex flex-wrap items-center gap-1",
                    ),
                    rx.cond(
                        TextQuestionsState.error_message != "",
                        rx.el.div(
                            rx.el.div(
                                rx.icon(
                                    "flag_triangle_right", class_name="h-5 w-5 text-red-500"
                                ),
                                rx.el.span(
                                    TextQuestionsState.error_message,
                                    class_name="text-sm text-red-600",
                                ),
                                rx.el.button(
                                    "Retry",
                                    on_click=TextQuestionsState.handle_generate,
                                    is_disabled=TextQuestionsState.generating | ~TextQuestionsState.preflight_ready,
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
                                    TextQuestionsState.current_yaml,
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
                        TextQuestionsState.conversion_warning_message != "",
                        rx.el.div(
                            rx.el.div(
                                rx.icon("triangle-alert", class_name="h-5 w-5 text-amber-600"),
                                rx.el.span(
                                    TextQuestionsState.conversion_warning_message,
                                    class_name="text-sm text-amber-800",
                                ),
                                class_name="flex items-center gap-2",
                            ),
                            class_name="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200",
                        ),
                        None,
                    ),
                    rx.cond(
                        TextQuestionsState.package_ready,
                        rx.el.div(
                            rx.el.div(
                                rx.icon(
                                    "square_check", class_name="h-5 w-5 text-green-500"
                                ),
                                rx.el.span(
                                    rx.cond(
                                        TextQuestionsState.is_conversion_mode,
                                        "Conversion complete! You can now review your questions.",
                                        "Generation complete! You can now review your questions.",
                                    ),
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
                                    TextQuestionsState.question_summary,
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
                                    "Download Text-Only Package (.zip)",
                                    on_click=TextQuestionsState.download_text_package,
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
                                    on_click=TextQuestionsState.open_delete_package_modal,
                                    class_name="p-2 text-red-600 bg-white border border-red-300 rounded-md hover:bg-red-50",
                                    title="Delete all text questions",
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


text_questions_v0 = text_questions

__all__ = ["text_questions", "text_questions_v0"]
