"""Pure-UI mock of the proposed decluttered Text Questions layout.

Route: /text-questions-mock
No state bindings — all values are hardcoded for visual preview.
"""

import reflex as rx

from app.components.layout_components import nav_menu


# ---------------------------------------------------------------------------
# Helpers — static chips / buttons (no event handlers)
# ---------------------------------------------------------------------------

def _mock_preset_chip(label: str, active: bool = False) -> rx.Component:
    if active:
        cls = "px-3 py-1.5 text-sm font-semibold text-white bg-blue-600 border border-blue-600 rounded-full shadow-sm"
    else:
        cls = "px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-full hover:bg-blue-100"
    return rx.el.button(label, class_name=cls)


def _mock_mode_toggle(active: str = "quick") -> rx.Component:
    q_cls = (
        "px-4 py-1.5 text-sm font-semibold text-white bg-blue-600 rounded-l-lg"
        if active == "quick"
        else "px-4 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-l-lg"
    )
    a_cls = (
        "px-4 py-1.5 text-sm font-semibold text-white bg-blue-600 rounded-r-lg"
        if active == "advanced"
        else "px-4 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-r-lg"
    )
    return rx.el.div(
        rx.el.button("Quick", class_name=q_cls),
        rx.el.button("Advanced", class_name=a_cls),
        class_name="flex",
    )


def _ready_dot(ok: bool, label: str) -> rx.Component:
    color = "bg-green-500" if ok else "bg-red-400"
    return rx.el.span(
        class_name=f"w-2.5 h-2.5 rounded-full {color} inline-block cursor-help",
        title=label,
    )


# ---------------------------------------------------------------------------
# Page header — no subtitle
# ---------------------------------------------------------------------------

def _mock_page_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("file-text", class_name="w-5 h-5 text-blue-600 flex-shrink-0"),
            rx.el.h1("Text Questions", class_name="text-xl font-bold text-gray-900"),
            class_name="flex items-center gap-2.5",
        ),
        class_name="pb-4 border-b border-gray-200",
    )


# ---------------------------------------------------------------------------
# Action bar — model pill + ready-to-go dots + Generate button
# ---------------------------------------------------------------------------

def _mock_action_bar() -> rx.Component:
    return rx.el.div(
        # ---- left: model indicator ----
        rx.el.div(
            rx.el.span("Model", class_name="text-xs font-medium text-gray-500 uppercase tracking-wider mr-2"),
            rx.el.span(
                "gpt-5.4",
                class_name="text-xs font-medium text-gray-800 bg-gray-50 px-2 py-1 rounded border border-gray-200",
            ),
            rx.el.button(
                "change",
                class_name="ml-2 text-xs text-blue-600 hover:text-blue-800 underline underline-offset-2",
            ),
            class_name="flex items-center",
        ),
        # ---- center: ready-to-go dots ----
        rx.el.div(
            rx.el.span("Ready to go", class_name="text-xs font-medium text-gray-500 uppercase tracking-wider mr-2"),
            rx.el.div(
                _ready_dot(False, "PDF loaded"),
                _ready_dot(True, "Model selected"),
                _ready_dot(True, "API key ready"),
                _ready_dot(True, "Model supports PDF"),
                class_name="flex items-center gap-1.5",
            ),
            class_name="flex items-center",
        ),
        # ---- right: generate button ----
        rx.el.button(
            "Generate Questions",
            class_name="py-2.5 px-5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors cursor-pointer",
        ),
        class_name="flex items-center justify-between pt-5 mt-5 border-t border-gray-200",
    )


# ---------------------------------------------------------------------------
# Quick-mode content
# ---------------------------------------------------------------------------

