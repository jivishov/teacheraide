import reflex as rx


def nav_menu() -> rx.Component:
    """Navigation menu component for all pages."""
    nav_items = [
        {"label": "Home", "href": "/", "icon": "home"},
        {"label": "Upload", "href": "/upload-material", "icon": "upload"},
        {"label": "Text Questions", "href": "/text-questions", "icon": "file-text"},
        {"label": "Image Questions", "href": "/image-questions", "icon": "image"},
        {"label": "Review", "href": "/review-download", "icon": "clipboard-check"},
        {"label": "Settings", "href": "/settings", "icon": "settings"},
        {"label": "Reading Material", "href": "/reading-material", "icon": "book-open"},
    ]
    return rx.el.nav(
        rx.el.div(
            rx.el.a(
                rx.el.div(
                    rx.el.span("Teacher", class_name="font-semibold text-gray-700"),
                    rx.el.span("AI", class_name="font-bold text-blue-600 font-['Outfit']"),
                    rx.el.span("de", class_name="font-semibold text-gray-700"),
                    class_name="inline-flex items-baseline text-lg tracking-tight",
                ),
                href="/",
                class_name="hover:opacity-80 transition-opacity",
            ),
            rx.el.div(
                *[
                    rx.el.a(
                        rx.icon(item["icon"], class_name="w-4 h-4"),
                        rx.el.span(item["label"]),
                        href=item["href"],
                        class_name="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all duration-200",
                    )
                    for item in nav_items
                ],
                class_name="flex items-center gap-1",
            ),
            class_name="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-14",
        ),
        class_name="bg-white border-b border-gray-200 sticky top-0 z-50 backdrop-blur-sm bg-white/95",
    )


def page_header(icon: str, title: str, description: str) -> rx.Component:
    """Compact inline page header with icon, title, and description."""
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="w-5 h-5 text-blue-600 flex-shrink-0"),
            rx.el.h1(title, class_name="text-xl font-bold text-gray-900"),
            rx.cond(
                description != "",
                rx.fragment(
                    rx.el.span("·", class_name="text-gray-300"),
                    rx.el.span(description, class_name="text-sm text-gray-500 truncate"),
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2.5",
        ),
        class_name="pb-4 border-b border-gray-200",
    )
