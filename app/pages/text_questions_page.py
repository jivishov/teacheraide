"""Active Text Questions page backed by the V2 layout."""

import reflex as rx

from app.components.layout_components import nav_menu, page_header
from app.components.model_switch_components import model_chip_group
from app.states.settings_state import SettingsState
from app.states.text_questions_state import TextQuestionsState


_QUESTION_TYPES = [
    {
        "label": "MCQ",
        "icon": "list-checks",
        "description": "Select the single best answer from options",
        "q_type": "mcq",
    },
    {
        "label": "MRQ",
        "icon": "check-check",
        "description": "Select all correct answers from options",
        "q_type": "mrq",
    },
    {
        "label": "T/F",
        "icon": "toggle-right",
        "description": "Determine if a statement is true or false",
        "q_type": "tf",
    },
    {
        "label": "FIB",
        "icon": "pilcrow",
        "description": "Complete sentences with the correct word",
        "q_type": "fib",
    },
    {
        "label": "Essay",
        "icon": "pencil-ruler",
        "description": "Write a detailed paragraph-length answer",
        "q_type": "essay",
    },
    {
        "label": "Match",
        "icon": "shuffle",
        "description": "Connect related items from two columns",
        "q_type": "match",
    },
    {
        "label": "Order",
        "icon": "arrow-down-up",
        "description": "Arrange items in the correct order",
        "q_type": "order",
    },
]


def _generate_disabled() -> rx.Var[bool]:
    return (
        TextQuestionsState.generating
        | (
            ~TextQuestionsState.is_conversion_mode
            & (TextQuestionsState.calculated_total_questions == 0)
        )
        | ~TextQuestionsState.preflight_ready
    )


def text_delete_package_modal_v2() -> rx.Component:
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
                        rx.dialog.title(
                            "Delete Text Questions",
                            class_name="text-lg font-semibold text-gray-900",
                        ),
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


def _preset_chip(label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=TextQuestionsState.apply_v2_preset(label),
        class_name=rx.cond(
            TextQuestionsState.v2_active_preset == label,
            "px-3 py-1.5 text-sm font-semibold text-white bg-blue-600 border border-blue-600 rounded-full shadow-sm transition-colors",
            "px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-full hover:bg-blue-100 transition-colors",
        ),
    )


def _content_type_chip(value: str, label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=TextQuestionsState.set_v2_content_type(value),
        class_name=rx.cond(
            TextQuestionsState.content_type == value,
            "px-3 py-1.5 text-sm font-semibold text-white bg-slate-700 border border-slate-700 rounded-full shadow-sm transition-colors",
            "px-3 py-1.5 text-sm font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-full hover:bg-slate-100 transition-colors",
        ),
    )


def _selected_content_type_helper() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            rx.cond(
                TextQuestionsState.content_type == "rm_q",
                "Generate questions directly from the uploaded material.",
                rx.cond(
                    TextQuestionsState.content_type == "siml_q",
                    "Rewrite the material into a fresh set of questions.",
                    "Create new questions on the same topic using the material as context.",
                ),
            ),
            class_name="text-sm leading-5 text-slate-700",
        ),
        class_name="mt-3 flex min-h-[3.125rem] items-center rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 shadow-sm",
    )


def _mode_toggle() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            "Quick",
            on_click=TextQuestionsState.set_v2_ui_mode("quick"),
            class_name=rx.cond(
                TextQuestionsState.is_v2_quick_mode,
                "px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-l-lg transition-colors",
                "px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-l-lg transition-colors",
            ),
        ),
        rx.el.button(
            "Advanced",
            on_click=TextQuestionsState.set_v2_ui_mode("advanced"),
            class_name=rx.cond(
                ~TextQuestionsState.is_v2_quick_mode,
                "px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-r-lg transition-colors",
                "px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-r-lg transition-colors",
            ),
        ),
        class_name="flex h-10",
    )


