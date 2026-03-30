"""Reading Material V2 — split-panel layout mockup."""

import reflex as rx

from app.components.layout_components import nav_menu, page_header
from app.states.v2_mock_state import ReadingMaterialV2State


def _file_type_icon(file_type: str) -> rx.Component:
    """Return a colored icon based on file type."""
    if file_type == "pdf":
        return rx.icon("file-text", class_name="w-4 h-4 text-red-500 flex-shrink-0")
    elif file_type == "docx":
        return rx.icon("file-type", class_name="w-4 h-4 text-blue-500 flex-shrink-0")
    else:
        return rx.icon("image", class_name="w-4 h-4 text-green-500 flex-shrink-0")


def _file_type_badge(file_type: str) -> rx.Component:
    """Small colored pill badge for file type."""
    if file_type == "pdf":
        return rx.el.span("PDF", class_name="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-red-100 text-red-700")
    elif file_type == "docx":
        return rx.el.span("DOCX", class_name="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-blue-100 text-blue-700")
    else:
        return rx.el.span("IMG", class_name="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-green-100 text-green-700")


def _ref_file_row(index: int) -> rx.Component:
    """Single reference file row: icon + filename + badge + size + remove button."""
    f = ReadingMaterialV2State.ref_files[index]
    file_type = f["type"].to(str)
    # Icon by type
    icon = rx.cond(
        file_type == "pdf",
        rx.icon("file-text", class_name="w-4 h-4 text-red-500 flex-shrink-0"),
        rx.cond(
            file_type == "docx",
            rx.icon("file-type", class_name="w-4 h-4 text-blue-500 flex-shrink-0"),
            rx.icon("image", class_name="w-4 h-4 text-green-500 flex-shrink-0"),
        ),
    )
    # Badge by type
    badge = rx.cond(
        file_type == "pdf",
        rx.el.span("PDF", class_name="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-red-100 text-red-700"),
        rx.cond(
            file_type == "docx",
            rx.el.span("DOCX", class_name="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-blue-100 text-blue-700"),
            rx.el.span("IMG", class_name="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-green-100 text-green-700"),
        ),
    )
    return rx.el.div(
        icon,
        rx.el.span(f["name"], class_name="text-sm text-gray-900 truncate flex-1"),
        badge,
        rx.el.span(f["size"], class_name="text-xs text-gray-400 flex-shrink-0"),
        rx.el.button(
            rx.icon("x", class_name="w-3.5 h-3.5"),
            on_click=ReadingMaterialV2State.remove_ref_file(index),
            class_name="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded flex-shrink-0",
        ),
        class_name="flex items-center gap-2.5 py-2 px-3 hover:bg-gray-50 rounded transition-colors",
    )


def _ref_file_list() -> rx.Component:
    """Conditional slot rendering for ref files (indices 0-4)."""
    return rx.el.div(
        rx.cond(ReadingMaterialV2State.ref_file_count >= 1, _ref_file_row(0), rx.fragment()),
        rx.cond(ReadingMaterialV2State.ref_file_count >= 2, _ref_file_row(1), rx.fragment()),
        rx.cond(ReadingMaterialV2State.ref_file_count >= 3, _ref_file_row(2), rx.fragment()),
        rx.cond(ReadingMaterialV2State.ref_file_count >= 4, _ref_file_row(3), rx.fragment()),
        rx.cond(ReadingMaterialV2State.ref_file_count >= 5, _ref_file_row(4), rx.fragment()),
        class_name="border border-gray-200 rounded-lg divide-y divide-gray-100 bg-white",
    )


