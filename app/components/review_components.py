import reflex as rx
from app.states.review_state import ReviewState, Question, QuestionWithMetadata, Choice, OrderItem, MatchPair, FIBAnswer


def question_summary_card() -> rx.Component:
    return rx.el.div(
        rx.el.h3("Question Summary", class_name="text-lg font-semibold text-gray-900"),
        rx.el.div(
            rx.foreach(
                ReviewState.question_summary.entries(),
                lambda item: rx.el.div(
                    rx.el.span(item[0], class_name="text-sm font-medium text-gray-600"),
                    rx.el.span(
                        item[1], class_name="text-sm font-semibold text-gray-900"
                    ),
                    class_name="flex items-center justify-between",
                ),
            ),
            class_name="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-2 mt-4",
        ),
        class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def download_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                "Assessment Title", class_name="text-sm font-medium text-gray-700"
            ),
            rx.el.input(
                default_value=ReviewState.title,
                on_change=ReviewState.set_title,
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.p(
                f"{ReviewState.total_questions} questions ready for download",
                class_name="text-sm text-gray-600 mb-4",
            )
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("cloud_download", class_name="mr-2"),
                "QTI Package (.zip)",
                on_click=ReviewState.download_qti,
                class_name="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
            ),
            rx.el.button(
                rx.icon("file-text", class_name="mr-2"),
                "Quiz Paper (.docx)",
                on_click=ReviewState.download_docx,
                class_name="mt-3 w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
            ),
            class_name="",
        ),
        class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def _render_mcq_mrq(question: Question) -> rx.Component:
    """Render MCQ or MRQ question choices."""
    return rx.el.div(
        rx.foreach(
            question["choices"],
            lambda choice: rx.el.div(
                rx.cond(
                    question["correct"].contains(choice["id"]),
                    rx.icon("square-check", class_name="h-5 w-5 text-green-500 flex-shrink-0"),
                    rx.icon("circle", class_name="h-5 w-5 text-gray-300 flex-shrink-0"),
                ),
                rx.el.span(
                    f"{choice['id']}. {choice['text']}",
                    class_name="ml-2 text-gray-800",
                ),
                class_name="flex items-center mt-2",
            ),
        ),
        class_name="mt-4",
    )


def _render_tf(question: Question) -> rx.Component:
    """Render True/False question choices (without redundant ID)."""
    return rx.el.div(
        rx.foreach(
            question["choices"],
            lambda choice: rx.el.div(
                rx.cond(
                    question["correct"].contains(choice["id"]),
                    rx.icon("square-check", class_name="h-5 w-5 text-green-500 flex-shrink-0"),
                    rx.icon("circle", class_name="h-5 w-5 text-gray-300 flex-shrink-0"),
                ),
                rx.el.span(
                    choice["text"],  # Only show text, not ID
                    class_name="ml-2 text-gray-800",
                ),
                class_name="flex items-center mt-2",
            ),
        ),
        class_name="mt-4",
    )


def _render_order(question: Question) -> rx.Component:
    """Render Order question with correct sequence."""
    return rx.el.div(
        rx.el.p("Correct Order:", class_name="text-sm font-semibold text-gray-700 mt-3 mb-2"),
        rx.foreach(
            question["correct_order"],
            lambda order_id, idx: rx.el.div(
                rx.el.span(
                    f"{idx + 1}.",
                    class_name="font-bold text-blue-600 w-6 flex-shrink-0",
                ),
                rx.el.span(
                    # Find the text for this order_id from order_items
                    rx.foreach(
                        question["order_items"],
                        lambda item: rx.cond(
                            item["id"] == order_id,
                            rx.el.span(item["text"]),
                            rx.fragment(),
                        ),
                    ),
                    class_name="ml-2 text-gray-800 bg-blue-50 px-3 py-1 rounded-md",
                ),
                class_name="flex items-center mt-2",
            ),
        ),
        class_name="mt-2",
    )