def _mock_quick_content() -> rx.Component:
    return rx.el.div(
        # Quick Presets chips + inline estimate
        rx.el.div(
            rx.el.div(
                rx.el.label("Quick Presets", class_name="text-sm font-medium text-gray-700 block mb-2"),
                rx.el.div(
                    _mock_preset_chip("Formative", active=True),
                    _mock_preset_chip("Summative"),
                    _mock_preset_chip("Quick Check"),
                    _mock_preset_chip("Homework"),
                    class_name="flex flex-wrap gap-2",
                ),
            ),
            rx.el.span(
                "~10 questions, mixed difficulty",
                class_name="text-sm text-gray-500 italic self-end",
            ),
            class_name="flex items-end justify-between mb-5",
        ),
        # Cognitive Distribution bar
        _mock_cognitive_bar(),
        # Special Instructions
        rx.el.div(
            rx.el.label(
                "Special Instructions", class_name="text-sm font-medium text-gray-700"
            ),
            rx.el.textarea(
                placeholder="e.g., Focus on chapter 3 concepts.",
                rows="2",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
            class_name="mt-4",
        ),
    )


# ---------------------------------------------------------------------------
# Advanced-mode content (stepper rows, cognitive bar, content type)
# ---------------------------------------------------------------------------

_QUESTION_TYPES = [
    ("MCQ", "list-checks", "Select the single best answer from options", 4),
    ("MRQ", "check-check", "Select all correct answers from options", 2),
    ("T/F", "toggle-right", "Determine if a statement is true or false", 2),
    ("FIB", "pilcrow", "Complete sentences with the correct word", 1),
    ("Essay", "pencil-ruler", "Write a detailed paragraph-length answer", 1),
    ("Match", "shuffle", "Connect related items from two columns", 0),
    ("Order", "arrow-down-up", "Arrange items in the correct order", 0),
]


def _mock_stepper_row(label: str, icon: str, desc: str, count: int) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="w-4 h-4 text-gray-500"),
                rx.el.span(label, class_name="text-sm font-semibold text-gray-800 ml-2"),
                class_name="flex items-center",
            ),
            rx.el.span(desc, class_name="text-xs text-gray-500 ml-6 mt-0.5"),
            class_name="flex flex-col flex-1 min-w-0",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("minus", class_name="w-4 h-4"),
                class_name="w-8 h-8 flex items-center justify-center text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-l-md border border-gray-300",
            ),
            rx.el.span(
                str(count),
                class_name="w-10 h-8 flex items-center justify-center text-sm font-semibold text-gray-900 bg-white border-t border-b border-gray-300",
            ),
            rx.el.button(
                rx.icon("plus", class_name="w-4 h-4"),
                class_name="w-8 h-8 flex items-center justify-center text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-r-md border border-gray-300",
            ),
            class_name="flex flex-shrink-0",
        ),
        class_name="flex items-center justify-between py-3",
    )


def _mock_cognitive_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label("Cognitive Distribution", class_name="text-sm font-medium text-gray-700"),
            rx.el.div(
                rx.el.span(
                    rx.el.span(class_name="inline-block h-2.5 w-2.5 rounded-sm bg-green-400 mr-1.5"),
                    "Basic 40%",
                    class_name="inline-flex items-center text-xs text-gray-600",
                ),
                rx.el.span(
                    rx.el.span(class_name="inline-block h-2.5 w-2.5 rounded-sm bg-yellow-400 mr-1.5"),
                    "Intermediate 40%",
                    class_name="inline-flex items-center text-xs text-gray-600",
                ),
                rx.el.span(
                    rx.el.span(class_name="inline-block h-2.5 w-2.5 rounded-sm bg-red-400 mr-1.5"),
                    "High 20%",
                    class_name="inline-flex items-center text-xs text-gray-600",
                ),
                class_name="flex flex-wrap items-center gap-x-4 gap-y-1",
            ),
            class_name="mb-1.5 flex flex-col gap-1 md:flex-row md:items-center md:justify-between",
        ),
        rx.el.div(
            rx.el.div(class_name="h-2.5 bg-green-400 rounded-l-md", style={"width": "40%"}),
            rx.el.div(class_name="h-2.5 bg-yellow-400", style={"width": "40%"}),
            rx.el.div(class_name="h-2.5 bg-red-400 rounded-r-md", style={"width": "20%"}),
            class_name="flex w-full rounded-md overflow-hidden",
        ),
        class_name="mt-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 shadow-sm",
    )


def _mock_content_type_chip(label: str, active: bool = False) -> rx.Component:
    if active:
        cls = "px-3 py-1.5 text-sm font-semibold text-white bg-slate-700 border border-slate-700 rounded-full shadow-sm"
    else:
        cls = "px-3 py-1.5 text-sm font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-full hover:bg-slate-100"
    return rx.el.button(label, class_name=cls)


