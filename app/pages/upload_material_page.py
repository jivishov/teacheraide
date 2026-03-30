"""Upload Material page — V2 layout matching text/image/reading material pages."""

import reflex as rx

from app.components.layout_components import nav_menu, page_header
from app.states.material_state import MaterialState


def _main_card() -> rx.Component:
    """PDF preview — the primary content area."""
    return rx.el.div(
        rx.el.label(
            "PDF Preview",
            class_name="text-sm font-medium text-gray-700 block mb-3",
        ),
        rx.cond(
            MaterialState.extracted_pdf_name,
            rx.el.iframe(
                src=rx.get_upload_url(MaterialState.extracted_pdf_name),
                class_name="w-full h-[720px] border border-gray-200 rounded-lg bg-white",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "file-search",
                        class_name="w-14 h-14 text-gray-200 mb-4",
                    ),
                    rx.el.p(
                        "Upload a PDF using the sidebar",
                        class_name="text-sm font-medium text-gray-400",
                    ),
                    rx.el.p(
                        "Select pages, extract, then preview here",
                        class_name="text-xs text-gray-300 mt-1",
                    ),
                    class_name="flex flex-col items-center justify-center",
                ),
                class_name="flex items-center justify-center w-full h-[720px] border border-gray-200 rounded-lg bg-gray-50",
            ),
        ),
        class_name="flex-1 min-w-0 p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def _sidebar() -> rx.Component:
    """Sidebar: upload controls, extraction status, workflow navigation."""
    extract_disabled = MaterialState.is_processing | MaterialState.uploaded_pdf_name.is_none()
    nav_disabled = MaterialState.extracted_pdf_name.is_none()

    return rx.el.div(
        # ---- Section 1: UPLOAD ----
        rx.el.div(
            rx.el.span(
                "UPLOAD",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2",
            ),
            rx.upload.root(
                rx.el.div(
                    rx.icon(
                        "cloud-upload",
                        class_name="w-6 h-6 text-gray-400 mb-1.5",
                    ),
                    rx.el.p(
                        "Click or drag & drop",
                        class_name="text-xs font-semibold text-gray-600",
                    ),
                    rx.el.p(
                        "PDF files only",
                        class_name="text-xs text-gray-400 mt-0.5",
                    ),
                    class_name="flex flex-col items-center py-4 px-3",
                ),
                id="pdf-upload",
                accept={"application/pdf": [".pdf"]},
                max_files=1,
                on_drop=MaterialState.handle_upload(
                    rx.upload_files(upload_id="pdf-upload")
                ),
                class_name="w-full border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 hover:bg-blue-50 hover:border-blue-300 cursor-pointer transition-colors",
            ),
            # File info chip (shown after upload)
            rx.cond(
                MaterialState.uploaded_pdf_name,
                rx.el.div(
                    rx.el.div(
                        rx.icon(
                            "file-text",
                            class_name="w-4 h-4 text-red-500 flex-shrink-0",
                        ),
                        rx.el.div(
                            rx.el.span(
                                MaterialState.uploaded_pdf_name,
                                class_name="text-xs font-medium text-gray-900 truncate block max-w-[160px]",
                            ),
                            rx.el.span(
                                f"{MaterialState.num_pages} pages",
                                class_name="text-xs text-gray-500",
                            ),
                            class_name="flex flex-col min-w-0",
                        ),
                        class_name="flex items-start gap-2 min-w-0",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="w-3.5 h-3.5"),
                        on_click=MaterialState.clear_uploaded_pdf,
                        disabled=MaterialState.is_processing,
                        type="button",
                        aria_label="Delete uploaded PDF",
                        title="Delete uploaded PDF",
                        class_name="inline-flex h-7 w-7 items-center justify-center rounded-md border border-gray-200 bg-white text-gray-500 transition-colors hover:border-red-200 hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-40",
                    ),
                    class_name="flex items-start justify-between gap-3 mt-2 p-2 bg-gray-50 border border-gray-200 rounded-md",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-col pb-4 border-b border-gray-200",
        ),
        # ---- Section 2: PAGE SELECTION ----
        rx.el.div(
            rx.el.span(
                "PAGE SELECTION",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2",
            ),
            rx.el.div(
                rx.el.label(
                    rx.el.input(
                        type="radio",
                        name="page_selection",
                        value="all",
                        on_change=lambda: MaterialState.set_page_selection("all"),
                        checked=MaterialState.page_selection == "all",
                        class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer flex-shrink-0",
                    ),
                    "All Pages",
                    class_name="flex items-center gap-2 text-sm text-gray-700",
                ),
                rx.el.label(
                    rx.el.input(
                        type="radio",
                        name="page_selection",
                        value="custom",
                        on_change=lambda: MaterialState.set_page_selection("custom"),
                        checked=MaterialState.page_selection == "custom",
                        class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer flex-shrink-0",
                    ),
                    "Custom Range",
                    class_name="flex items-center gap-2 text-sm text-gray-700",
                ),
                class_name="flex items-center gap-4",
            ),
            rx.cond(
                MaterialState.page_selection == "custom",
                rx.el.input(
                    default_value=MaterialState.custom_pages,
                    on_change=MaterialState.set_custom_pages,
                    placeholder="e.g., 1, 3, 5-7",
                    class_name="mt-2 h-9 w-full px-3 py-2 bg-white text-gray-900 text-sm border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
                rx.fragment(),
            ),
            rx.el.button(
                rx.cond(
                    MaterialState.is_processing,
                    rx.el.span(
                        rx.icon(
                            "loader-circle",
                            class_name="w-4 h-4 animate-spin mr-2 inline-block",
                        ),
                        "Extracting\u2026",
                    ),
                    "Extract Pages",
                ),
                on_click=MaterialState.extract_pages,
                disabled=extract_disabled,
                class_name=rx.cond(
                    extract_disabled,
                    "mt-3 w-full flex items-center justify-center py-2 px-4 text-sm font-semibold text-white bg-gray-400 rounded-lg shadow-sm cursor-not-allowed",
                    "mt-3 w-full flex items-center justify-center py-2 px-4 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm cursor-pointer transition-colors",
                ),
            ),
            class_name="flex flex-col py-4 border-b border-gray-200",
        ),
        # ---- Section 3: EXTRACTION ----
        rx.el.div(
            rx.el.span(
                "EXTRACTION",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider",
            ),
            rx.cond(
                MaterialState.is_processing,
                rx.el.span(
                    rx.icon(
                        "loader-circle",
                        class_name="w-3.5 h-3.5 animate-spin mr-1.5 inline-block",
                    ),
                    "Processing\u2026",
                    class_name="mt-1 inline-flex items-center px-3 py-1 text-sm font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-full",
                ),
                rx.cond(
                    MaterialState.extracted_pdf_name,
                    rx.el.span(
                        "Extracted",
                        class_name="mt-1 inline-block px-3 py-1 text-sm font-semibold text-green-700 bg-green-50 border border-green-200 rounded-full",
                    ),
                    rx.el.span(
                        "Not extracted",
                        class_name="mt-1 inline-block px-3 py-1 text-sm font-semibold text-gray-500 bg-gray-50 border border-gray-200 rounded-full",
                    ),
                ),
            ),
            class_name="flex flex-col items-center text-center py-4 border-b border-gray-200",
        ),
        # ---- Section 4: NEXT STEP ----
        rx.el.div(
            rx.el.span(
                "NEXT STEP",
                class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2",
            ),
            rx.el.button(
                rx.icon("file-text", class_name="w-4 h-4 mr-2 flex-shrink-0"),
                "Text Questions",
                rx.icon("arrow-right", class_name="w-4 h-4 ml-auto opacity-50"),
                on_click=MaterialState.go_to_text_questions,
                disabled=nav_disabled,
                class_name="w-full flex items-center px-3 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-blue-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed",
            ),
            rx.el.button(
                rx.icon("image", class_name="w-4 h-4 mr-2 flex-shrink-0"),
                "Image Questions",
                rx.icon("arrow-right", class_name="w-4 h-4 ml-auto opacity-50"),
                on_click=MaterialState.go_to_image_questions,
                disabled=nav_disabled,
                class_name="w-full flex items-center px-3 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-blue-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed",
            ),
            rx.el.button(
                rx.icon("list-checks", class_name="w-4 h-4 mr-2 flex-shrink-0"),
                "Convert to Test",
                rx.icon("arrow-right", class_name="w-4 h-4 ml-auto opacity-50"),
                on_click=MaterialState.go_to_pdf_question_conversion,
                disabled=nav_disabled,
                class_name="w-full flex items-center px-3 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-emerald-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed",
            ),
            class_name="flex flex-col gap-2 pt-4",
        ),
        class_name="w-full lg:w-72 flex-shrink-0 p-4 bg-white rounded-xl border border-gray-200 shadow-sm h-fit lg:sticky lg:top-20",
    )


def _status_panel() -> rx.Component:
    """Error and success panels below the two-column layout."""
    return rx.el.div(
        # Error panel
        rx.cond(
            MaterialState.error_message != "",
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "triangle-alert",
                        class_name="h-5 w-5 text-red-500 flex-shrink-0",
                    ),
                    rx.el.span(
                        MaterialState.error_message,
                        class_name="text-sm text-red-600",
                    ),
                    class_name="flex items-center gap-2",
                ),
                class_name="p-3 bg-red-50 rounded-lg border border-red-200",
            ),
            rx.fragment(),
        ),
        # Success panel
        rx.cond(
            (MaterialState.extracted_pdf_name != None)
            & ~MaterialState.is_processing
            & (MaterialState.error_message == ""),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "square-check",
                        class_name="h-5 w-5 text-green-500 flex-shrink-0",
                    ),
                    rx.el.span(
                        "PDF extracted \u2014 choose a workflow from the sidebar",
                        class_name="text-sm text-green-600 font-medium",
                    ),
                    class_name="flex items-center gap-2",
                ),
                class_name="p-3 bg-green-50 rounded-lg border border-green-200",
            ),
            rx.fragment(),
        ),
        class_name="max-w-7xl mx-auto mt-4 space-y-3",
    )


def upload_material() -> rx.Component:
    """Upload material page — V2 layout."""
    return rx.fragment(
        nav_menu(),
        rx.el.main(
            rx.el.div(
                page_header(
                    "upload",
                    "Upload Material",
                    "Upload PDF to generate questions",
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