def _render_fib(question: Question) -> rx.Component:
    """Render Fill in Blank question with prompt and answers."""
    return rx.el.div(
        # Show prompt with blanks
        rx.cond(
            question["prompt_with_blanks"] != "",
            rx.el.div(
                rx.el.p("Prompt with blanks:", class_name="text-sm font-semibold text-gray-700 mt-3 mb-2"),
                rx.el.p(
                    question["prompt_with_blanks"],
                    class_name="text-gray-800 bg-gray-50 p-3 rounded-md border",
                ),
            ),
            rx.fragment(),
        ),
        # Show correct answers
        rx.el.p("Correct Answers:", class_name="text-sm font-semibold text-gray-700 mt-3 mb-2"),
        rx.foreach(
            question["fib_answers"],
            lambda ans: rx.el.div(
                rx.el.span(
                    f"Blank {ans['blank_num']}:",
                    class_name="font-medium text-gray-600 mr-2",
                ),
                rx.el.span(
                    rx.foreach(
                        ans["answers"],
                        lambda a, i: rx.fragment(
                            rx.cond(
                                i > 0,
                                rx.el.span(", ", class_name="text-gray-400"),
                                rx.fragment(),
                            ),
                            rx.el.span(a, class_name="text-green-700 font-medium"),
                        ),
                    ),
                ),
                class_name="flex items-center mt-1 bg-green-50 px-3 py-1 rounded-md",
            ),
        ),
        class_name="mt-2",
    )


def _render_essay(question: Question) -> rx.Component:
    """Render Essay question with expected length info."""
    return rx.el.div(
        rx.el.div(
            rx.el.span("Expected Length:", class_name="text-sm font-semibold text-gray-700"),
            rx.el.span(
                f" {question['expected_lines']} lines",
                class_name="text-gray-600",
            ),
            class_name="mt-3",
        ),
        rx.el.div(
            rx.el.textarea(
                placeholder="Student answer area (preview only)",
                disabled=True,
                class_name="w-full mt-2 p-3 bg-gray-50 border border-gray-200 rounded-md text-gray-400 resize-none",
                rows=rx.cond(question["expected_lines"] > 0, question["expected_lines"], 5),
            ),
        ),
        class_name="mt-2",
    )


def _render_numeric(question: Question) -> rx.Component:
    """Render Numeric question answer preview."""
    return rx.el.div(
        rx.el.div(
            rx.el.span("Correct Answer:", class_name="text-sm font-semibold text-gray-700"),
            rx.el.span(
                f" {question['numeric_answer']}",
                class_name="text-green-700 font-medium",
            ),
            class_name="mt-3",
        ),
        rx.el.div(
            rx.el.span("Expected Length:", class_name="text-sm font-semibold text-gray-700"),
            rx.el.span(
                f" {question['numeric_expected_length']}",
                class_name="text-gray-600",
            ),
            class_name="mt-2",
        ),
        class_name="mt-2",
    )


def _render_match(question: Question) -> rx.Component:
    """Render Matching question with correct pairs."""
    return rx.el.div(
        rx.el.p("Correct Matching Pairs:", class_name="text-sm font-semibold text-gray-700 mt-3 mb-2"),
        rx.foreach(
            question["match_pairs"],
            lambda pair: rx.el.div(
                rx.el.div(
                    rx.el.span(pair["source_id"], class_name="font-bold text-blue-600 mr-1"),
                    rx.el.span(pair["source_text"], class_name="text-gray-800"),
                    class_name="flex-1 bg-blue-50 px-3 py-2 rounded-md",
                ),
                rx.icon("arrow-right", class_name="mx-2 text-gray-400 flex-shrink-0"),
                rx.el.div(
                    rx.el.span(pair["target_id"], class_name="font-bold text-green-600 mr-1"),
                    rx.el.span(pair["target_text"], class_name="text-gray-800"),
                    class_name="flex-1 bg-green-50 px-3 py-2 rounded-md",
                ),
                class_name="flex items-center mt-2",
            ),
        ),
        class_name="mt-2",
    )


