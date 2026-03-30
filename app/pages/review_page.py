import reflex as rx

from app.components.layout_components import nav_menu
from app.components.review_components import (
    question_summary_card,
    download_section,
    question_card_with_actions,
    delete_confirmation_modal,
    edit_question_modal,
    upload_questions_modal,
    upload_button,
    clear_all_modal,
)
from app.states.review_state import ReviewState


def review_download() -> rx.Component:
    return rx.fragment(
        delete_confirmation_modal(),
        edit_question_modal(),
        upload_questions_modal(),
        clear_all_modal(),
        nav_menu(),
        rx.el.main(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon("clipboard-check", class_name="w-5 h-5 text-blue-600 flex-shrink-0"),
                        rx.el.h1("Review & Download", class_name="text-xl font-bold text-gray-900"),
                        rx.el.span("·", class_name="text-gray-300"),
                        rx.el.span("Review questions and download packages", class_name="text-sm text-gray-500 truncate"),
                        class_name="flex items-center gap-2.5",
                    ),
                    rx.el.div(
                        upload_button(),
                        rx.el.button(
                            rx.icon("refresh-cw", class_name="mr-2 h-4 w-4"),
                            "Refresh",
                            on_click=ReviewState.refresh_data,
                            class_name="flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50",
                        ),
                        rx.el.button(
                            rx.icon("trash-2", class_name="mr-2 h-4 w-4"),
                            "Clear",
                            on_click=ReviewState.open_clear_all_modal,
                            class_name="flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700",
                        ),
                        class_name="flex items-center gap-2",
                    ),
                    class_name="flex items-center justify-between pb-4 border-b border-gray-200",
                ),
                rx.cond(
                    ReviewState.action_status_message != "",
                    rx.el.div(
                        rx.el.span(
                            ReviewState.action_status_message,
                            class_name=rx.cond(
                                ReviewState.action_status_type == "warning",
                                "text-sm font-medium text-amber-800",
                                "text-sm font-medium text-green-800",
                            ),
                        ),
                        rx.el.button(
                            "Dismiss",
                            on_click=ReviewState.clear_action_status,
                            class_name=rx.cond(
                                ReviewState.action_status_type == "warning",
                                "px-2 py-1 text-xs text-amber-700 bg-amber-100 rounded hover:bg-amber-200",
                                "px-2 py-1 text-xs text-green-700 bg-green-100 rounded hover:bg-green-200",
                            ),
                        ),
                        class_name=rx.cond(
                            ReviewState.action_status_type == "warning",
                            "mt-4 flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-md",
                            "mt-4 flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-md",
                        ),
                    ),
                    rx.fragment(),
                ),
                rx.el.div(
                    rx.el.div(
                        rx.cond(
                            ReviewState.filtered_questions_with_metadata.length() > 0,
                            rx.el.div(
                                rx.foreach(
                                    ReviewState.filtered_questions_with_metadata,
                                    lambda item, i: question_card_with_actions(item, i),
                                ),
                                class_name="space-y-4",
                            ),
                            rx.el.div(
                                rx.icon("inbox", class_name="w-12 h-12 text-gray-300 mx-auto"),
                                rx.el.h3("No questions yet", class_name="mt-4 text-lg font-medium text-gray-700"),
                                rx.el.p(
                                    "Generate questions from Text or Image pages, convert uploaded PDF question sets from Upload Material, or upload a previously generated QTI package.",
                                    class_name="mt-2 text-sm text-gray-500 text-center max-w-md",
                                ),
                                rx.el.div(
                                    rx.el.a(
                                        rx.el.button(
                                            rx.icon("file-text", class_name="mr-2 h-4 w-4"),
                                            "Text Questions",
                                            class_name="flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50",
                                        ),
                                        href="/text-questions",
                                    ),
                                    rx.el.a(
                                        rx.el.button(
                                            rx.icon("image", class_name="mr-2 h-4 w-4"),
                                            "Image Questions",
                                            class_name="flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700",
                                        ),
                                        href="/image-questions",
                                    ),
                                    class_name="mt-6 flex items-center gap-4",
                                ),
                                class_name="flex flex-col items-center justify-center py-16 bg-gray-50 rounded-lg border border-dashed border-gray-300",
                            ),
                        ),
                        class_name="col-span-12 lg:col-span-8",
                    ),
                    rx.el.div(
                        question_summary_card(),
                        download_section(),
                        class_name="col-span-12 lg:col-span-4 space-y-6",
                    ),
                    class_name="grid grid-cols-12 gap-6 mt-6",
                ),
                class_name="p-6",
            ),
            class_name="min-h-screen bg-gray-50 font-['Inter']",
        ),
    )
