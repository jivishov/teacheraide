import reflex as rx


def icon_wrapper(icon_name: str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon_name, class_name="h-5 w-5 text-blue-600"),
        class_name="flex items-center justify-center h-10 w-10 bg-blue-100 rounded-xl flex-shrink-0",
    )


def feature_card(icon: str, title: str, description: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            icon_wrapper(icon),
            rx.el.h3(title, class_name="text-base font-bold text-gray-900"),
            class_name="flex items-center gap-3",
        ),
        rx.el.p(description, class_name="mt-2 text-sm text-gray-600 leading-relaxed"),
        class_name="p-4 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow",
    )