def question_card_with_actions(item: QuestionWithMetadata, index: rx.Var[int]) -> rx.Component:
    """Render a question card with edit/delete buttons using metadata."""
    question = item["question"]
    source_type = item["source_type"]
    original_index = item["original_index"]

    return rx.el.div(
        rx.el.div(
            # Question header with action buttons
            rx.el.div(
                # Left side: number and type badge
                rx.el.div(
                    rx.el.span(f"{index + 1}.", class_name="font-bold text-gray-800"),
                    rx.el.span(
                        question["type"].to(str),
                        class_name="px-2 py-1 text-xs font-semibold text-blue-800 bg-blue-100 rounded-full",
                    ),
                    class_name="flex items-center gap-2",
                ),
                # Right side: action buttons
                rx.el.div(
                    rx.el.button(
                        rx.icon("pencil", class_name="h-4 w-4"),
                        on_click=lambda _e, st=source_type, oi=original_index: ReviewState.open_edit_modal(st, oi),
                        class_name="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors",
                        title="Edit question",
                    ),
                    rx.el.button(
                        rx.icon("trash-2", class_name="h-4 w-4"),
                        on_click=lambda _e, st=source_type, oi=original_index: ReviewState.open_delete_modal(st, oi),
                        class_name="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors",
                        title="Delete question",
                    ),
                    class_name="flex items-center gap-1",
                ),
                class_name="flex items-center justify-between",
            ),
            # Question prompt (FIB prompt is rendered in _render_fib as prompt_with_blanks)
            rx.cond(
                (question["type"] != "FIB") | (question["prompt_with_blanks"] == ""),
                rx.el.p(question["prompt"], class_name="mt-2 text-gray-700"),
                rx.fragment(),
            ),
            # Image if present
            rx.cond(
                question["img_src"],
                rx.image(
                    src=rx.get_upload_url(question["img_src"]),
                    class_name="mt-2 rounded-lg max-h-64 w-auto",
                ),
                rx.fragment(),
            ),
            # MCQ / MRQ content
            rx.cond(
                (question["type"] == "MCQ") | (question["type"] == "MRQ"),
                _render_mcq_mrq(question),
                rx.fragment(),
            ),
            # T/F content
            rx.cond(
                question["type"] == "TF",
                _render_tf(question),
                rx.fragment(),
            ),
            # Order content
            rx.cond(
                question["type"] == "Order",
                _render_order(question),
                rx.fragment(),
            ),
            # FIB content
            rx.cond(
                question["type"] == "FIB",
                _render_fib(question),
                rx.fragment(),
            ),
            # Essay content
            rx.cond(
                question["type"] == "Essay",
                _render_essay(question),
                rx.fragment(),
            ),
            # Numeric content
            rx.cond(
                question["type"] == "Numeric",
                _render_numeric(question),
                rx.fragment(),
            ),
            # Match content
            rx.cond(
                question["type"] == "Match",
                _render_match(question),
                rx.fragment(),
            ),
            class_name="",
        ),
        class_name="bg-white p-4 rounded-lg border border-gray-200 shadow-sm",
    )


def delete_confirmation_modal() -> rx.Component:
    """Modal for delete confirmation."""
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
                            "Delete Question",
                            class_name="text-lg font-semibold text-gray-900",
                        ),
                        rx.dialog.description(
                            "Are you sure you want to delete this question? This action cannot be undone and the question will be removed from the assessment package.",
                            class_name="mt-2 text-sm text-gray-500",
                        ),
                        class_name="ml-4",
                    ),
                    class_name="flex items-start",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=ReviewState.close_delete_modal,
                        class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                    ),
                    rx.el.button(
                        "Delete",
                        on_click=ReviewState.confirm_delete_question,
                        class_name="ml-3 px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500",
                    ),
                    class_name="mt-6 flex justify-end",
                ),
                class_name="p-6",
            ),
            class_name="max-w-md mx-auto bg-white rounded-lg shadow-xl",
        ),
        open=ReviewState.delete_modal_open,
    )


