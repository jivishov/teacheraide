import reflex as rx
from app.states.text_questions_state import TextQuestionsState


def question_type_card(
    icon: str, q_type: str, name: str, description: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="w-4 h-4 text-blue-600"),
            rx.el.h3(name, class_name="text-sm font-semibold text-gray-800"),
            class_name="flex items-center gap-1.5",
        ),
        rx.el.p(description, class_name="mt-1 text-xs text-gray-500 truncate"),
        rx.el.input(
            type="number",
            value=TextQuestionsState.question_counts[q_type].to(str),
            on_change=lambda val: TextQuestionsState.set_question_count(q_type, val),
            min=0,
            max=20,
            class_name="mt-2 w-full px-2 py-1.5 text-sm bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
        ),
        class_name="p-3 bg-white rounded-lg border border-gray-200 shadow-sm transition-all duration-200 hover:shadow-md hover:border-blue-300",
    )