def _stepper_row(
    label: str,
    icon: str,
    description: str,
    q_type: str,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="w-4 h-4 text-gray-500"),
                rx.el.span(label, class_name="text-sm font-semibold text-gray-800 ml-2"),
                class_name="flex items-center",
            ),
            rx.el.span(description, class_name="text-xs text-gray-500 ml-6 mt-0.5"),
            class_name="flex flex-col flex-1 min-w-0",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("minus", class_name="w-4 h-4"),
                on_click=TextQuestionsState.decrement_question_count(q_type),
                class_name="w-8 h-8 flex items-center justify-center text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-l-md border border-gray-300",
            ),
            rx.el.span(
                TextQuestionsState.question_counts[q_type].to(str),
                class_name="w-10 h-8 flex items-center justify-center text-sm font-semibold text-gray-900 bg-white border-t border-b border-gray-300",
            ),
            rx.el.button(
                rx.icon("plus", class_name="w-4 h-4"),
                on_click=TextQuestionsState.increment_question_count(q_type),
                class_name="w-8 h-8 flex items-center justify-center text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-r-md border border-gray-300",
            ),
            class_name="flex flex-shrink-0",
        ),
        class_name="flex items-center justify-between py-3",
    )


def _cognitive_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.el.span(
                        class_name="inline-block h-2.5 w-2.5 rounded-sm bg-green-400 mr-1.5"
                    ),
                    f"Basic {TextQuestionsState.cognitive_basic_percent}%",
                    class_name="inline-flex items-center text-xs text-gray-600",
                ),
                rx.el.span(
                    rx.el.span(
                        class_name="inline-block h-2.5 w-2.5 rounded-sm bg-yellow-400 mr-1.5"
                    ),
                    f"Intermediate {TextQuestionsState.cognitive_intermediate_percent}%",
                    class_name="inline-flex items-center text-xs text-gray-600",
                ),
                rx.el.span(
                    rx.el.span(
                        class_name="inline-block h-2.5 w-2.5 rounded-sm bg-red-400 mr-1.5"
                    ),
                    f"High {TextQuestionsState.cognitive_high_percent}%",
                    class_name="inline-flex items-center text-xs text-gray-600",
                ),
                class_name="flex flex-wrap items-center gap-x-4 gap-y-1",
            ),
            class_name="mb-1.5 flex items-center justify-end",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-2.5 bg-green-400 rounded-l-md",
                style={"width": TextQuestionsState.cognitive_basic_percent.to(str) + "%"},
                title="Basic",
            ),
            rx.el.div(
                class_name="h-2.5 bg-yellow-400",
                style={
                    "width": TextQuestionsState.cognitive_intermediate_percent.to(str)
                    + "%"
                },
                title="Intermediate",
            ),
            rx.el.div(
                class_name="h-2.5 bg-red-400 rounded-r-md",
                style={"width": TextQuestionsState.cognitive_high_percent.to(str) + "%"},
                title="High",
            ),
            class_name="flex w-full rounded-md overflow-hidden",
        ),
        class_name="mt-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 shadow-sm",
    )


