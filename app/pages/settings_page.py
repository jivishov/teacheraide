import reflex as rx

from app.components.layout_components import nav_menu, page_header
from app.states.settings_state import SettingsState


def _reasoning_effort_label(option: str) -> str:
    labels = {
        "none": "None",
        "minimal": "Minimal",
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "xhigh": "X-High",
    }
    return labels.get(option, option)


def _api_key_card(
    provider: str,
    icon: str,
    color: str,
    api_key_value,
    masked_key,
    show_key,
    on_change_handler,
    on_toggle_handler,
    on_clear_handler,
) -> rx.Component:
    """Reusable API key input card."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name=f"w-5 h-5 text-{color}-600"),
                rx.el.h3(f"{provider} API Key", class_name="text-lg font-semibold text-gray-900"),
                class_name="flex items-center gap-2",
            ),
            rx.cond(
                api_key_value != "",
                rx.el.span(
                    rx.icon("square-check", class_name="w-4 h-4 mr-1"),
                    "Configured",
                    class_name="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800",
                ),
                rx.el.span(
                    "Not configured",
                    class_name="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600",
                ),
            ),
            class_name="flex items-center justify-between mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.input(
                    type=rx.cond(show_key, "text", "password"),
                    placeholder=f"Enter your {provider} API key",
                    value=api_key_value,
                    on_change=on_change_handler,
                    class_name="flex-1 px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-l-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                ),
                rx.el.button(
                    rx.cond(
                        show_key,
                        rx.icon("eye-off", class_name="w-4 h-4"),
                        rx.icon("eye", class_name="w-4 h-4"),
                    ),
                    on_click=on_toggle_handler,
                    class_name="px-3 py-2 border border-l-0 border-gray-300 bg-gray-50 hover:bg-gray-100 text-gray-600",
                ),
                rx.el.button(
                    rx.icon("x", class_name="w-4 h-4"),
                    on_click=on_clear_handler,
                    class_name="px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 hover:bg-red-50 text-gray-600 hover:text-red-600",
                ),
                class_name="flex w-full",
            ),
            rx.cond(
                api_key_value != "",
                rx.el.p(
                    f"Key: {masked_key}",
                    class_name="text-xs text-gray-500 mt-2",
                ),
                None,
            ),
            class_name="w-full",
        ),
        class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def _model_selection_card(
    provider: str,
    icon: str,
    color: str,
    models,
    selected_model,
    on_change_handler,
    model_input,
    on_input_change_handler,
    on_add_handler,
    on_remove_handler,
) -> rx.Component:
    """Reusable model selection card with add/remove controls."""
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name=f"w-5 h-5 text-{color}-600"),
            rx.el.h3(f"{provider} Model", class_name="text-lg font-semibold text-gray-900"),
            class_name="flex items-center gap-2 mb-4",
        ),
        rx.cond(
            models.length() > 0,
            rx.el.div(
                rx.foreach(
                    models,
                    lambda model: rx.el.div(
                        rx.el.label(
                            rx.el.input(
                                type="radio",
                                name=f"{provider.lower()}_model",
                                value=model,
                                checked=selected_model == model,
                                on_change=lambda v: on_change_handler(v),
                                class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 checked:bg-blue-600 checked:border-[5px] cursor-pointer mr-2",
                            ),
                            model,
                            class_name=rx.cond(
                                selected_model == model,
                                f"flex-1 flex items-center p-3 rounded-lg border-2 border-{color}-500 bg-{color}-50 text-gray-900 cursor-pointer",
                                "flex-1 flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-900 cursor-pointer",
                            ),
                        ),
                        rx.el.button(
                            rx.icon("trash-2", class_name="w-4 h-4"),
                            on_click=lambda: on_remove_handler(model),
                            class_name="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md border border-gray-200",
                            title=f"Remove {model}",
                        ),
                        class_name="flex items-center gap-2",
                    ),
                ),
                class_name="space-y-2 mb-4",
            ),
            rx.el.div(
                rx.icon("inbox", class_name="w-5 h-5 text-gray-300"),
                rx.el.p(
                    "No models configured for this provider.",
                    class_name="text-sm text-gray-400",
                ),
                class_name="flex items-center gap-2 py-2 mb-4",
            ),
        ),
        rx.el.div(
            rx.el.input(
                placeholder=f"Add {provider} model",
                value=model_input,
                on_change=on_input_change_handler,
                class_name=f"flex-1 px-3 py-2 bg-white text-gray-900 border border-{color}-200 rounded-l-md shadow-sm focus:ring-{color}-500 focus:border-{color}-500",
            ),
            rx.el.button(
                rx.icon("plus", class_name="w-4 h-4 mr-1"),
                "Add",
                on_click=on_add_handler,
                class_name=f"flex items-center px-4 py-2 border border-l-0 border-{color}-300 rounded-r-md bg-{color}-600 hover:bg-{color}-700 text-white font-medium",
            ),
            class_name="flex w-full",
        ),
        class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def _custom_models_card() -> rx.Component:
    """Card for managing custom model names."""
    return rx.el.div(
        rx.el.div(
            rx.icon("plus", class_name="w-5 h-5 text-purple-600"),
            rx.el.h3("Custom Models", class_name="text-lg font-semibold text-gray-900"),
            class_name="flex items-center gap-2 mb-2",
        ),
        rx.el.p(
            "Add custom model names to use in function assignments.",
            class_name="text-sm text-gray-500 mb-4",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="Enter custom model name",
                value=SettingsState.new_model_input,
                on_change=SettingsState.set_new_model_input,
                class_name="flex-1 px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-l-md shadow-sm focus:ring-purple-500 focus:border-purple-500",
            ),
            rx.el.button(
                rx.icon("plus", class_name="w-4 h-4 mr-1"),
                "Add",
                on_click=SettingsState.add_custom_model,
                class_name="flex items-center px-4 py-2 border border-l-0 border-gray-300 rounded-r-md bg-purple-600 hover:bg-purple-700 text-white font-medium",
            ),
            class_name="flex w-full mb-4",
        ),
        rx.cond(
            SettingsState.custom_models.length() > 0,
            rx.el.div(
                rx.el.p("Added Models:", class_name="text-sm font-medium text-gray-700 mb-2"),
                rx.el.div(
                    rx.foreach(
                        SettingsState.custom_models,
                        lambda model: rx.el.div(
                            rx.el.span(model, class_name="text-sm text-gray-700"),
                            rx.el.button(
                                rx.icon("trash-2", class_name="w-4 h-4"),
                                on_click=lambda: SettingsState.remove_custom_model(model),
                                class_name="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded",
                            ),
                            class_name="flex items-center justify-between p-2 bg-gray-50 rounded-lg border border-gray-200",
                        ),
                    ),
                    class_name="space-y-2",
                ),
            ),
            rx.el.div(
                rx.icon("inbox", class_name="w-8 h-8 text-gray-300 mx-auto mb-2"),
                rx.el.p("No custom models added yet", class_name="text-sm text-gray-400 text-center"),
                class_name="py-6",
            ),
        ),
        class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def _function_assignment_card() -> rx.Component:
    """Card for assigning models to generation functions."""
    functions = [
        {
            "id": "reading_material",
            "name": "Reading Material (Text Only)",
            "desc": "Generate reading material without images",
            "icon": "file-text",
            "value": SettingsState.reading_material_model,
            "handler": SettingsState.set_reading_material_model,
        },
        {
            "id": "reading_material_image",
            "name": "Reading Material (With Image)",
            "desc": "Generate reading material with images",
            "icon": "image",
            "value": SettingsState.reading_material_with_image_model,
            "handler": SettingsState.set_reading_material_with_image_model,
        },
        {
            "id": "text_questions",
            "name": "Text-Only Questions",
            "desc": "Generate text-based questions",
            "icon": "list-checks",
            "value": SettingsState.text_questions_model,
            "handler": SettingsState.set_text_questions_model,
        },
        {
            "id": "image_questions",
            "name": "Image-Based Questions",
            "desc": "Generate questions from images",
            "icon": "image-plus",
            "value": SettingsState.image_questions_model,
            "handler": SettingsState.set_image_questions_model,
        },
        {
            "id": "student_remediation",
            "name": "Student Remediation",
            "desc": "Generate final remediation plans after scoring",
            "icon": "sparkles",
            "value": SettingsState.student_remediation_model,
            "handler": SettingsState.set_student_remediation_model,
        },
    ]

    return rx.el.div(
        rx.el.div(
            rx.icon("workflow", class_name="w-5 h-5 text-indigo-600"),
            rx.el.h3("Function Model Assignments", class_name="text-lg font-semibold text-gray-900"),
            class_name="flex items-center gap-2 mb-2",
        ),
        rx.el.p(
            "Assign a specific model to each generation function.",
            class_name="text-sm text-gray-500 mb-6",
        ),
        rx.el.div(
            *[
                rx.el.div(
                    rx.el.div(
                        rx.icon(func["icon"], class_name="w-5 h-5 text-gray-600"),
                        rx.el.div(
                            rx.el.p(func["name"], class_name="text-sm font-medium text-gray-900"),
                            rx.el.p(func["desc"], class_name="text-xs text-gray-500"),
                            class_name="ml-3",
                        ),
                        class_name="flex items-center",
                    ),
                    rx.el.select(
                        rx.el.option("-- Select Model --", value=""),
                        rx.foreach(
                            SettingsState.openai_models,
                            lambda m: rx.el.option(f"OpenAI: {m}", value=m),
                        ),
                        rx.foreach(
                            SettingsState.anthropic_models,
                            lambda m: rx.el.option(f"Anthropic: {m}", value=m),
                        ),
                        rx.foreach(
                            SettingsState.gemini_models,
                            lambda m: rx.el.option(f"Gemini: {m}", value=m),
                        ),
                        rx.foreach(
                            SettingsState.custom_models,
                            lambda m: rx.el.option(f"Custom: {m}", value=m),
                        ),
                        value=func["value"],
                        on_change=func["handler"],
                        class_name="w-64 px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500",
                    ),
                    class_name="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 mb-3",
                )
                for func in functions
            ],
            class_name="space-y-3",
        ),
        class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def settings() -> rx.Component:
    """Settings page for API keys and model configuration."""
    return rx.fragment(
        nav_menu(),
        rx.el.main(
            rx.el.div(
                page_header("settings", "Settings", "Configure API keys and model preferences"),
                rx.el.div(
                    rx.el.button(
                        rx.icon("save", class_name="w-4 h-4 mr-2"),
                        "Save Settings",
                        on_click=SettingsState.save_settings,
                        class_name="inline-flex items-center px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700",
                    ),
                    rx.cond(
                        SettingsState.settings_status != "",
                        rx.el.span(
                            SettingsState.settings_status,
                            class_name="text-sm text-gray-600",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex items-center justify-between mb-4 p-4 bg-white rounded-lg border border-gray-200 shadow-sm",
                ),
                rx.el.div(
                    rx.el.h2(
                        rx.icon("key", class_name="w-5 h-5 mr-2"),
                        "API Keys",
                        class_name="flex items-center text-lg font-bold text-gray-900 mb-4",
                    ),
                    rx.el.div(
                        _api_key_card(
                            provider="OpenAI",
                            icon="bot",
                            color="green",
                            api_key_value=SettingsState.openai_api_key,
                            masked_key=SettingsState.masked_openai_key,
                            show_key=SettingsState.show_openai_key,
                            on_change_handler=SettingsState.set_openai_api_key,
                            on_toggle_handler=SettingsState.toggle_openai_key_visibility,
                            on_clear_handler=SettingsState.clear_openai_key,
                        ),
                        _api_key_card(
                            provider="Anthropic",
                            icon="sparkles",
                            color="orange",
                            api_key_value=SettingsState.anthropic_api_key,
                            masked_key=SettingsState.masked_anthropic_key,
                            show_key=SettingsState.show_anthropic_key,
                            on_change_handler=SettingsState.set_anthropic_api_key,
                            on_toggle_handler=SettingsState.toggle_anthropic_key_visibility,
                            on_clear_handler=SettingsState.clear_anthropic_key,
                        ),
                        _api_key_card(
                            provider="Gemini",
                            icon="gem",
                            color="blue",
                            api_key_value=SettingsState.gemini_api_key,
                            masked_key=SettingsState.masked_gemini_key,
                            show_key=SettingsState.show_gemini_key,
                            on_change_handler=SettingsState.set_gemini_api_key,
                            on_toggle_handler=SettingsState.toggle_gemini_key_visibility,
                            on_clear_handler=SettingsState.clear_gemini_key,
                        ),
                        class_name="grid grid-cols-1 lg:grid-cols-3 gap-4",
                    ),
                    class_name="mb-8",
                ),
                rx.el.div(
                    rx.el.h2(
                        rx.icon("cpu", class_name="w-5 h-5 mr-2"),
                        "Model Selection",
                        class_name="flex items-center text-lg font-bold text-gray-900 mb-4",
                    ),
                    rx.el.div(
                        _model_selection_card(
                            provider="OpenAI",
                            icon="bot",
                            color="green",
                            models=SettingsState.openai_models,
                            selected_model=SettingsState.selected_openai_model,
                            on_change_handler=SettingsState.set_selected_openai_model,
                            model_input=SettingsState.new_openai_model_input,
                            on_input_change_handler=SettingsState.set_new_openai_model_input,
                            on_add_handler=SettingsState.add_openai_model,
                            on_remove_handler=SettingsState.remove_openai_model,
                        ),
                        _model_selection_card(
                            provider="Anthropic",
                            icon="sparkles",
                            color="orange",
                            models=SettingsState.anthropic_models,
                            selected_model=SettingsState.selected_anthropic_model,
                            on_change_handler=SettingsState.set_selected_anthropic_model,
                            model_input=SettingsState.new_anthropic_model_input,
                            on_input_change_handler=SettingsState.set_new_anthropic_model_input,
                            on_add_handler=SettingsState.add_anthropic_model,
                            on_remove_handler=SettingsState.remove_anthropic_model,
                        ),
                        _model_selection_card(
                            provider="Gemini",
                            icon="gem",
                            color="blue",
                            models=SettingsState.gemini_models,
                            selected_model=SettingsState.selected_gemini_model,
                            on_change_handler=SettingsState.set_selected_gemini_model,
                            model_input=SettingsState.new_gemini_model_input,
                            on_input_change_handler=SettingsState.set_new_gemini_model_input,
                            on_add_handler=SettingsState.add_gemini_model,
                            on_remove_handler=SettingsState.remove_gemini_model,
                        ),
                        class_name="grid grid-cols-1 lg:grid-cols-3 gap-4",
                    ),
                    class_name="mb-8",
                ),
                rx.el.div(
                    rx.el.h2(
                        rx.icon("brain", class_name="w-5 h-5 mr-2"),
                        "Thinking / Reasoning",
                        class_name="flex items-center text-lg font-bold text-gray-900 mb-4",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.div(
                                rx.el.h3("Extended Thinking Mode", class_name="text-lg font-semibold text-gray-900"),
                                rx.el.p(
                                    "Enable extended thinking for more thorough reasoning (Claude/Gemini) or higher reasoning effort (OpenAI).",
                                    class_name="text-sm text-gray-500 mt-1",
                                ),
                                class_name="flex-1",
                            ),
                            rx.el.button(
                                rx.cond(
                                    SettingsState.enable_thinking,
                                    rx.el.span("Enabled", class_name="text-white"),
                                    rx.el.span("Disabled", class_name="text-gray-700"),
                                ),
                                on_click=SettingsState.toggle_thinking,
                                class_name=rx.cond(
                                    SettingsState.enable_thinking,
                                    "px-4 py-2 rounded-lg bg-blue-600 text-white font-medium",
                                    "px-4 py-2 rounded-lg bg-gray-200 text-gray-700 font-medium",
                                ),
                            ),
                            class_name="flex items-center justify-between p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
                        ),
                        rx.el.div(
                            rx.el.div(
                                rx.icon("gauge", class_name="w-5 h-5 text-orange-600"),
                                rx.el.h3("Thinking Budget", class_name="text-lg font-semibold text-gray-900 ml-2"),
                                class_name="flex items-center mb-2",
                            ),
                            rx.el.p(
                                "Token budget for extended thinking (Claude/Gemini). Range: 1,024 - 32,768 tokens.",
                                class_name="text-sm text-gray-500 mb-4",
                            ),
                            rx.el.div(
                                rx.el.input(
                                    type="number",
                                    min="1024",
                                    max="32768",
                                    step="1024",
                                    value=SettingsState.thinking_budget.to_string(),
                                    on_change=SettingsState.set_thinking_budget,
                                    class_name="w-full px-3 py-2 bg-white text-gray-900 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                                ),
                                rx.el.p(
                                    f"Current: {SettingsState.thinking_budget} tokens",
                                    class_name="text-sm text-gray-600 mt-2",
                                ),
                            ),
                            class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
                        ),
                        rx.el.div(
                            rx.el.div(
                                rx.icon("zap", class_name="w-5 h-5 text-green-600"),
                                rx.el.h3("Reasoning Effort (OpenAI)", class_name="text-lg font-semibold text-gray-900 ml-2"),
                                class_name="flex items-center mb-2",
                            ),
                            rx.el.p(
                                "Set reasoning effort for OpenAI GPT-5 and o-series models.",
                                class_name="text-sm text-gray-500 mb-4",
                            ),
                            rx.el.div(
                                rx.foreach(
                                    SettingsState.reasoning_effort_options,
                                    lambda option: rx.el.label(
                                        rx.el.input(
                                            type="radio",
                                            name="reasoning_effort",
                                            value=option,
                                            checked=SettingsState.reasoning_effort == option,
                                            on_change=lambda v: SettingsState.set_reasoning_effort(v),
                                            class_name="appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-green-600 checked:bg-green-600 checked:border-[5px] cursor-pointer mr-2",
                                        ),
                                        rx.el.span(_reasoning_effort_label(option), class_name="text-gray-900"),
                                        class_name=rx.cond(
                                            SettingsState.reasoning_effort == option,
                                            "flex items-center p-3 rounded-lg border-2 border-green-500 bg-green-50 cursor-pointer",
                                            "flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer",
                                        ),
                                    ),
                                ),
                                class_name="flex gap-4",
                            ),
                            class_name="p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
                        ),
                        class_name="grid grid-cols-1 lg:grid-cols-3 gap-4",
                    ),
                    class_name="mb-8",
                ),
                rx.el.div(
                    rx.el.h2(
                        rx.icon("layers", class_name="w-5 h-5 mr-2"),
                        "Custom Models",
                        class_name="flex items-center text-lg font-bold text-gray-900 mb-4",
                    ),
                    _custom_models_card(),
                    class_name="mb-8",
                ),
                rx.el.div(
                    rx.el.h2(
                        rx.icon("git-branch", class_name="w-5 h-5 mr-2"),
                        "Function Assignments",
                        class_name="flex items-center text-lg font-bold text-gray-900 mb-4",
                    ),
                    _function_assignment_card(),
                    class_name="mb-8",
                ),
                class_name="p-6 space-y-6",
            ),
            class_name="min-h-screen bg-gray-50 font-['Inter']",
        ),
    )
