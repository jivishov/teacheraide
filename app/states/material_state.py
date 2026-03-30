import reflex as rx
from io import BytesIO
import logging
from app.states.settings_state import SettingsState
from app.utils.input_limits import (
    MAX_PDF_UPLOAD_BYTES,
    exceeds_upload_limit,
    upload_limit_error,
)
from app.utils.llm_handlers import (
    get_api_key_for_provider,
    release_openai_cached_file,
)

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


def parse_page_selection(page_str: str, total: int) -> list[int]:
    pages = set()
    try:
        for part in page_str.split(","):
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-"))
                for i in range(start, end + 1):
                    if 1 <= i <= total:
                        pages.add(i - 1)
            else:
                page_num = int(part)
                if 1 <= page_num <= total:
                    pages.add(page_num - 1)
    except ValueError as e:
        logging.exception(f"Invalid page selection format: {page_str} - {e}")
        return []
    return sorted(list(pages))


class MaterialState(rx.State):
    uploaded_pdf_name: str | None = None
    num_pages: int = 0
    page_selection: str = "all"
    custom_pages: str = ""
    is_processing: bool = False
    error_message: str = ""
    extracted_pdf_name: str | None = None
    workflow_intent: str = "generate_text"

    @rx.var
    def page_selection_summary(self) -> str:
        if not self.uploaded_pdf_name:
            return "No file"
        if self.page_selection == "all":
            return f"All {self.num_pages} pages"
        if self.custom_pages:
            return f"Custom: {self.custom_pages}"
        return "Custom (not set)"

    async def _release_cached_openai_pdf(self, filename: str | None):
        if not filename:
            return

        upload_path = rx.get_upload_dir() / filename
        if not upload_path.exists():
            return

        try:
            pdf_bytes = upload_path.read_bytes()
        except OSError:
            logging.warning("Failed to read cached PDF for cleanup: %s", upload_path)
            return

        settings_state = await self.get_state(SettingsState)
        api_key = get_api_key_for_provider("openai") or settings_state.openai_api_key
        if not api_key:
            return

        await release_openai_cached_file(api_key, pdf_bytes)

    def _consume_workflow_intent_once(self) -> str:
        """Consume routing intent so it does not leak into future page visits."""
        intent = self.workflow_intent
        self.workflow_intent = "generate_text"
        return intent

    def _reset_upload_state(self):
        self.uploaded_pdf_name = None
        self.num_pages = 0
        self.page_selection = "all"
        self.custom_pages = ""
        self.is_processing = False
        self.error_message = ""
        self.extracted_pdf_name = None

    async def _cleanup_uploaded_pdf_files(
        self,
        uploaded_filename: str | None,
        extracted_filename: str | None,
    ):
        upload_dir = rx.get_upload_dir()
        filenames = []
        for filename in (uploaded_filename, extracted_filename):
            if filename and filename not in filenames:
                filenames.append(filename)

        for filename in filenames:
            await self._release_cached_openai_pdf(filename)
            file_path = upload_dir / filename
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                logging.warning("Failed to delete uploaded PDF during cleanup: %s", file_path)

    @rx.event
    def set_workflow_intent(self, value: str):
        allowed = {"generate_text", "generate_image", "convert_pdf_questions"}
        if value in allowed:
            self.workflow_intent = value

    @rx.event
    def set_page_selection(self, value: str):
        if value in {"all", "custom"}:
            self.page_selection = value

    @rx.event
    def set_custom_pages(self, value: str):
        self.custom_pages = value

    @rx.event
    def go_to_text_questions(self):
        self.workflow_intent = "generate_text"
        return rx.redirect("/text-questions")

    @rx.event
    def go_to_image_questions(self):
        self.workflow_intent = "generate_image"
        return rx.redirect("/image-questions")

    @rx.event
    def go_to_pdf_question_conversion(self):
        self.workflow_intent = "convert_pdf_questions"
        return rx.redirect("/text-questions")

    @rx.event
    async def clear_uploaded_pdf(self):
        await self._cleanup_uploaded_pdf_files(
            self.uploaded_pdf_name,
            self.extracted_pdf_name,
        )
        self._reset_upload_state()
        return rx.clear_selected_files("pdf-upload")

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        clear_upload = rx.clear_selected_files("pdf-upload")
        if not files:
            return clear_upload
        if PyPDF2 is None:
            self.error_message = "PDF support is unavailable. Install PyPDF2 to upload and extract PDFs."
            return clear_upload
        upload_file = files[0]
        await self._cleanup_uploaded_pdf_files(
            self.uploaded_pdf_name,
            self.extracted_pdf_name,
        )
        self._reset_upload_state()
        try:
            upload_data = await upload_file.read()
            if exceeds_upload_limit(len(upload_data), MAX_PDF_UPLOAD_BYTES):
                self.error_message = upload_limit_error("PDF", MAX_PDF_UPLOAD_BYTES)
                return clear_upload
            upload_dir = rx.get_upload_dir()
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / upload_file.name
            with file_path.open("wb") as f:
                f.write(upload_data)
            self.uploaded_pdf_name = upload_file.name
            reader = PyPDF2.PdfReader(BytesIO(upload_data))
            self.num_pages = len(reader.pages)
        except Exception as e:
            self.error_message = f"Failed to process PDF: {e}"
            logging.exception("Error during PDF upload and processing")
        return clear_upload

    @rx.event
    def extract_pages(self):
        if PyPDF2 is None:
            self.error_message = "PDF support is unavailable. Install PyPDF2 to extract pages."
            return
        if not self.uploaded_pdf_name:
            self.error_message = "No PDF uploaded."
            return
        self.is_processing = True
        self.error_message = ""
        self.extracted_pdf_name = None
        yield
        try:
            upload_dir = rx.get_upload_dir()
            original_path = upload_dir / self.uploaded_pdf_name
            with original_path.open("rb") as f:
                pdf_bytes = f.read()
            if self.page_selection == "all":
                self.extracted_pdf_name = self.uploaded_pdf_name
            else:
                page_indices = parse_page_selection(self.custom_pages, self.num_pages)
                if not page_indices:
                    self.error_message = "Invalid custom page range."
                    self.is_processing = False
                    return
                reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
                writer = PyPDF2.PdfWriter()
                for i in page_indices:
                    writer.add_page(reader.pages[i])
                extracted_bytes = BytesIO()
                writer.write(extracted_bytes)
                extracted_bytes.seek(0)
                new_filename = f"extracted_{self.uploaded_pdf_name}"
                new_filepath = upload_dir / new_filename
                with new_filepath.open("wb") as f:
                    f.write(extracted_bytes.read())
                self.extracted_pdf_name = new_filename
        except Exception as e:
            self.error_message = f"Failed to extract pages: {e}"
            logging.exception("Error during page extraction")
        finally:
            self.is_processing = False