def _cog_footer_strip() -> rx.Component:
    """Compact cognitive-distribution footer bar — shared by quick & advanced panels."""
    return rx.el.div(
        rx.el.span(
            "Cognitive Distribution",
            class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider flex-shrink-0",
        ),
        rx.el.div(
            rx.el.span(
                rx.el.span(class_name="inline-block h-2 w-2 rounded-sm bg-green-400 mr-1.5"),
                f"Basic {TextQuestionsState.cognitive_basic_percent}%",
                class_name="inline-flex items-center text-xs text-gray-500 whitespace-nowrap",
            ),
            rx.el.span(
                rx.el.span(class_name="inline-block h-2 w-2 rounded-sm bg-yellow-400 mr-1.5"),
                f"Intermediate {TextQuestionsState.cognitive_intermediate_percent}%",
                class_name="inline-flex items-center text-xs text-gray-500 whitespace-nowrap",
            ),
            rx.el.span(
                rx.el.span(class_name="inline-block h-2 w-2 rounded-sm bg-red-400 mr-1.5"),
                f"High {TextQuestionsState.cognitive_high_percent}%",
                class_name="inline-flex items-center text-xs text-gray-500 whitespace-nowrap",
            ),
            class_name="flex items-center gap-4 flex-shrink-0",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-2 bg-green-400 rounded-l-full",
                style={"width": TextQuestionsState.cognitive_basic_percent.to(str) + "%"},
                title="Basic",
            ),
            rx.el.div(
                class_name="h-2 bg-yellow-400",
                style={
                    "width": TextQuestionsState.cognitive_intermediate_percent.to(str) + "%"
                },
                title="Intermediate",
            ),
            rx.el.div(
                class_name="h-2 bg-red-400 rounded-r-full",
                style={"width": TextQuestionsState.cognitive_high_percent.to(str) + "%"},
                title="High",
            ),
            class_name="flex flex-1 rounded-full overflow-hidden",
        ),
        class_name="flex items-center gap-5 px-5 py-3 bg-gray-50 border-t border-gray-200",
    )


