import reflex as rx


def model_chip_group(
    provider_label: str,
    models,
    selected_model,
    on_select_handler,
) -> rx.Component:
    """Render provider-labeled model chips."""
    return rx.cond(
        models.length() > 0,
        rx.el.div(
            rx.el.p(provider_label, class_name="text-xs font-semibold text-gray-600"),
            rx.el.div(
                rx.foreach(
                    models,
                    lambda model_name: rx.el.button(
                        model_name,
                        on_click=lambda _e, m=model_name: on_select_handler(m),
                        type="button",
                        class_name=rx.cond(
                            selected_model == model_name,
                            "px-3 py-1.5 text-xs font-semibold rounded-full border border-blue-700 bg-blue-600 text-white shadow-sm",
                            "px-3 py-1.5 text-xs font-medium rounded-full border border-gray-300 bg-white text-gray-700 hover:bg-gray-100",
                        ),
                    ),
                ),
                class_name="mt-1.5 flex flex-wrap gap-2",
            ),
            class_name="space-y-1",
        ),
        rx.fragment(),
    )


def quick_model_switcher(
    title,
    selected_model,
    default_model,
    openai_models,
    anthropic_models,
    gemini_models,
    custom_models,
    on_select_handler,
    persist_choice,
    on_toggle_persist_handler,
    on_reset_handler,
) -> rx.Component:
    """Reusable segmented-chip model switcher for action pages."""
    return rx.el.details(
        rx.el.summary(
            rx.el.div(
                rx.el.div(
                    rx.el.h4(title, class_name="text-sm font-semibold text-gray-900"),
                    rx.el.p(
                        "Expand to change model before generating.",
                        class_name="text-xs text-gray-500 mt-0.5",
                    ),
                ),
                rx.el.div(
                    rx.el.span("Selected:", class_name="text-xs text-gray-500"),
                    rx.el.code(
                        rx.cond(selected_model != "", selected_model, "Not selected"),
                        class_name="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-800",
                    ),
                    rx.el.span("Default:", class_name="text-xs text-gray-500 ml-2"),
                    rx.el.code(
                        rx.cond(default_model != "", default_model, "Auto"),
                        class_name="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-800",
                    ),
                    class_name="mt-2 md:mt-0 flex flex-wrap items-center gap-2",
                ),
                class_name="flex flex-col md:flex-row md:items-center md:justify-between gap-2",
            ),
            class_name="cursor-pointer list-none",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    rx.cond(
                        persist_choice,
                        "Use as default: On",
                        "Use as default: Off",
                    ),
                    on_click=on_toggle_persist_handler,
                    type="button",
                    class_name=rx.cond(
                        persist_choice,
                        "px-3 py-1.5 text-xs rounded-md bg-blue-100 text-blue-800 border border-blue-300",
                        "px-3 py-1.5 text-xs rounded-md bg-gray-100 text-gray-700 border border-gray-300",
                    ),
                ),
                rx.el.button(
                    "Reset to default",
                    on_click=on_reset_handler,
                    type="button",
                    class_name="px-3 py-1.5 text-xs rounded-md bg-white text-gray-700 border border-gray-300 hover:bg-gray-50",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                model_chip_group("OpenAI", openai_models, selected_model, on_select_handler),
                model_chip_group(
                    "Anthropic", anthropic_models, selected_model, on_select_handler
                ),
                model_chip_group("Gemini", gemini_models, selected_model, on_select_handler),
                model_chip_group("Custom", custom_models, selected_model, on_select_handler),
                class_name="mt-3 space-y-3",
            ),
            class_name="mt-3",
        ),
        class_name="mt-4 p-3 bg-white rounded-lg border border-gray-200",
    )