def _reference_upload_section() -> rx.Component:
    """Reference material upload section with dropzone, file list, and controls."""
    return rx.el.div(
        # Header: label + file count badge
        rx.el.div(
            rx.el.label(
                "Reference Materials",
                class_name="text-sm font-medium text-gray-700",
            ),
            rx.el.span("(Optional)", class_name="text-xs text-gray-400 ml-1"),
            rx.cond(
                ReadingMaterialV2State.ref_file_count > 0,
                rx.el.span(
                    ReadingMaterialV2State.ref_file_count.to(str),
                    class_name="ml-2 px-1.5 py-0.5 text-[10px] font-semibold rounded-full bg-blue-100 text-blue-700",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center mb-2",
        ),

        # Dropzone or max-reached indicator
        rx.cond(
            ReadingMaterialV2State.can_add_ref_file,
            # Compact dropzone strip
            rx.el.div(
                rx.el.div(
                    rx.icon("cloud-upload", class_name="w-6 h-6 text-gray-400 mr-2.5 flex-shrink-0"),
                    rx.el.div(
                        rx.el.p(
                            "Drop files here or click to browse",
                            class_name="text-sm font-semibold text-gray-600",
                        ),
                        rx.el.p(
                            "JPG, PNG, PDF, DOCX (max 5 files)",
                            class_name="text-xs text-gray-400 mt-0.5",
                        ),
                    ),
                    class_name="flex items-center justify-center py-3 px-4",
                ),
                on_click=ReadingMaterialV2State.mock_add_ref_file,
                class_name="w-full border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors mb-2",
            ),
            # Max files reached
            rx.el.div(
                rx.el.div(
                    rx.icon("check-check", class_name="w-4 h-4 text-amber-500 mr-2 flex-shrink-0"),
                    rx.el.span("Maximum files reached (5/5)", class_name="text-sm text-amber-600 font-medium"),
                    class_name="flex items-center justify-center py-2.5 px-4",
                ),
                class_name="w-full border-2 border-dashed border-amber-300 rounded-lg bg-amber-50 mb-2",
            ),
        ),

        # File list (only when there are files)
        rx.cond(
            ReadingMaterialV2State.ref_file_count > 0,
            rx.el.div(
                _ref_file_list(),
                # Clear All button
                rx.el.div(
                    rx.el.button(
                        rx.icon("trash-2", class_name="w-3.5 h-3.5 mr-1"),
                        "Clear All",
                        on_click=ReadingMaterialV2State.clear_ref_files,
                        class_name="inline-flex items-center px-2.5 py-1 text-xs font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors",
                    ),
                    class_name="flex justify-end mt-1.5",
                ),
            ),
            rx.fragment(),
        ),

        # Error message
        rx.cond(
            ReadingMaterialV2State.upload_error != "",
            rx.el.p(
                ReadingMaterialV2State.upload_error,
                class_name="text-xs text-red-500 mt-1",
            ),
            rx.fragment(),
        ),

        class_name="mb-4",
    )


def _preflight_item(label: str, is_ok: rx.Var[bool]) -> rx.Component:
    """Single labeled preflight check: dot + label."""
    return rx.el.div(
        rx.el.span(
            class_name=rx.cond(
                is_ok,
                "w-2.5 h-2.5 rounded-full bg-green-500 inline-block flex-shrink-0",
                "w-2.5 h-2.5 rounded-full bg-red-400 inline-block flex-shrink-0",
            ),
        ),
        rx.el.span(label, class_name="text-xs text-gray-600"),
        class_name="flex items-center gap-1.5",
    )


def _left_panel() -> rx.Component:
    """Left config panel (40% width)."""
    return rx.el.div(
        # Content Type radios
        rx.el.div(
            rx.el.label("Content Type", class_name="text-sm font-medium text-gray-700 block mb-2"),
            rx.el.div(
                rx.el.label(
                    rx.el.input(
                        type="radio",
                        name="rm_v2_content_type",
                        value="reading",
                        checked=ReadingMaterialV2State.content_type == "reading",
                        on_change=lambda _: ReadingMaterialV2State.set_content_type_v2("reading"),
                        class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer",
                    ),
                    " Reading",
                    class_name="flex items-center gap-2 text-sm text-gray-700",
                ),
                rx.el.label(
                    rx.el.input(
                        type="radio",
                        name="rm_v2_content_type",
                        value="slide",
                        checked=ReadingMaterialV2State.content_type == "slide",
                        on_change=lambda _: ReadingMaterialV2State.set_content_type_v2("slide"),
                        class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer",
                    ),
                    " Slide Notes",
                    class_name="flex items-center gap-2 text-sm text-gray-700",
                ),
                class_name="flex items-center gap-6",
            ),
            class_name="mb-4",
        ),

        # Item 4: Grade + Topic row — proportional grid
        rx.el.div(
            rx.el.div(
                rx.el.label("Grade Level", class_name="text-sm font-medium text-gray-700"),
                rx.el.select(
                    *[rx.el.option(g, value=g) for g in [
                        "K", "1", "2", "3", "4", "5", "6", "7", "8",
                        "9", "10", "11", "12", "College",
                    ]],
                    value=ReadingMaterialV2State.grade_level,
                    on_change=ReadingMaterialV2State.set_grade_level_v2,
                    class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
            ),
            rx.el.div(
                rx.el.label("Topic", class_name="text-sm font-medium text-gray-700"),
                rx.el.input(
                    placeholder="e.g., Photosynthesis",
                    value=ReadingMaterialV2State.topic,
                    on_change=ReadingMaterialV2State.set_topic_v2,
                    class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
            ),
            class_name="grid grid-cols-[0.3fr_1fr] gap-3 mb-4",
        ),

        # Objectives
        rx.el.div(
            rx.el.label("Learning Objectives", class_name="text-sm font-medium text-gray-700"),
            rx.el.textarea(
                placeholder="List the key objectives students should achieve...",
                value=ReadingMaterialV2State.objectives,
                on_change=ReadingMaterialV2State.set_objectives_v2,
                rows="3",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
            class_name="mb-4",
        ),

        # Instructions
        rx.el.div(
            rx.el.label("Additional Instructions", class_name="text-sm font-medium text-gray-700"),
            rx.el.textarea(
                placeholder="Any special instructions for the content...",
                value=ReadingMaterialV2State.user_prompt,
                on_change=ReadingMaterialV2State.set_user_prompt_v2,
                rows="2",
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none",
            ),
            class_name="mb-4",
        ),

        # Reference material uploads
        _reference_upload_section(),

        # Divider
        rx.el.hr(class_name="border-gray-200 my-4"),

        # Item 2: Model — full-width row
        rx.el.div(
            rx.el.label("Model", class_name="text-sm font-medium text-gray-700"),
            rx.el.select(
                rx.foreach(
                    ReadingMaterialV2State.model_options,
                    lambda model_name: rx.el.option(model_name, value=model_name),
                ),
                value=ReadingMaterialV2State.active_model,
                on_change=ReadingMaterialV2State.set_active_model_v2,
                class_name="mt-1 w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
            ),
            class_name="mb-4",
        ),

        # Item 2: Preflight — full-width row with labeled dots
        rx.el.div(
            rx.el.label("Preflight", class_name="text-sm font-medium text-gray-700 block mb-2"),
            rx.el.div(
                _preflight_item("Model", ReadingMaterialV2State.preflight_model),
                _preflight_item("API Key", ReadingMaterialV2State.preflight_api_key),
                _preflight_item("Topic", ReadingMaterialV2State.preflight_topic),
                class_name="flex items-center gap-4",
            ),
            class_name="mb-5",
        ),

        # Item 1: Generate button — disabled/loading state
        rx.el.button(
            rx.cond(
                ReadingMaterialV2State.generating,
                rx.el.span(
                    rx.icon("loader-circle", class_name="w-4 h-4 animate-spin mr-2 inline-block"),
                    "Generating...",
                ),
                "Generate Reading Material",
            ),
            on_click=ReadingMaterialV2State.mock_generate,
            disabled=~ReadingMaterialV2State.can_generate,
            class_name=rx.cond(
                ReadingMaterialV2State.can_generate,
                "w-full py-3 px-4 text-base font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors cursor-pointer",
                "w-full py-3 px-4 text-base font-semibold text-white bg-gray-400 rounded-lg shadow-sm cursor-not-allowed",
            ),
        ),

        # Item 1: Progress bar (shown when generating)
        rx.cond(
            ReadingMaterialV2State.generating,
            rx.el.div(
                rx.el.div(
                    ReadingMaterialV2State.progress.to(str) + "%",
                    class_name="text-xs font-medium text-blue-700 mb-1",
                ),
                rx.el.div(
                    rx.el.div(
                        class_name="bg-blue-600 h-2 rounded-full transition-all",
                        style={"width": ReadingMaterialV2State.progress.to(str) + "%"},
                    ),
                    class_name="w-full bg-gray-200 rounded-full h-2 overflow-hidden",
                ),
                rx.el.p(
                    ReadingMaterialV2State.generation_stage,
                    class_name="text-xs text-gray-500 mt-1",
                ),
                class_name="mt-3",
            ),
            rx.fragment(),
        ),

        class_name="w-full lg:w-[40%] flex-shrink-0 p-6 bg-white rounded-xl border border-gray-200 shadow-sm overflow-y-auto max-h-[calc(100vh-8rem)]",
    )


def _right_panel() -> rx.Component:
    """Right output/preview panel (60% width)."""
    return rx.el.div(
        rx.cond(
            ReadingMaterialV2State.show_output,
            # Generated content view
            rx.el.div(
                # Toolbar
                rx.el.div(
                    rx.el.button(
                        rx.icon("copy", class_name="w-4 h-4 mr-1"),
                        "Copy",
                        class_name="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="w-4 h-4 mr-1"),
                        "Clear",
                        on_click=ReadingMaterialV2State.clear_output,
                        class_name="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50",
                    ),
                    rx.el.button(
                        rx.icon("download", class_name="w-4 h-4 mr-1"),
                        "Download",
                        class_name="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50",
                    ),
                    class_name="flex gap-2 mb-3",
                ),

                # Item 6: Stats bar
                rx.el.div(
                    rx.el.span(
                        "Word count: ",
                        rx.el.span(
                            ReadingMaterialV2State.word_count.to(str),
                            class_name="font-medium",
                        ),
                        class_name="text-xs text-gray-500",
                    ),
                    rx.el.span("|", class_name="text-xs text-gray-300"),
                    rx.el.span(
                        "Sections: ",
                        rx.el.span(
                            ReadingMaterialV2State.section_count.to(str),
                            class_name="font-medium",
                        ),
                        class_name="text-xs text-gray-500",
                    ),
                    rx.el.span("|", class_name="text-xs text-gray-300"),
                    rx.el.span(
                        "Grade ",
                        rx.el.span(
                            ReadingMaterialV2State.grade_level,
                            class_name="font-medium",
                        ),
                        class_name="text-xs text-gray-500",
                    ),
                    class_name="flex items-center gap-2 mb-3",
                ),

                # Markdown content
                rx.el.div(
                    rx.markdown(ReadingMaterialV2State.generated_content),
                    class_name="prose prose-sm max-w-none p-4 bg-white rounded-lg border border-gray-200 text-gray-900",
                ),
                class_name="h-full",
            ),
            # Item 5: Enhanced empty state
            rx.el.div(
                rx.el.div(
                    rx.icon("file-text", class_name="w-16 h-16 text-gray-300 mb-4"),
                    rx.cond(
                        ReadingMaterialV2State.preflight_topic,
                        # Topic is entered — show context-aware placeholder
                        rx.el.div(
                            rx.el.p(
                                rx.el.span("Your ", class_name="text-gray-400"),
                                rx.el.span(
                                    ReadingMaterialV2State.topic,
                                    class_name="text-gray-600 font-semibold",
                                ),
                                rx.el.span(" reading material will appear here", class_name="text-gray-400"),
                                class_name="text-sm font-medium",
                            ),
                            rx.el.p(
                                rx.el.span("Grade ", class_name="text-gray-300"),
                                rx.el.span(
                                    ReadingMaterialV2State.grade_level,
                                    class_name="text-gray-400 font-medium",
                                ),
                                class_name="text-xs mt-1.5",
                            ),
                            class_name="text-center",
                        ),
                        # No topic — generic placeholder
                        rx.el.div(
                            rx.el.p(
                                "Enter a topic and click Generate",
                                class_name="text-gray-400 text-sm font-medium",
                            ),
                            rx.el.p(
                                "Configure settings on the left to get started",
                                class_name="text-gray-300 text-xs mt-1",
                            ),
                            class_name="text-center",
                        ),
                    ),
                    class_name="flex flex-col items-center justify-center",
                ),
                class_name="flex items-center justify-center h-full min-h-[400px]",
            ),
        ),
        class_name="flex-1 p-6 bg-gray-50 rounded-xl border border-gray-200 overflow-y-auto max-h-[calc(100vh-8rem)]",
    )


def reading_material_v2() -> rx.Component:
    """Reading Material V2 page — split-panel layout."""
    return rx.fragment(
        nav_menu(),
        rx.el.main(
            rx.el.div(
                page_header(
                    "book-open",
                    "Reading Material V2",
                    "Split-panel layout mockup",
                ),
                # Two-panel split
                rx.el.div(
                    _left_panel(),
                    _right_panel(),
                    class_name="flex flex-col lg:flex-row gap-6 mt-6",
                ),
                class_name="p-6",
            ),
            class_name="min-h-screen bg-gray-50 font-['Inter']",
        ),
    )