def _cognitive_bar_compact() -> rx.Component:
    """Cognitive bar without outer container — for use inside panel zones."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                rx.el.span(class_name="inline-block h-2.5 w-2.5 rounded-sm bg-green-400 mr-1.5"),
                f"Basic {TextQuestionsState.cognitive_basic_percent}%",
                class_name="inline-flex items-center text-xs text-gray-600",
            ),
            rx.el.span(
                rx.el.span(class_name="inline-block h-2.5 w-2.5 rounded-sm bg-yellow-400 mr-1.5"),
                f"Intermediate {TextQuestionsState.cognitive_intermediate_percent}%",
                class_name="inline-flex items-center text-xs text-gray-600",
            ),
            rx.el.span(
                rx.el.span(class_name="inline-block h-2.5 w-2.5 rounded-sm bg-red-400 mr-1.5"),
                f"High {TextQuestionsState.cognitive_high_percent}%",
                class_name="inline-flex items-center text-xs text-gray-600",
            ),
            class_name="flex flex-wrap items-center gap-x-3 gap-y-1 mb-2",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-2.5 bg-green-400 rounded-l-md",
                style={"width": TextQuestionsState.cognitive_basic_percent.to(str) + "%"},
                title="Basic",
            ),
            rx.el.div(
                class_name="h-2.5 bg-yellow-400",
                style={
                    "width": TextQuestionsState.cognitive_intermediate_percent.to(str) + "%"
                },
                title="Intermediate",
            ),
            rx.el.div(
                class_name="h-2.5 bg-red-400 rounded-r-md",
                style={"width": TextQuestionsState.cognitive_high_percent.to(str) + "%"},
                title="High",
            ),
            class_name="flex w-full rounded-md overflow-hidden",
        ),
    )


def _quick_mode_content() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Assessment Type",
                    class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-2",
                ),
                rx.el.div(
                    _preset_chip("Formative"),
                    _preset_chip("Summative"),
                    _preset_chip("Quick Check"),
                    _preset_chip("Homework"),
                    class_name="flex flex-wrap gap-1.5",
                ),
                class_name="px-5 py-4",
            ),
            _cog_footer_strip(),
            class_name="border border-gray-200 rounded-lg overflow-hidden mb-5",
        ),
        rx.el.div(
            rx.el.label(
                "Special Instructions", class_name="text-sm font-medium text-gray-700"
            ),
            rx.el.textarea(
                placeholder="e.g., Focus on chapter 3 concepts.",
                value=TextQuestionsState.special_instructions,
                on_change=TextQuestionsState.set_special_instructions,
                rows="2",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
        ),
    )


def _advanced_mode_header_controls() -> rx.Component:
    return rx.el.div(
        # Top: flex row — Assessment shrinks to chip width, Content gets the rest
        rx.el.div(
            # Left: Assessment type — takes its natural chip width, never wraps
            rx.el.div(
                rx.el.label(
                    "Assessment Type",
                    class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-2",
                ),
                rx.el.div(
                    _preset_chip("Formative"),
                    _preset_chip("Summative"),
                    _preset_chip("Quick Check"),
                    _preset_chip("Homework"),
                    class_name="flex gap-1.5",
                ),
                class_name="flex-shrink-0 px-5 py-4",
            ),
            rx.el.div(class_name="w-px self-stretch bg-gray-200"),
            # Right: Content type — gets all remaining space
            rx.cond(
                TextQuestionsState.is_conversion_mode,
                rx.el.div(
                    rx.icon("lock", class_name="w-4 h-4 text-gray-400 flex-shrink-0"),
                    rx.el.span(
                        "Conversion mode: fixed question-conversion behavior.",
                        class_name="text-sm text-gray-500",
                    ),
                    class_name="flex-1 flex items-center gap-2 px-5 py-4 bg-gray-50",
                ),
                rx.el.div(
                    rx.el.label(
                        "Content Type",
                        class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-2",
                    ),
                    rx.el.div(
                        _content_type_chip("rm_q", "From Material"),
                        _content_type_chip("siml_q", "Paraphrase"),
                        _content_type_chip("diffr_q", "New Topic"),
                        class_name="flex gap-1.5 mb-2",
                    ),
                    rx.el.p(
                        rx.cond(
                            TextQuestionsState.content_type == "rm_q",
                            "Generate questions directly from the uploaded material.",
                            rx.cond(
                                TextQuestionsState.content_type == "siml_q",
                                "Rewrite the material into a fresh set of questions.",
                                "Create new questions on the same topic using the material as context.",
                            ),
                        ),
                        class_name="text-xs text-gray-400 leading-relaxed",
                    ),
                    class_name="flex-1 px-5 py-4",
                ),
            ),
            class_name="flex items-stretch",
        ),
        # Bottom: cognitive distribution footer strip
        _cog_footer_strip(),
        class_name="border border-gray-200 rounded-lg overflow-hidden mb-5",
    )


def _advanced_mode_content() -> rx.Component:
    return rx.el.div(
        _advanced_mode_header_controls(),
        rx.cond(
            TextQuestionsState.is_conversion_mode,
            rx.el.div(
                rx.el.p(
                    "Question counts are not used in conversion mode. The app will convert all valid questions found in the uploaded PDF.",
                    class_name="text-sm text-gray-600",
                ),
                class_name="p-3 bg-gray-50 rounded-md border border-gray-200",
            ),
            rx.fragment(
                rx.el.h3(
                    "Question Types", class_name="text-base font-semibold text-gray-900 mb-3"
                ),
                rx.el.div(
                    rx.foreach(
                        _QUESTION_TYPES,
                        lambda question_type: _stepper_row(
                            question_type["label"],
                            question_type["icon"],
                            question_type["description"],
                            question_type["q_type"],
                        ),
                    ),
                    class_name="divide-y divide-gray-100",
                ),
            ),
        ),
        rx.el.div(
            rx.el.label(
                "Special Instructions", class_name="text-sm font-medium text-gray-700"
            ),
            rx.el.textarea(
                placeholder="e.g., Focus on chapter 3 concepts.",
                value=TextQuestionsState.special_instructions,
                on_change=TextQuestionsState.set_special_instructions,
                rows="2",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
            class_name="mt-5",
        ),
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
                TextQuestionsState.v2_active_model_display,
                class_name="text-xs font-medium text-gray-800 bg-gray-50 px-2 py-1 rounded border border-gray-200",
            ),
            rx.el.button(
                "change",
                on_click=TextQuestionsState.toggle_model_picker,
                class_name="ml-2 text-xs text-blue-600 hover:text-blue-800 underline underline-offset-2 cursor-pointer",
            ),
            class_name="flex items-center",
        ),
        # ---- center: ready-to-go dots ----
        rx.el.div(
            rx.el.span("Ready to go", class_name="text-xs font-medium text-gray-500 uppercase tracking-wider mr-2"),
            rx.el.div(
                _ready_dot_with_label("PDF loaded", TextQuestionsState.preflight_pdf_ready),
                _ready_dot_with_label("Model selected", TextQuestionsState.preflight_model_ready),
                _ready_dot_with_label("API key ready", TextQuestionsState.preflight_api_key_ready),
                _ready_dot_with_label("Model supports PDF", TextQuestionsState.preflight_feature_ready),
                class_name="flex items-center gap-2.5",
            ),
            class_name="flex items-center",
        ),
        # ---- right: generate button ----
        rx.el.button(
            rx.cond(
                TextQuestionsState.generating,
                rx.el.span(
                    rx.icon("loader-circle", class_name="w-4 h-4 animate-spin mr-2 inline-block"),
                    "Generating...",
                ),
                rx.cond(
                    TextQuestionsState.is_conversion_mode,
                    "Convert Questions",
                    "Generate Questions",
                ),
            ),
            on_click=TextQuestionsState.handle_generate,
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
        TextQuestionsState.model_picker_open,
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    rx.cond(
                        TextQuestionsState.persist_model_choice,
                        "Use as default: On",
                        "Use as default: Off",
                    ),
                    on_click=TextQuestionsState.toggle_persist_model_choice,
                    type="button",
                    class_name=rx.cond(
                        TextQuestionsState.persist_model_choice,
                        "px-3 py-1.5 text-xs rounded-md bg-blue-100 text-blue-800 border border-blue-300",
                        "px-3 py-1.5 text-xs rounded-md bg-gray-100 text-gray-700 border border-gray-300",
                    ),
                ),
                rx.el.button(
                    "Reset to default",
                    on_click=TextQuestionsState.reset_to_default_model,
                    type="button",
                    class_name="px-3 py-1.5 text-xs rounded-md bg-white text-gray-700 border border-gray-300 hover:bg-gray-50",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                model_chip_group(
                    "OpenAI",
                    SettingsState.openai_models,
                    TextQuestionsState.active_model,
                    TextQuestionsState.select_active_model,
                ),
                model_chip_group(
                    "Anthropic",
                    SettingsState.anthropic_models,
                    TextQuestionsState.active_model,
                    TextQuestionsState.select_active_model,
                ),
                model_chip_group(
                    "Gemini",
                    SettingsState.gemini_models,
                    TextQuestionsState.active_model,
                    TextQuestionsState.select_active_model,
                ),
                model_chip_group(
                    "Custom",
                    SettingsState.custom_models,
                    TextQuestionsState.active_model,
                    TextQuestionsState.select_active_model,
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
        TextQuestionsState.generating,
        rx.el.div(
            rx.el.div(
                f"{TextQuestionsState.progress}%",
                class_name="text-xs font-medium text-blue-700 mb-1",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="bg-blue-600 h-2 rounded-full transition-all",
                    style={"width": TextQuestionsState.progress.to(str) + "%"},
                ),
                class_name="w-full bg-gray-200 rounded-full h-2 overflow-hidden",
            ),
            rx.el.p(
                TextQuestionsState.generation_stage,
                class_name="text-xs text-gray-500 mt-1",
            ),
            class_name="mt-3",
        ),
        rx.fragment(),
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
                    rx.el.option(
                        "PLTW Medical Interventions", value="PLTW Medical Interventions"
                    ),
                    value=TextQuestionsState.selected_subject,
                    on_change=TextQuestionsState.set_selected_subject,
                    class_name="mt-1 h-10 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
            ),
            rx.el.div(
                rx.el.label(
                    "Assessment Title", class_name="text-sm font-medium text-gray-700"
                ),
                rx.el.input(
                    placeholder="e.g., Biology Chapter 5 Quiz",
                    value=TextQuestionsState.assessment_title,
                    on_change=TextQuestionsState.set_assessment_title,
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
            TextQuestionsState.is_v2_quick_mode,
            _quick_mode_content(),
            _advanced_mode_content(),
        ),
        _action_bar(),
        _inline_model_picker(),
        _inline_progress(),
        class_name="flex-1 min-w-0 p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
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


def _sidebar() -> rx.Component:
    disabled = _generate_disabled()
    return rx.el.div(
        # Total Questions
        rx.el.div(
            rx.el.span("TOTAL QUESTIONS", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
            rx.el.span(
                TextQuestionsState.calculated_total_questions.to(str),
                class_name="text-3xl font-bold text-gray-900 mt-1",
            ),
            class_name="flex flex-col items-center text-center pb-4 border-b border-gray-200",
        ),
        # Profile badge
        rx.el.div(
            rx.el.span("PROFILE", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
            rx.el.span(
                TextQuestionsState.v2_active_preset,
                class_name="mt-1 inline-block px-3 py-1 text-sm font-semibold text-blue-700 bg-blue-50 border border-blue-200 rounded-full",
            ),
            class_name="flex flex-col items-center text-center py-4 border-b border-gray-200",
        ),
        # Model badge
        rx.el.div(
            rx.el.span("MODEL", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
            rx.el.span(
                TextQuestionsState.v2_active_model_display,
                class_name="mt-1 inline-block px-3 py-1 text-sm font-medium text-gray-800 bg-gray-50 border border-gray-200 rounded-full",
            ),
            class_name="flex flex-col items-center text-center py-4 border-b border-gray-200",
        ),
        # Ready to go checklist
        rx.el.div(
            rx.el.span("READY TO GO", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2"),
            _checklist_item(TextQuestionsState.preflight_pdf_ready, "PDF loaded"),
            _checklist_item(TextQuestionsState.preflight_model_ready, "Model selected"),
            _checklist_item(TextQuestionsState.preflight_api_key_ready, "API key ready"),
            _checklist_item(TextQuestionsState.preflight_feature_ready, "Supports PDF"),
            class_name="flex flex-col gap-1.5 py-4 border-b border-gray-200",
        ),
        # Generate button
        rx.el.button(
            rx.cond(
                TextQuestionsState.generating,
                rx.el.span(
                    rx.icon("loader-circle", class_name="w-4 h-4 animate-spin mr-2 inline-block"),
                    "Generating…",
                ),
                "Generate Questions",
            ),
            on_click=TextQuestionsState.handle_generate,
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
            TextQuestionsState.error_message != "",
            rx.el.div(
                rx.el.div(
                    rx.icon("flag_triangle_right", class_name="h-5 w-5 text-red-500"),
                    rx.el.span(
                        TextQuestionsState.error_message,
                        class_name="text-sm text-red-600",
                    ),
                    rx.el.button(
                        "Retry",
                        on_click=TextQuestionsState.handle_generate,
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
                        TextQuestionsState.current_yaml,
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
            rx.fragment(),
        ),
        rx.cond(
            TextQuestionsState.package_ready,
            rx.el.div(
                rx.el.div(
                    rx.icon("square_check", class_name="h-5 w-5 text-green-500"),
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
            rx.fragment(),
        ),
        class_name="max-w-7xl mx-auto mt-6 space-y-4",
    )


def text_questions_v2() -> rx.Component:
    return rx.fragment(
        text_delete_package_modal_v2(),
        nav_menu(),
        rx.el.main(
            rx.el.div(
                page_header("file-text", "Text Questions", ""),
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
                                "This run extracts existing questions from the uploaded PDF into YAML and QTI. Question counts are auto-detected from the source file.",
                                class_name="text-xs text-emerald-700",
                            ),
                        ),
                        class_name="max-w-7xl mx-auto flex items-start gap-3 p-3 bg-emerald-50 rounded-md border border-emerald-200",
                    ),
                    rx.fragment(),
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


text_questions = text_questions_v2

__all__ = ["text_questions", "text_questions_v2"]