def edit_question_modal() -> rx.Component:
    """Modal dialog for editing questions."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.el.div(
                # Header
                rx.el.div(
                    rx.dialog.title(
                        "Edit Question",
                        class_name="text-lg font-semibold text-gray-900",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-5 w-5"),
                        on_click=ReviewState.close_edit_modal,
                        class_name="p-1 text-gray-400 hover:text-gray-600 rounded",
                    ),
                    class_name="flex items-center justify-between pb-4 border-b border-gray-200",
                ),
                # Form content
                rx.el.div(
                    # Question type badge
                    rx.el.div(
                        rx.el.span("Question Type: ", class_name="text-sm text-gray-500"),
                        rx.el.span(
                            ReviewState.editing_question_type,
                            class_name="px-2 py-1 text-xs font-semibold text-blue-800 bg-blue-100 rounded-full",
                        ),
                        class_name="mb-4",
                    ),
                    # FIB Question Editor
                    rx.cond(
                        ReviewState.editing_question_type == "FIB",
                        rx.el.div(
                            # FIB Segments and Answers
                            rx.el.label(
                                "Fill-in-the-Blank Question",
                                class_name="block text-sm font-medium text-gray-700 mb-2",
                            ),
                            rx.el.p(
                                "Edit the text segments and correct answers for each blank:",
                                class_name="text-xs text-gray-500 mb-3",
                            ),
                            rx.foreach(
                                ReviewState.edit_fib_segments,
                                lambda seg, idx: rx.el.div(
                                    # Text segment input
                                    rx.el.div(
                                        rx.el.label(
                                            f"Text {idx + 1}:",
                                            class_name="text-xs text-gray-500",
                                        ),
                                        rx.el.input(
                                            default_value=seg,
                                            on_change=lambda _e, i=idx: ReviewState.set_fib_segment(i, _e),
                                            class_name="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                                        ),
                                        class_name="mb-2",
                                    ),
                                    # Answer input (if there's a blank after this segment)
                                    rx.cond(
                                        idx < ReviewState.edit_fib_answers.length(),
                                        rx.el.div(
                                            rx.el.label(
                                                f"Blank {idx + 1} Answer:",
                                                class_name="text-xs text-green-700 font-medium",
                                            ),
                                            rx.el.input(
                                                default_value=ReviewState.edit_fib_answers[idx][0],
                                                on_change=lambda _e, i=idx: ReviewState.set_fib_answer(i, _e),
                                                class_name="w-full px-3 py-2 border border-green-300 rounded-md text-sm text-gray-900 bg-green-50 focus:outline-none focus:ring-green-500 focus:border-green-500",
                                                placeholder="Correct answer",
                                            ),
                                            class_name="mb-3 ml-4 pl-3 border-l-2 border-green-300",
                                        ),
                                        rx.fragment(),
                                    ),
                                    class_name="mb-2",
                                ),
                            ),
                            class_name="mb-4",
                        ),
                        # Non-FIB questions
                        rx.fragment(
                            # Prompt field
                            rx.el.div(
                                rx.el.label(
                                    "Question Prompt",
                                    class_name="block text-sm font-medium text-gray-700",
                                ),
                                rx.el.textarea(
                                    default_value=ReviewState.edit_prompt,
                                    on_change=ReviewState.set_edit_prompt,
                                    class_name="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                                    rows="3",
                                ),
                                class_name="mb-4",
                            ),
                            # Choices (for MCQ/MRQ only)
                            rx.cond(
                                (ReviewState.editing_question_type == "MCQ") | (ReviewState.editing_question_type == "MRQ"),
                                rx.el.div(
                                    rx.el.label(
                                        "Answer Choices",
                                        class_name="block text-sm font-medium text-gray-700 mb-2",
                                    ),
                                    rx.el.p(
                                        rx.cond(
                                            ReviewState.editing_question_type == "MCQ",
                                            "Select one correct answer:",
                                            "Select all correct answers:",
                                        ),
                                        class_name="text-xs text-gray-500 mb-3",
                                    ),
                                    rx.foreach(
                                        ReviewState.edit_choices,
                                        lambda choice, idx: rx.el.div(
                                            # Checkbox/radio for correct answer
                                            rx.el.button(
                                                rx.cond(
                                                    ReviewState.edit_correct_answers.contains(choice["id"]),
                                                    rx.icon("square-check", class_name="h-5 w-5 text-green-600"),
                                                    rx.icon("square", class_name="h-5 w-5 text-gray-400"),
                                                ),
                                                on_click=lambda _e, cid=choice["id"]: ReviewState.toggle_correct_answer(cid),
                                                class_name="p-1 hover:bg-gray-100 rounded",
                                                type="button",
                                            ),
                                            # Choice ID label
                                            rx.el.span(
                                                choice["id"],
                                                class_name="w-8 text-sm font-semibold text-gray-600",
                                            ),
                                            # Choice text input
                                            rx.el.input(
                                                default_value=choice["text"],
                                                on_change=lambda v, i=idx: ReviewState.set_edit_choice_text(i, v),
                                                class_name="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                                            ),
                                            class_name="flex items-center gap-2 mb-2",
                                        ),
                                    ),
                                    class_name="mb-4",
                                ),
                                rx.fragment(),
                            ),
                            # T/F choices editor (simplified - no ID labels)
                            rx.cond(
                                ReviewState.editing_question_type == "TF",
                                rx.el.div(
                                    rx.el.label(
                                        "Answer Choices",
                                        class_name="block text-sm font-medium text-gray-700 mb-2",
                                    ),
                                    rx.el.p(
                                        "Select the correct answer:",
                                        class_name="text-xs text-gray-500 mb-3",
                                    ),
                                    rx.foreach(
                                        ReviewState.edit_choices,
                                        lambda choice, idx: rx.el.div(
                                            rx.el.button(
                                                rx.cond(
                                                    ReviewState.edit_correct_answers.contains(choice["id"]),
                                                    rx.icon("square-check", class_name="h-5 w-5 text-green-600"),
                                                    rx.icon("square", class_name="h-5 w-5 text-gray-400"),
                                                ),
                                                on_click=lambda _e, cid=choice["id"]: ReviewState.toggle_correct_answer(cid),
                                                class_name="p-1 hover:bg-gray-100 rounded",
                                                type="button",
                                            ),
                                            # Only show text (no ID label or input)
                                            rx.el.span(
                                                choice["text"],
                                                class_name="ml-2 text-gray-800 font-medium",
                                            ),
                                            class_name="flex items-center gap-2 mb-2",
                                        ),
                                    ),
                                    class_name="mb-4",
                                ),
                                rx.fragment(),
                            ),
                            # Order items editor
                            rx.cond(
                                ReviewState.editing_question_type == "Order",
                                rx.el.div(
                                    rx.el.label(
                                        "Order Items",
                                        class_name="block text-sm font-medium text-gray-700 mb-2",
                                    ),
                                    rx.el.p(
                                        "Edit the text of each item (order is preserved):",
                                        class_name="text-xs text-gray-500 mb-3",
                                    ),
                                    rx.foreach(
                                        ReviewState.edit_order_items,
                                        lambda item, idx: rx.el.div(
                                            # Item number
                                            rx.el.span(
                                                f"{idx + 1}.",
                                                class_name="w-8 text-sm font-semibold text-blue-600",
                                            ),
                                            # Item ID badge
                                            rx.el.span(
                                                item["id"],
                                                class_name="px-2 py-0.5 text-xs font-medium text-gray-500 bg-gray-100 rounded mr-2",
                                            ),
                                            # Item text input
                                            rx.el.input(
                                                default_value=item["text"],
                                                on_change=lambda _e, i=idx: ReviewState.set_order_item_text(i, _e),
                                                class_name="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                                            ),
                                            class_name="flex items-center gap-2 mb-2",
                                        ),
                                    ),
                                    class_name="mb-4",
                                ),
                                rx.fragment(),
                            ),
                            # Match pairs editor
                            rx.cond(
                                ReviewState.editing_question_type == "Match",
                                rx.el.div(
                                    rx.el.label(
                                        "Match Pairs",
                                        class_name="block text-sm font-medium text-gray-700 mb-2",
                                    ),
                                    rx.el.p(
                                        "Edit the text of source and target items:",
                                        class_name="text-xs text-gray-500 mb-3",
                                    ),
                                    rx.foreach(
                                        ReviewState.edit_match_pairs,
                                        lambda pair, idx: rx.el.div(
                                            # Source side
                                            rx.el.div(
                                                rx.el.span(
                                                    pair["source_id"],
                                                    class_name="text-xs font-medium text-blue-600 mb-1",
                                                ),
                                                rx.el.input(
                                                    default_value=pair["source_text"],
                                                    on_change=lambda _e, i=idx: ReviewState.set_match_source_text(i, _e),
                                                    class_name="w-full px-3 py-1.5 border border-blue-300 rounded-md text-sm text-gray-900 bg-blue-50 focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                                                ),
                                                class_name="flex-1 flex flex-col",
                                            ),
                                            # Arrow
                                            rx.icon("arrow-right", class_name="mx-2 text-gray-400 flex-shrink-0"),
                                            # Target side
                                            rx.el.div(
                                                rx.el.span(
                                                    pair["target_id"],
                                                    class_name="text-xs font-medium text-green-600 mb-1",
                                                ),
                                                rx.el.input(
                                                    default_value=pair["target_text"],
                                                    on_change=lambda _e, i=idx: ReviewState.set_match_target_text(i, _e),
                                                    class_name="w-full px-3 py-1.5 border border-green-300 rounded-md text-sm text-gray-900 bg-green-50 focus:outline-none focus:ring-green-500 focus:border-green-500",
                                                ),
                                                class_name="flex-1 flex flex-col",
                                            ),
                                            class_name="flex items-center mb-3",
                                        ),
                                    ),
                                    class_name="mb-4",
                                ),
                                rx.fragment(),
                            ),
                            # Message for Essay questions (no additional editing)
                            rx.cond(
                                ReviewState.editing_question_type == "Essay",
                                rx.el.div(
                                    rx.el.p(
                                        "Note: Only the question prompt can be edited for Essay questions.",
                                        class_name="text-sm text-amber-600 bg-amber-50 p-3 rounded-md",
                                    ),
                                    class_name="mb-4",
                                ),
                                rx.fragment(),
                            ),
                        ),
                    ),
                    class_name="py-4",
                ),
                # Footer buttons
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=ReviewState.close_edit_modal,
                        class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                    ),
                    rx.el.button(
                        "Save Changes",
                        on_click=ReviewState.save_edited_question,
                        class_name="ml-3 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                    ),
                    class_name="pt-4 border-t border-gray-200 flex justify-end",
                ),
                class_name="p-6",
            ),
            class_name="max-w-lg mx-auto bg-white rounded-lg shadow-xl",
        ),
        open=ReviewState.edit_modal_open,
    )


# Keep the old function for backwards compatibility if needed
def upload_questions_modal() -> rx.Component:
    """Modal dialog for uploading previously generated questions."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.el.div(
                # Header
                rx.el.div(
                    rx.el.div(
                        rx.icon("upload", class_name="h-5 w-5 text-blue-600 mr-2"),
                        rx.dialog.title(
                            "Upload Questions",
                            class_name="text-lg font-semibold text-gray-900",
                        ),
                        class_name="flex items-center",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-5 w-5"),
                        on_click=ReviewState.close_upload_modal,
                        class_name="p-1 text-gray-400 hover:text-gray-600 rounded",
                    ),
                    class_name="flex items-center justify-between pb-4 border-b border-gray-200",
                ),
                # Upload area
                rx.el.div(
                    rx.el.p(
                        "Upload QTI packages (.zip) or question files (.xml) to import questions.",
                        class_name="text-sm text-gray-600 mb-3",
                    ),
                    # Compact file upload button
                    rx.upload.root(
                        rx.el.div(
                            rx.icon("cloud_upload", class_name="h-4 w-4 text-blue-600"),
                            rx.el.span("Choose Files", class_name="text-sm text-gray-700 ml-1.5"),
                            class_name="flex items-center justify-center px-4 py-2",
                        ),
                        id="question_upload",
                        accept={
                            "application/zip": [".zip"],
                            "application/xml": [".xml"],
                            "text/xml": [".xml"],
                        },
                        max_files=10,
                        multiple=True,
                        on_drop=ReviewState.handle_upload(rx.upload_files(upload_id="question_upload")),
                        class_name="bg-white border border-gray-300 rounded-md shadow-sm cursor-pointer hover:bg-gray-50 transition-colors",
                    ),
                    rx.el.p(
                        "Select multiple .zip or .xml files",
                        class_name="mt-2 text-xs text-gray-400",
                    ),
                    class_name="py-2",
                ),
                # Import mode selection
                rx.el.div(
                    rx.el.p("Import Mode:", class_name="text-sm font-medium text-gray-700 mb-2"),
                    rx.el.div(
                        # Append option
                        rx.el.label(
                            rx.el.input(
                                type="radio",
                                name="upload_mode",
                                checked=ReviewState.upload_mode == "append",
                                on_change=lambda _: ReviewState.set_upload_mode("append"),
                                class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer",
                            ),
                            rx.el.span("Add to existing questions", class_name="ml-2 text-sm text-gray-700"),
                            class_name="flex items-center cursor-pointer",
                        ),
                        # Replace option
                        rx.el.label(
                            rx.el.input(
                                type="radio",
                                name="upload_mode",
                                checked=ReviewState.upload_mode == "replace",
                                on_change=lambda _: ReviewState.set_upload_mode("replace"),
                                class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer",
                            ),
                            rx.el.span("Replace all existing questions", class_name="ml-2 text-sm text-gray-700"),
                            class_name="flex items-center cursor-pointer",
                        ),
                        class_name="space-y-2",
                    ),
                    class_name="py-3 border-t border-gray-100",
                ),
                # Processing indicator
                rx.cond(
                    ReviewState.upload_processing,
                    rx.el.div(
                        rx.icon("loader_circle", class_name="h-5 w-5 text-blue-600 animate-spin mr-2"),
                        rx.el.span("Processing file...", class_name="text-sm text-gray-600"),
                        class_name="flex items-center justify-center py-4",
                    ),
                    rx.fragment(),
                ),
                # Error display
                rx.cond(
                    ReviewState.upload_errors.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            ReviewState.upload_errors,
                            lambda error: rx.el.div(
                                rx.icon("circle-alert", class_name="h-4 w-4 text-red-500 mr-2 flex-shrink-0"),
                                rx.el.span(error, class_name="text-sm text-red-700"),
                                class_name="flex items-center",
                            ),
                        ),
                        class_name="bg-red-50 border border-red-200 rounded-md p-3 mt-4",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    ReviewState.upload_warnings.length() > 0,
                    rx.el.div(
                        rx.el.div(
                            rx.icon("triangle-alert", class_name="h-4 w-4 text-amber-600 mr-2 flex-shrink-0"),
                            rx.el.span(
                                f"{ReviewState.upload_warnings.length()} warning(s) detected while parsing uploads.",
                                class_name="text-sm text-amber-800 font-medium",
                            ),
                            class_name="flex items-center",
                        ),
                        rx.el.details(
                            rx.el.summary(
                                "View warning details",
                                class_name="mt-2 text-xs font-medium text-amber-700 cursor-pointer",
                            ),
                            rx.el.div(
                                rx.foreach(
                                    ReviewState.upload_warnings,
                                    lambda warning: rx.el.div(
                                        rx.el.span(
                                            warning,
                                            class_name="text-xs text-amber-700",
                                        ),
                                        class_name="mt-1",
                                    ),
                                ),
                            ),
                            class_name="mt-1",
                        ),
                        class_name="bg-amber-50 border border-amber-200 rounded-md p-3 mt-4",
                    ),
                    rx.fragment(),
                ),
                # Preview section (shown when questions are parsed)
                rx.cond(
                    ReviewState.upload_preview_count > 0,
                    rx.el.div(
                        rx.el.div(
                            rx.icon("square-check", class_name="h-5 w-5 text-green-500 mr-2"),
                            rx.el.span(
                                rx.cond(
                                    ReviewState.upload_file_count > 1,
                                    f"{ReviewState.upload_preview_count} questions from {ReviewState.upload_file_count} files ready to import",
                                    f"{ReviewState.upload_preview_count} questions ready to import",
                                ),
                                class_name="text-sm font-medium text-green-700",
                            ),
                            class_name="flex items-center mb-3",
                        ),
                        # Question type breakdown
                        rx.el.div(
                            rx.el.p("Question Types:", class_name="text-xs font-medium text-gray-500 mb-2"),
                            rx.el.div(
                                rx.foreach(
                                    ReviewState.upload_preview_summary.entries(),
                                    lambda item: rx.cond(
                                        item[1] > 0,
                                        rx.el.span(
                                            f"{item[0]}: {item[1]}",
                                            class_name="px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded mr-2 mb-1",
                                        ),
                                        rx.fragment(),
                                    ),
                                ),
                                class_name="flex flex-wrap",
                            ),
                            class_name="bg-gray-50 rounded-md p-3",
                        ),
                        class_name="mt-4 bg-green-50 border border-green-200 rounded-md p-4",
                    ),
                    rx.fragment(),
                ),
                # Footer buttons
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=ReviewState.close_upload_modal,
                        class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                    ),
                    rx.cond(
                        ReviewState.upload_preview_count > 0,
                        rx.el.button(
                            rx.icon("download", class_name="h-4 w-4 mr-2"),
                            "Import Questions",
                            on_click=ReviewState.confirm_upload,
                            class_name="ml-3 flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                        ),
                        rx.el.button(
                            "Import Questions",
                            disabled=True,
                            class_name="ml-3 px-4 py-2 text-sm font-medium text-gray-400 bg-gray-100 border border-gray-200 rounded-md cursor-not-allowed",
                        ),
                    ),
                    class_name="pt-4 border-t border-gray-200 flex justify-end",
                ),
                class_name="p-6",
            ),
            class_name="max-w-md mx-auto bg-white rounded-lg shadow-xl",
        ),
        open=ReviewState.upload_modal_open,
    )