def _mock_advanced_content() -> rx.Component:
    return rx.el.div(
        # Header controls: presets + content type
        rx.el.div(
            rx.el.div(
                rx.el.label("Quick Presets", class_name="text-sm font-medium text-gray-700 block mb-2"),
                rx.el.div(
                    _mock_preset_chip("Formative", active=True),
                    _mock_preset_chip("Summative"),
                    _mock_preset_chip("Quick Check"),
                    _mock_preset_chip("Homework"),
                    class_name="flex flex-wrap gap-2",
                ),
                _mock_cognitive_bar(),
                class_name="min-w-0 md:flex-1",
            ),
            rx.el.div(class_name="hidden md:block w-px self-stretch bg-gray-200"),
            rx.el.div(
                rx.el.label("Content Type", class_name="text-sm font-medium text-gray-700 block mb-2"),
                rx.el.div(
                    _mock_content_type_chip("From Material", active=True),
                    _mock_content_type_chip("Paraphrase"),
                    _mock_content_type_chip("New Topic"),
                    class_name="flex flex-wrap gap-2",
                ),
                rx.el.div(
                    rx.el.p(
                        "Generate questions directly from the uploaded material.",
                        class_name="text-sm leading-5 text-slate-700",
                    ),
                    class_name="mt-3 flex min-h-[3.125rem] items-center rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 shadow-sm",
                ),
                class_name="min-w-0 md:flex-1",
            ),
            class_name="flex flex-col gap-4 md:flex-row md:items-start md:gap-5 mb-5",
        ),
        # Question Types
        rx.el.h3("Question Types", class_name="text-base font-semibold text-gray-900 mb-3"),
        rx.el.div(
            *[_mock_stepper_row(*qt) for qt in _QUESTION_TYPES],
            class_name="divide-y divide-gray-100",
        ),
        # Special Instructions
        rx.el.div(
            rx.el.label("Special Instructions", class_name="text-sm font-medium text-gray-700"),
            rx.el.textarea(
                placeholder="e.g., Focus on chapter 3 concepts.",
                rows="2",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
            class_name="mt-5",
        ),
    )


# ---------------------------------------------------------------------------
# Main card — single card with action bar at bottom
# ---------------------------------------------------------------------------

def _mock_main_card(mode: str = "quick") -> rx.Component:
    content = _mock_quick_content() if mode == "quick" else _mock_advanced_content()
    return rx.el.div(
        # Top controls row
        rx.el.div(
            rx.el.div(
                rx.el.label("Subject", class_name="text-sm font-medium text-gray-700"),
                rx.el.select(
                    rx.el.option("Biology", value="Biology"),
                    rx.el.option("Chemistry", value="Chemistry"),
                    rx.el.option("Physics", value="Physics"),
                    rx.el.option("Math", value="Math"),
                    value="Biology",
                    class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
            ),
            rx.el.div(
                rx.el.label("Assessment Title", class_name="text-sm font-medium text-gray-700"),
                rx.el.input(
                    placeholder="e.g., Biology Chapter 5 Quiz",
                    value="TeacherAIde Text Assessment",
                    class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
            ),
            rx.el.div(
                rx.el.label("Mode", class_name="text-sm font-medium text-gray-700 block mb-1"),
                _mock_mode_toggle(active=mode),
            ),
            class_name="grid grid-cols-[0.7fr_2fr_auto] gap-4 mb-6",
        ),
        rx.el.hr(class_name="border-gray-200 mb-5"),
        # Mode content
        content,
        # Action bar at bottom
        _mock_action_bar(),
        class_name="flex-1 p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


# ---------------------------------------------------------------------------
# Mock success banner (shown after generation — for reference)
# ---------------------------------------------------------------------------

def _mock_success_banner() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("square-check", class_name="h-5 w-5 text-green-500"),
            rx.el.span(
                "Generation complete! You can now review your questions.",
                class_name="text-sm text-green-600 font-medium",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.h4("Question Summary", class_name="text-md font-semibold text-gray-800 mt-4 mb-2"),
        rx.el.div(
            *[
                rx.el.div(
                    rx.el.span(t, class_name="text-xs font-medium text-gray-500"),
                    rx.el.span(str(c), class_name="text-base font-bold text-gray-900"),
                    class_name="flex flex-col items-center justify-center p-1.5 bg-gray-50 rounded-md border",
                )
                for t, c in [("MCQ", 4), ("MRQ", 2), ("T/F", 2), ("FIB", 1), ("Essay", 1), ("Match", 0), ("Order", 0)]
            ],
            class_name="grid grid-cols-7 gap-2",
        ),
        rx.el.div(
            rx.el.button(
                "Download Text-Only Package (.zip)",
                class_name="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700",
            ),
            rx.el.button(
                "Review All Questions",
                rx.icon("arrow-right", class_name="ml-2 w-4 h-4"),
                class_name="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 inline-flex items-center justify-center",
            ),
            class_name="flex gap-4 mt-4 items-center",
        ),
        class_name="max-w-7xl mx-auto mt-6 p-4 bg-green-50 rounded-lg border border-green-200",
    )


# ---------------------------------------------------------------------------
# Sidebar — static summary panel
# ---------------------------------------------------------------------------

def _mock_checklist_item(ok: bool, label: str) -> rx.Component:
    icon_cls = "w-4 h-4 text-green-500" if ok else "w-4 h-4 text-red-400"
    icon_name = "check" if ok else "x"
    text_cls = "text-sm text-gray-700" if ok else "text-sm text-red-500"
    return rx.el.div(
        rx.icon(icon_name, class_name=icon_cls),
        rx.el.span(label, class_name=text_cls),
        class_name="flex items-center gap-2",
    )


def _mock_sidebar() -> rx.Component:
    return rx.el.div(
        # Total Questions
        rx.el.div(
            rx.el.span("TOTAL QUESTIONS", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
            rx.el.span("10", class_name="text-3xl font-bold text-gray-900 mt-1"),
            class_name="flex flex-col items-center text-center pb-4 border-b border-gray-200",
        ),
        # Profile badge
        rx.el.div(
            rx.el.span("PROFILE", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
            rx.el.span(
                "Formative",
                class_name="mt-1 inline-block px-3 py-1 text-sm font-semibold text-blue-700 bg-blue-50 border border-blue-200 rounded-full",
            ),
            class_name="flex flex-col items-center text-center py-4 border-b border-gray-200",
        ),
        # Model badge
        rx.el.div(
            rx.el.span("MODEL", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
            rx.el.span(
                "gpt-5.4",
                class_name="mt-1 inline-block px-3 py-1 text-sm font-medium text-gray-800 bg-gray-50 border border-gray-200 rounded-full",
            ),
            class_name="flex flex-col items-center text-center py-4 border-b border-gray-200",
        ),
        # Ready to Go checklist
        rx.el.div(
            rx.el.span("READY TO GO", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2"),
            _mock_checklist_item(False, "PDF loaded"),
            _mock_checklist_item(True, "Model selected"),
            _mock_checklist_item(True, "API key ready"),
            _mock_checklist_item(True, "Supports PDF"),
            class_name="flex flex-col gap-1.5 py-4 border-b border-gray-200",
        ),
        # Generate button
        rx.el.button(
            "Generate Questions",
            class_name="mt-4 w-full py-2.5 px-5 text-sm font-semibold text-white bg-gray-400 rounded-lg shadow-sm cursor-not-allowed",
        ),
        class_name="w-full lg:w-72 flex-shrink-0 p-4 bg-white rounded-xl border border-gray-200 shadow-sm h-fit lg:sticky lg:top-20",
    )


# ---------------------------------------------------------------------------
# Full page
# ---------------------------------------------------------------------------

def text_questions_mock() -> rx.Component:
    return rx.fragment(
        nav_menu(),
        rx.el.main(
            rx.el.div(
                _mock_page_header(),
                # Section label
                rx.el.p(
                    "Quick Mode",
                    class_name="mt-6 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-widest",
                ),
                # Quick mode — card + sidebar in flex row
                rx.el.div(
                    _mock_main_card(mode="quick"),
                    _mock_sidebar(),
                    class_name="flex flex-col lg:flex-row gap-6 max-w-7xl mx-auto",
                ),

                # Divider between the two previews
                rx.el.div(
                    rx.el.hr(class_name="border-gray-300"),
                    rx.el.p(
                        "Advanced Mode (same card, different content)",
                        class_name="mt-6 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-widest",
                    ),
                    class_name="mt-10",
                ),
                # Advanced mode — card + sidebar in flex row
                rx.el.div(
                    _mock_main_card(mode="advanced"),
                    _mock_sidebar(),
                    class_name="flex flex-col lg:flex-row gap-6 max-w-7xl mx-auto",
                ),

                # Example success banner
                rx.el.div(
                    rx.el.hr(class_name="border-gray-300"),
                    rx.el.p(
                        "Success banner (appears only after generation)",
                        class_name="mt-6 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-widest",
                    ),
                    class_name="mt-10",
                ),
                _mock_success_banner(),

                class_name="p-6 space-y-0",
            ),
            class_name="min-h-screen bg-gray-50 font-['Inter']",
        ),
    )
