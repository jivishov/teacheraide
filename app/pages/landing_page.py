import reflex as rx

from app.components.layout_components import nav_menu
from app.components.landing_components import feature_card


def index() -> rx.Component:
    return rx.el.div(
        nav_menu(),
        rx.el.main(
            rx.el.div(
                rx.el.h1(
                    rx.el.span("Teacher", class_name="font-semibold text-gray-700"),
                    rx.el.span("AI", class_name="font-black text-blue-600 font-['Outfit']"),
                    rx.el.span("de", class_name="font-semibold text-gray-700"),
                    class_name="text-5xl md:text-6xl tracking-tight",
                ),
                rx.el.p(
                    "AI-Powered Assessment Question Generator",
                    class_name="mt-2 text-lg md:text-xl text-gray-600 max-w-2xl text-center",
                ),
                rx.el.div(
                    rx.el.a(
                        rx.el.button(
                            "Get Started",
                            rx.icon("arrow-right", class_name="ml-2"),
                            class_name="flex items-center bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-transform transform hover:scale-105 shadow-lg",
                        ),
                        href="/upload-material",
                    ),
                    rx.el.a(
                        rx.el.button(
                            "Review Existing",
                            rx.icon("file-check-2", class_name="ml-2"),
                            class_name="flex items-center bg-white text-gray-700 px-8 py-3 rounded-lg text-lg font-semibold hover:bg-gray-100 transition-colors border border-gray-300 shadow-lg",
                        ),
                        href="/review-download",
                    ),
                    class_name="mt-4 flex flex-col sm:flex-row items-center justify-center gap-4",
                ),
                class_name="flex flex-col items-center justify-center text-center py-8 md:py-10",
            ),
            rx.el.div(
                feature_card(
                    icon="cloud_upload",
                    title="1. Upload Material",
                    description="Easily upload your PDF documents. Our system processes your files securely and prepares them for question generation.",
                ),
                feature_card(
                    icon="bot",
                    title="2. Generate Questions",
                    description="Leverage AI to generate a variety of question types, including text-based and image-based questions, tailored to your content.",
                ),
                feature_card(
                    icon="download",
                    title="3. Review & Download",
                    description="Review all generated questions, make edits, and download them as QTI packages or printable Word documents.",
                ),
                feature_card(
                    icon="graduation-cap",
                    title="4. Publish to Students",
                    description="Manage sections and standards, publish reviewed assessments, and score essay responses for the separate student app.",
                ),
                class_name="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-6 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4",
            ),
            class_name="w-full",
        ),
        class_name="font-['Inter'] bg-gradient-to-b from-gray-50 to-white min-h-screen overflow-x-hidden",
    )