def upload_button() -> rx.Component:
    """Button to open the upload modal."""
    return rx.el.button(
        rx.icon("upload", class_name="mr-2 h-4 w-4"),
        "Upload",
        on_click=ReviewState.open_upload_modal,
        class_name="flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50",
    )


def clear_all_modal() -> rx.Component:
    """Confirmation dialog for clearing all questions across all states."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.el.div(
                # Warning icon and title
                rx.el.div(
                    rx.el.div(
                        rx.icon("triangle-alert", class_name="h-6 w-6 text-red-600"),
                        class_name="flex items-center justify-center w-12 h-12 rounded-full bg-red-100",
                    ),
                    rx.el.div(
                        rx.dialog.title(
                            "Clear All Questions",
                            class_name="text-lg font-semibold text-gray-900",
                        ),
                        rx.dialog.description(
                            "This will permanently delete all questions from the application.",
                            class_name="mt-1 text-sm text-gray-500",
                        ),
                        class_name="ml-4",
                    ),
                    class_name="flex items-start",
                ),
                # Warning details
                rx.el.div(
                    rx.el.p(
                        "The following will be cleared:",
                        class_name="text-sm font-medium text-gray-700 mb-2",
                    ),
                    rx.el.ul(
                        rx.el.li("Text Questions page - all generated questions", class_name="text-sm text-gray-600"),
                        rx.el.li("Image Questions page - all generated questions", class_name="text-sm text-gray-600"),
                        rx.el.li("Review & Download page - all questions", class_name="text-sm text-gray-600"),
                        class_name="list-disc list-inside space-y-1",
                    ),
                    rx.el.p(
                        "This action cannot be undone.",
                        class_name="mt-3 text-sm font-medium text-red-600",
                    ),
                    class_name="mt-4 p-3 bg-gray-50 rounded-md",
                ),
                # Footer buttons
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=ReviewState.close_clear_all_modal,
                        class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50",
                    ),
                    rx.el.button(
                        "Clear All",
                        on_click=ReviewState.confirm_clear_all,
                        class_name="ml-3 px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700",
                    ),
                    class_name="mt-6 flex justify-end",
                ),
                class_name="p-6",
            ),
            class_name="max-w-md mx-auto bg-white rounded-lg shadow-xl",
        ),
        open=ReviewState.clear_all_modal_open,
    )


def question_card(question: Question, index: rx.Var[int]) -> rx.Component:
    """Render a question card that handles all question types (without edit/delete buttons)."""
    return rx.el.div(
        rx.el.div(
            # Question header
            rx.el.div(
                rx.el.span(f"{index + 1}.", class_name="font-bold text-gray-800"),
                rx.el.span(
                    question["type"].to(str),
                    class_name="px-2 py-1 text-xs font-semibold text-blue-800 bg-blue-100 rounded-full",
                ),
                class_name="flex items-center gap-2",
            ),
            # Question prompt (FIB prompt is rendered in _render_fib as prompt_with_blanks)
            rx.cond(
                (question["type"] != "FIB") | (question["prompt_with_blanks"] == ""),
                rx.el.p(question["prompt"], class_name="mt-2 text-gray-700"),
                rx.fragment(),
            ),
            # Image if present
            rx.cond(
                question["img_src"],
                rx.image(
                    src=rx.get_upload_url(question["img_src"]),
                    class_name="mt-2 rounded-lg max-h-64 w-auto",
                ),
                rx.fragment(),
            ),
            # MCQ / MRQ content
            rx.cond(
                (question["type"] == "MCQ") | (question["type"] == "MRQ"),
                _render_mcq_mrq(question),
                rx.fragment(),
            ),
            # T/F content
            rx.cond(
                question["type"] == "TF",
                _render_tf(question),
                rx.fragment(),
            ),
            # Order content
            rx.cond(
                question["type"] == "Order",
                _render_order(question),
                rx.fragment(),
            ),
            # FIB content
            rx.cond(
                question["type"] == "FIB",
                _render_fib(question),
                rx.fragment(),
            ),
            # Essay content
            rx.cond(
                question["type"] == "Essay",
                _render_essay(question),
                rx.fragment(),
            ),
            # Match content
            rx.cond(
                question["type"] == "Match",
                _render_match(question),
                rx.fragment(),
            ),
            class_name="",
        ),
        class_name="bg-white p-4 rounded-lg border border-gray-200 shadow-sm",
    )
