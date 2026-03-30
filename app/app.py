# Load environment variables first (before any other imports that might use them)
try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is optional in some environments.
    def load_dotenv(*_args, **_kwargs):
        return False


load_dotenv()

import reflex as rx

from app.pages.image_questions_page import image_questions, image_questions_v2
from app.pages.image_questions_page_v0 import image_questions_v0
from app.pages.landing_page import index
from app.pages.reading_material_page import reading_material
from app.pages.review_page import review_download
from app.pages.settings_page import settings
from app.pages.text_questions_page import text_questions, text_questions_v2
from app.pages.text_questions_page_v0 import text_questions_v0
from app.pages.text_questions_mock import text_questions_mock
from app.pages.upload_material_page import upload_material
from app.pages.reading_material_page_v2 import reading_material_v2
from app.states.image_questions_state import ImageQuestionsState
from app.states.reading_material_state import ReadingMaterialState
from app.states.review_state import ReviewState
from app.states.settings_state import SettingsState
from app.states.text_questions_state import TextQuestionsState


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800;900&display=swap",
            rel="stylesheet",
        ),
    ],
)

app.add_page(index, on_load=SettingsState.load_settings)
app.add_page(review_download, route="/review-download", on_load=ReviewState.on_load)
app.add_page(upload_material, route="/upload-material")
app.add_page(text_questions, route="/text-questions", on_load=TextQuestionsState.initialize_model_selection)
app.add_page(text_questions_v0, route="/text-questions-v0", on_load=TextQuestionsState.initialize_model_selection)
app.add_page(image_questions, route="/image-questions", on_load=ImageQuestionsState.initialize_model_selection)
app.add_page(image_questions_v0, route="/image-questions-v0", on_load=ImageQuestionsState.initialize_model_selection)
app.add_page(settings, route="/settings", on_load=SettingsState.load_settings)
app.add_page(reading_material, route="/reading-material", on_load=ReadingMaterialState.initialize_model_selection)
app.add_page(reading_material_v2, route="/reading-material-v2")
app.add_page(
    text_questions_v2,
    route="/text-questions-v2",
    on_load=TextQuestionsState.initialize_model_selection,
)
app.add_page(
    image_questions_v2,
    route="/image-questions-v2",
    on_load=ImageQuestionsState.initialize_model_selection,
)
app.add_page(text_questions_mock, route="/text-questions-mock")
