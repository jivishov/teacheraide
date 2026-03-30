import reflex as rx
from typing import TypedDict, Any, Dict, List
import xml.etree.ElementTree as ET
import logging
import re
from datetime import datetime
from app.utils.combined_questions import (
    create_package_with_warnings,
    combine_questions_from_state,
    get_question_count_summary,
    store_questions,
)
from app.utils.docx_converter import QTIToDocxConverter
from app.utils.question_upload import (
    process_uploaded_questions_with_report,
    get_upload_summary,
)
from app.utils.local_storage import get_load_all_questions_script, get_clear_all_questions_script
from app.utils.qti_review_parser import parse_qti_question_for_review


class Choice(TypedDict):
    id: str
    text: str


class OrderItem(TypedDict):
    id: str
    text: str


class MatchPair(TypedDict):
    source_id: str
    source_text: str
    target_id: str
    target_text: str


class FIBAnswer(TypedDict):
    blank_num: int
    answers: list[str]


class Question(TypedDict):
    type: str
    prompt: str
    choices: list[Choice]
    correct: list[str]
    img_src: str | None
    # For Order questions
    order_items: list[OrderItem]
    correct_order: list[str]
    # For Match questions
    match_pairs: list[MatchPair]
    # For FIB questions
    fib_answers: list[FIBAnswer]
    prompt_with_blanks: str
    # For Essay questions
    expected_lines: int
    # For Numeric questions
    numeric_answer: str
    numeric_expected_length: int


class QuestionWithMetadata(TypedDict):
    """Question with source metadata for edit/delete operations."""
    question: Question
    source_type: str  # "text" or "image"
    original_index: int


class ReviewState(rx.State):
    title: str = "My Assessment"
    text_questions: list[Question] = []
    image_questions: list[Question] = []

    # Store raw question data from generation states
    text_questions_data: Dict = {}  # {questions: [], timestamp: ""}
    image_questions_data: Dict = {}  # {questions: [], media_files: {}, timestamp: ""}
    text_questions_xml: List[str] = []
    image_questions_xml: List[str] = []
    image_media_files: Dict[str, bytes] = {}

    # Delete modal state
    delete_modal_open: bool = False
    deleting_source_type: str = ""  # "text" or "image"
    deleting_original_index: int = -1

    # Edit modal state
    edit_modal_open: bool = False
    editing_source_type: str = ""  # "text" or "image"
    editing_original_index: int = -1
    editing_question_type: str = ""  # "MCQ", "MRQ", etc.

    # Edit form fields
    edit_prompt: str = ""
    edit_choices: List[Dict[str, str]] = []  # [{id: "A", text: "..."}, ...]
    edit_correct_answers: List[str] = []

    # FIB edit fields
    edit_fib_segments: List[str] = []  # Text segments between blanks
    edit_fib_answers: List[List[str]] = []  # Answers for each blank [[ans1], [ans2]]

    # Order edit fields
    edit_order_items: List[Dict[str, str]] = []  # [{id, text}, ...]

    # Match edit fields
    edit_match_pairs: List[Dict[str, str]] = []  # [{source_id, source_text, target_id, target_text}, ...]

    # Upload state
    upload_modal_open: bool = False
    upload_processing: bool = False
    upload_errors: List[str] = []
    upload_warnings: List[str] = []
    upload_preview_count: int = 0
    upload_preview_summary: Dict[str, int] = {}
    pending_upload_xml: List[str] = []
    pending_upload_media: Dict[str, bytes] = {}
    upload_mode: str = "append"  # "append" or "replace"
    upload_file_count: int = 0  # Number of files uploaded

    # Clear all modal state
    clear_all_modal_open: bool = False

    # Pending localStorage data (for cross-tab question loading)
    pending_local_text_questions: List[str] = []
    pending_local_image_questions: List[str] = []
    pending_local_image_filenames: List[str] = []
    local_storage_checked: bool = False
    xml_parse_cache: Dict[str, Question] = {}
    action_status_message: str = ""
    action_status_type: str = "success"

    # Explicit setters for modal state (required by Reflex 0.9+)
    @rx.event
    def set_title(self, value: str):
        self.title = value

    @rx.event
    def set_delete_modal_open(self, value: bool):
        self.delete_modal_open = value
        if not value:
            # Reset delete state when modal closes
            self.deleting_source_type = ""
            self.deleting_original_index = -1

    @rx.event
    def set_edit_modal_open(self, value: bool):
        self.edit_modal_open = value
        if not value:
            # Reset edit form when modal closes
            self._reset_edit_form()

    @rx.event
    def set_upload_modal_open(self, value: bool):
        self.upload_modal_open = value
        if not value:
            # Reset upload state when modal closes
            self._reset_upload_state()

    def _reset_upload_state(self):
        """Reset all upload-related state."""
        self.upload_processing = False
        self.upload_errors = []
        self.upload_warnings = []
        self.upload_preview_count = 0
        self.upload_preview_summary = {}
        self.pending_upload_xml = []
        self.pending_upload_media = {}
        self.upload_mode = "append"
        self.upload_file_count = 0

    @rx.event
    def set_upload_mode(self, mode: str):
        """Set the upload mode (append or replace)."""
        self.upload_mode = mode

    @rx.event
    def open_upload_modal(self):
        """Open the upload modal."""
        self._reset_upload_state()
        self.upload_modal_open = True

    @rx.event
    def close_upload_modal(self):
        """Close the upload modal without importing."""
        self.upload_modal_open = False
        self._reset_upload_state()

    @rx.event
    def clear_action_status(self):
        """Clear transient review action status message."""
        self.action_status_message = ""

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle file upload and parse questions from multiple files."""
        self.upload_processing = True
        self.upload_errors = []
        self.upload_warnings = []

        if not files:
            self.upload_errors = ["No files selected"]
            self.upload_processing = False
            return

        try:
            all_questions_xml: List[str] = []
            all_media_files: Dict[str, bytes] = {}
            all_errors: List[str] = []
            all_warnings: List[str] = []

            # Process each uploaded file
            for file in files:
                filename = file.filename
                file_bytes = await file.read()

                # Process the uploaded file
                questions_xml, media_files, errors, warnings = process_uploaded_questions_with_report(
                    filename,
                    file_bytes,
                )

                if errors:
                    # Prefix errors with filename for clarity
                    all_errors.extend([f"{filename}: {err}" for err in errors])
                if warnings:
                    all_warnings.extend([f"{filename}: {warn}" for warn in warnings])

                if questions_xml:
                    all_questions_xml.extend(questions_xml)
                    all_media_files.update(media_files)

            # Set combined results
            if all_errors:
                self.upload_errors = all_errors
            if all_warnings:
                self.upload_warnings = all_warnings

            if all_questions_xml:
                self.pending_upload_xml = all_questions_xml
                self.pending_upload_media = all_media_files
                self.upload_preview_count = len(all_questions_xml)
                self.upload_preview_summary = get_upload_summary(all_questions_xml)
                self.upload_file_count = len(files)
                logging.info(f"Upload preview: {self.upload_preview_count} questions from {len(files)} files, summary: {self.upload_preview_summary}")
            else:
                if not all_errors:
                    self.upload_errors = ["No valid questions found in the uploaded files"]

        except Exception as e:
            logging.exception(f"Error processing upload: {e}")
            self.upload_errors = [f"Error processing files: {str(e)}"]

        self.upload_processing = False

    @rx.event
    async def confirm_upload(self):
        """Confirm and import the uploaded questions."""
        if not self.pending_upload_xml:
            self.upload_errors = ["No questions to import"]
            return

        try:
            # Handle replace mode - clear all existing questions first
            if self.upload_mode == "replace":
                # Clear ReviewState
                self.text_questions_xml = []
                self.text_questions = []
                self.text_questions_data = {}
                self.image_questions_xml = []
                self.image_questions = []
                self.image_questions_data = {}
                self.image_media_files = {}

                # Also clear source states to prevent refresh from pulling old data
                from app.states.text_questions_state import TextQuestionsState
                from app.states.image_questions_state import ImageQuestionsState

                text_state = await self.get_state(TextQuestionsState)
                text_state.xml_questions = []

                image_state = await self.get_state(ImageQuestionsState)
                image_state.xml_questions = []
                image_state.media_files = {}

                logging.info("Replace mode: cleared all existing questions including source states")

            # Add uploaded questions to text_questions (treating uploads as text-based)
            new_text_xml = list(self.text_questions_xml) + list(self.pending_upload_xml)
            self.text_questions_xml = new_text_xml

            # Merge media files
            if self.pending_upload_media:
                new_media = dict(self.image_media_files)
                new_media.update(self.pending_upload_media)
                self.image_media_files = new_media

            # Update text_questions_data for downloads
            self.text_questions_data = store_questions(
                self.text_questions_xml,
                media_files=None,
                source_type="text"
            )

            # Re-parse all questions
            text_parsed = []
            for xml_str in self.text_questions_xml:
                parsed_q = self._parse_xml_cached(xml_str)
                if parsed_q:
                    text_parsed.append(parsed_q)
            self.text_questions = text_parsed

            mode_str = "replaced" if self.upload_mode == "replace" else "appended"
            logging.info(f"Imported {len(self.pending_upload_xml)} questions successfully ({mode_str})")

            # Close modal and reset
            self.upload_modal_open = False
            self._reset_upload_state()

        except Exception as e:
            logging.exception(f"Error importing questions: {e}")
            self.upload_errors = [f"Error importing questions: {str(e)}"]

    mock_mcq_xml = """<?xml version="1.0" encoding="UTF-8"?>
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p2" identifier="MCQ_1" title="Sample MCQ">
  <responseDeclaration identifier="RESPONSE" cardinality="single">
    <correctResponse>
      <value>B</value>
    </correctResponse>
  </responseDeclaration>
  <itemBody>
    <choiceInteraction responseIdentifier="RESPONSE" shuffle="true">
      <prompt>What is the capital of France?</prompt>
      <simpleChoice identifier="A">London</simpleChoice>
      <simpleChoice identifier="B">Paris</simpleChoice>
      <simpleChoice identifier="C">Berlin</simpleChoice>
      <simpleChoice identifier="D">Madrid</simpleChoice>
    </choiceInteraction>
  </itemBody>
</assessmentItem>"""

    @rx.var
    def question_summary(self) -> dict[str, int]:
        summary = {"MCQ": 0, "TF": 0, "FIB": 0, "Essay": 0, "MRQ": 0, "Match": 0, "Order": 0, "Numeric": 0}
        all_questions = self.text_questions + self.image_questions
        for q in all_questions:
            if q["type"] in summary:
                summary[q["type"]] += 1
        return summary

    @rx.var
    def total_questions(self) -> int:
        return len(self.text_questions) + len(self.image_questions)

    @rx.var
    def text_questions_count(self) -> int:
        return len(self.text_questions)

    @rx.var
    def image_questions_count(self) -> int:
        return len(self.image_questions)

    @rx.var
    def filtered_questions(self) -> list[Question]:
        """Returns all questions combined."""
        return self.text_questions + self.image_questions

    @rx.var
    def filtered_questions_with_metadata(self) -> list[QuestionWithMetadata]:
        """Returns all questions with source metadata for edit/delete operations."""
        result: list[QuestionWithMetadata] = []

        for i, q in enumerate(self.text_questions):
            result.append({
                "question": q,
                "source_type": "text",
                "original_index": i
            })

        for i, q in enumerate(self.image_questions):
                result.append({
                    "question": q,
                    "source_type": "image",
                    "original_index": i
                })

        return result

    # ============ DELETE HANDLERS ============

    @rx.event
    def open_delete_modal(self, source_type: str, original_index: int):
        """Open delete confirmation modal."""
        self.deleting_source_type = source_type
        self.deleting_original_index = original_index
        self.delete_modal_open = True

    @rx.event
    def close_delete_modal(self):
        """Close delete modal without deleting."""
        self.delete_modal_open = False
        self.deleting_source_type = ""
        self.deleting_original_index = -1

    @rx.event
    def confirm_delete_question(self):
        """Delete question from both parsed list and XML list."""
        source_type = self.deleting_source_type
        idx = self.deleting_original_index

        if idx < 0:
            self.close_delete_modal()
            return

        if source_type == "text":
            if idx < len(self.text_questions):
                # Create new lists without the deleted item
                new_questions = [q for i, q in enumerate(self.text_questions) if i != idx]
                new_xml = [x for i, x in enumerate(self.text_questions_xml) if i != idx]
                self.text_questions = new_questions
                self.text_questions_xml = new_xml
                # Update text_questions_data for downloads (full reassignment for Reflex reactivity)
                self.text_questions_data = store_questions(new_xml, media_files=None, source_type="text")
        else:  # image
            if idx < len(self.image_questions):
                new_questions = [q for i, q in enumerate(self.image_questions) if i != idx]
                new_xml = [x for i, x in enumerate(self.image_questions_xml) if i != idx]
                self.image_questions = new_questions
                self.image_questions_xml = new_xml
                # Update image_questions_data for downloads (full reassignment for Reflex reactivity)
                self.image_questions_data = store_questions(new_xml, media_files=self.image_media_files, source_type="image")

        self.close_delete_modal()
        self.action_status_type = "success"
        self.action_status_message = "Question deleted."

    # ============ EDIT HANDLERS ============

    @rx.event
    def open_edit_modal(self, source_type: str, original_index: int):
        """Open edit modal and populate form with question data."""
        self.editing_source_type = source_type
        self.editing_original_index = original_index

        # Get the question to edit
        if source_type == "text" and original_index < len(self.text_questions):
            question = self.text_questions[original_index]
        elif source_type == "image" and original_index < len(self.image_questions):
            question = self.image_questions[original_index]
        else:
            return

        # Populate form fields
        self.editing_question_type = question["type"]
        self.edit_choices = [{"id": c["id"], "text": c["text"]} for c in question["choices"]]
        self.edit_correct_answers = list(question["correct"])

        # Handle FIB questions specially
        if question["type"] == "FIB":
            # Parse segments from prompt_with_blanks
            # "Text [BLANK 1] more text [BLANK 2] end" → ["Text ", " more text ", " end"]
            prompt_with_blanks = question.get("prompt_with_blanks", "")
            segments = re.split(r'\[BLANK \d+\]', prompt_with_blanks)
            self.edit_fib_segments = segments

            # Get answers for each blank
            fib_answers = question.get("fib_answers", [])
            self.edit_fib_answers = [ans.get("answers", []) for ans in fib_answers]

            # Use prompt_with_blanks for display
            self.edit_prompt = prompt_with_blanks
        else:
            self.edit_prompt = question["prompt"]
            # Reset FIB fields
            self.edit_fib_segments = []
            self.edit_fib_answers = []

        # Handle Order questions
        if question["type"] == "Order":
            order_items = question.get("order_items", [])
            self.edit_order_items = [{"id": item["id"], "text": item["text"]} for item in order_items]
        else:
            self.edit_order_items = []

        # Handle Match questions
        if question["type"] == "Match":
            match_pairs = question.get("match_pairs", [])
            self.edit_match_pairs = [
                {
                    "source_id": pair["source_id"],
                    "source_text": pair["source_text"],
                    "target_id": pair["target_id"],
                    "target_text": pair["target_text"]
                }
                for pair in match_pairs
            ]
        else:
            self.edit_match_pairs = []

        self.edit_modal_open = True

    @rx.event
    def close_edit_modal(self):
        """Close edit modal without saving."""
        self.edit_modal_open = False
        self._reset_edit_form()

    def _reset_edit_form(self):
        """Reset all edit form fields."""
        self.editing_source_type = ""
        self.editing_original_index = -1
        self.editing_question_type = ""
        self.edit_prompt = ""
        self.edit_choices = []
        self.edit_correct_answers = []

    @rx.event
    def set_edit_prompt(self, value: str):
        """Update edit prompt field."""
        self.edit_prompt = value

    @rx.event
    def set_edit_choice_text(self, choice_index: int, value: str):
        """Update a specific choice's text by index."""
        if 0 <= choice_index < len(self.edit_choices):
            new_choices = list(self.edit_choices)
            new_choices[choice_index] = {"id": new_choices[choice_index]["id"], "text": value}
            self.edit_choices = new_choices

    @rx.event
    def toggle_correct_answer(self, choice_id: str):
        """Toggle whether a choice is marked as correct."""
        new_correct = list(self.edit_correct_answers)
        if choice_id in new_correct:
            new_correct.remove(choice_id)
        else:
            # For MCQ and TF, only allow one correct answer
            if self.editing_question_type in ["MCQ", "TF"]:
                new_correct = [choice_id]
            else:
                new_correct.append(choice_id)
        self.edit_correct_answers = new_correct

    @rx.event
    def set_fib_segment(self, index: int, value: str):
        """Update a specific FIB text segment."""
        if 0 <= index < len(self.edit_fib_segments):
            new_segments = list(self.edit_fib_segments)
            new_segments[index] = value
            self.edit_fib_segments = new_segments

    @rx.event
    def set_fib_answer(self, blank_index: int, value: str):
        """Update the answer for a specific blank."""
        if 0 <= blank_index < len(self.edit_fib_answers):
            new_answers = [list(ans) for ans in self.edit_fib_answers]
            new_answers[blank_index] = [value]  # Single answer per blank
            self.edit_fib_answers = new_answers

    @rx.event
    def set_order_item_text(self, index: int, value: str):
        """Update the text of an order item at specific index."""
        if 0 <= index < len(self.edit_order_items):
            new_items = [dict(item) for item in self.edit_order_items]
            new_items[index]["text"] = value
            self.edit_order_items = new_items

    @rx.event
    def set_match_source_text(self, index: int, value: str):
        """Update the source text of a match pair at specific index."""
        if 0 <= index < len(self.edit_match_pairs):
            new_pairs = [dict(pair) for pair in self.edit_match_pairs]
            new_pairs[index]["source_text"] = value
            self.edit_match_pairs = new_pairs

    @rx.event
    def set_match_target_text(self, index: int, value: str):
        """Update the target text of a match pair at specific index."""
        if 0 <= index < len(self.edit_match_pairs):
            new_pairs = [dict(pair) for pair in self.edit_match_pairs]
            new_pairs[index]["target_text"] = value
            self.edit_match_pairs = new_pairs

    @rx.event
    def save_edited_question(self):
        """Save edits to both parsed objects and XML strings."""
        source_type = self.editing_source_type
        idx = self.editing_original_index

        if idx < 0:
            self.close_edit_modal()
            return

        if source_type == "text" and idx < len(self.text_questions):
            # Update the parsed Question object
            new_questions = list(self.text_questions)
            updated_q = dict(new_questions[idx])
            updated_q["prompt"] = self.edit_prompt
            updated_q["choices"] = self.edit_choices
            updated_q["correct"] = self.edit_correct_answers

            # Handle FIB-specific updates
            if self.editing_question_type == "FIB":
                # Rebuild prompt_with_blanks from segments
                parts = []
                for i, seg in enumerate(self.edit_fib_segments):
                    parts.append(seg)
                    if i < len(self.edit_fib_answers):
                        parts.append(f"[BLANK {i + 1}]")
                # Remove the trailing blank marker if segments > answers
                if len(self.edit_fib_segments) > len(self.edit_fib_answers):
                    updated_q["prompt_with_blanks"] = "".join(parts)
                else:
                    updated_q["prompt_with_blanks"] = "".join(parts[:-1]) if parts else ""
                # Update fib_answers
                updated_q["fib_answers"] = [
                    {"blank_num": i + 1, "answers": ans}
                    for i, ans in enumerate(self.edit_fib_answers)
                ]

            # Handle Order-specific updates
            if self.editing_question_type == "Order":
                updated_q["order_items"] = self.edit_order_items

            # Handle Match-specific updates
            if self.editing_question_type == "Match":
                updated_q["match_pairs"] = self.edit_match_pairs

            new_questions[idx] = updated_q
            self.text_questions = new_questions

            # Update the XML string
            if idx < len(self.text_questions_xml):
                updated_xml = self._update_xml_from_edits(
                    self.text_questions_xml[idx],
                    self.edit_prompt,
                    self.edit_choices,
                    self.edit_correct_answers,
                    q_type=self.editing_question_type,
                    fib_segments=self.edit_fib_segments if self.editing_question_type == "FIB" else None,
                    fib_answers=self.edit_fib_answers if self.editing_question_type == "FIB" else None,
                    order_items=self.edit_order_items if self.editing_question_type == "Order" else None,
                    match_pairs=self.edit_match_pairs if self.editing_question_type == "Match" else None
                )
                new_xml = list(self.text_questions_xml)
                new_xml[idx] = updated_xml
                self.text_questions_xml = new_xml

                # Update text_questions_data for downloads (full reassignment for Reflex reactivity)
                self.text_questions_data = store_questions(new_xml, media_files=None, source_type="text")

        elif source_type == "image" and idx < len(self.image_questions):
            # Update the parsed Question object
            new_questions = list(self.image_questions)
            updated_q = dict(new_questions[idx])
            updated_q["prompt"] = self.edit_prompt
            updated_q["choices"] = self.edit_choices
            updated_q["correct"] = self.edit_correct_answers

            # Handle FIB-specific updates
            if self.editing_question_type == "FIB":
                # Rebuild prompt_with_blanks from segments
                parts = []
                for i, seg in enumerate(self.edit_fib_segments):
                    parts.append(seg)
                    if i < len(self.edit_fib_answers):
                        parts.append(f"[BLANK {i + 1}]")
                if len(self.edit_fib_segments) > len(self.edit_fib_answers):
                    updated_q["prompt_with_blanks"] = "".join(parts)
                else:
                    updated_q["prompt_with_blanks"] = "".join(parts[:-1]) if parts else ""
                updated_q["fib_answers"] = [
                    {"blank_num": i + 1, "answers": ans}
                    for i, ans in enumerate(self.edit_fib_answers)
                ]

            # Handle Order-specific updates
            if self.editing_question_type == "Order":
                updated_q["order_items"] = self.edit_order_items

            # Handle Match-specific updates
            if self.editing_question_type == "Match":
                updated_q["match_pairs"] = self.edit_match_pairs

            new_questions[idx] = updated_q
            self.image_questions = new_questions

            # Update the XML string
            if idx < len(self.image_questions_xml):
                updated_xml = self._update_xml_from_edits(
                    self.image_questions_xml[idx],
                    self.edit_prompt,
                    self.edit_choices,
                    self.edit_correct_answers,
                    q_type=self.editing_question_type,
                    fib_segments=self.edit_fib_segments if self.editing_question_type == "FIB" else None,
                    fib_answers=self.edit_fib_answers if self.editing_question_type == "FIB" else None,
                    order_items=self.edit_order_items if self.editing_question_type == "Order" else None,
                    match_pairs=self.edit_match_pairs if self.editing_question_type == "Match" else None
                )
                new_xml = list(self.image_questions_xml)
                new_xml[idx] = updated_xml
                self.image_questions_xml = new_xml

                # Update image_questions_data for downloads (full reassignment for Reflex reactivity)
                self.image_questions_data = store_questions(new_xml, media_files=self.image_media_files, source_type="image")

        self.close_edit_modal()
        self.action_status_type = "success"
        self.action_status_message = "Question updated."

    def _update_xml_from_edits(self, xml_string: str, prompt: str,
                                choices: List[Dict[str, str]],
                                correct_answers: List[str],
                                q_type: str = "",
                                fib_segments: List[str] = None,
                                fib_answers: List[List[str]] = None,
                                order_items: List[Dict[str, str]] = None,
                                match_pairs: List[Dict[str, str]] = None) -> str:
        """Update XML string with edited question data."""
        try:
            # Register namespace to preserve it in output
            ET.register_namespace('', "http://www.imsglobal.org/xsd/imsqti_v2p2")
            ns = {"qti": "http://www.imsglobal.org/xsd/imsqti_v2p2"}

            root = ET.fromstring(xml_string)

            # Handle FIB questions specially
            if q_type == "FIB" and fib_segments:
                # Update text segments in the <p> element
                item_body = root.find("qti:itemBody", ns)
                if item_body is not None:
                    p_elem = item_body.find(".//qti:p", ns)
                    if p_elem is not None:
                        # Update the text before first interaction
                        p_elem.text = str(fib_segments[0]) if fib_segments else ""

                        # Update tail text after each textEntryInteraction
                        interactions = p_elem.findall("qti:textEntryInteraction", ns)
                        for i, interaction in enumerate(interactions):
                            if i + 1 < len(fib_segments):
                                interaction.tail = str(fib_segments[i + 1])

                # Update answers in responseDeclaration elements
                if fib_answers:
                    response_decls = root.findall(".//qti:responseDeclaration", ns)
                    blank_idx = 0
                    for decl in response_decls:
                        resp_id = decl.get("identifier", "")
                        if resp_id.startswith("RESPONSE") and blank_idx < len(fib_answers):
                            correct_resp = decl.find("qti:correctResponse", ns)
                            if correct_resp is not None:
                                # Clear existing values
                                for val in list(correct_resp.findall("qti:value", ns)):
                                    correct_resp.remove(val)
                                # Add new answer(s)
                                for ans in fib_answers[blank_idx]:
                                    val_el = ET.SubElement(correct_resp, "{http://www.imsglobal.org/xsd/imsqti_v2p2}value")
                                    val_el.text = str(ans)
                            blank_idx += 1

            # Handle Order questions
            elif q_type == "Order" and order_items:
                # Update prompt
                prompt_el = root.find(".//qti:prompt", ns)
                if prompt_el is not None:
                    prompt_el.text = str(prompt)

                # Update simpleChoice text in orderInteraction
                for item in order_items:
                    item_id = str(item['id'])
                    choice_el = root.find(f".//qti:simpleChoice[@identifier='{item_id}']", ns)
                    if choice_el is not None:
                        choice_el.text = str(item["text"])
                        # Remove any child elements but keep attributes
                        for child in list(choice_el):
                            choice_el.remove(child)

            # Handle Match questions
            elif q_type == "Match" and match_pairs:
                # Update prompt
                prompt_el = root.find(".//qti:prompt", ns)
                if prompt_el is not None:
                    prompt_el.text = str(prompt)

                # Update simpleAssociableChoice text in both matchSets
                # First, collect all unique source and target updates
                source_updates = {str(pair['source_id']): str(pair['source_text']) for pair in match_pairs}
                target_updates = {str(pair['target_id']): str(pair['target_text']) for pair in match_pairs}

                # Update source choices (first simpleMatchSet)
                match_sets = root.findall(".//qti:simpleMatchSet", ns)
                if len(match_sets) >= 2:
                    for choice in match_sets[0].findall(".//qti:simpleAssociableChoice", ns):
                        identifier = choice.get("identifier", "")
                        if identifier in source_updates:
                            choice.text = source_updates[identifier]
                            for child in list(choice):
                                choice.remove(child)

                    # Update target choices (second simpleMatchSet)
                    for choice in match_sets[1].findall(".//qti:simpleAssociableChoice", ns):
                        identifier = choice.get("identifier", "")
                        if identifier in target_updates:
                            choice.text = target_updates[identifier]
                            for child in list(choice):
                                choice.remove(child)

            else:
                # Standard question types (MCQ, MRQ, Essay, etc.)
                # Update prompt (convert MutableProxy to str for ElementTree)
                prompt_el = root.find(".//qti:prompt", ns)
                if prompt_el is not None:
                    prompt_el.text = str(prompt)

                # Update choice texts (for MCQ/MRQ)
                for choice in choices:
                    choice_id = str(choice['id'])
                    choice_el = root.find(f".//qti:simpleChoice[@identifier='{choice_id}']", ns)
                    if choice_el is not None:
                        # Clear existing content (convert MutableProxy to str)
                        choice_el.text = str(choice["text"])
                        # Remove any child elements but keep attributes
                        for child in list(choice_el):
                            choice_el.remove(child)

                # Update correct answer(s)
                correct_resp = root.find(".//qti:correctResponse", ns)
                if correct_resp is not None:
                    # Clear existing values
                    for val in list(correct_resp.findall("qti:value", ns)):
                        correct_resp.remove(val)
                    # Add new correct answers (convert MutableProxy to str)
                    for ans_id in correct_answers:
                        val_el = ET.SubElement(correct_resp, "{http://www.imsglobal.org/xsd/imsqti_v2p2}value")
                        val_el.text = str(ans_id)

            # Return updated XML string
            return ET.tostring(root, encoding="unicode")

        except Exception as e:
            logging.exception(f"Error updating XML: {e}")
            # Return original if update fails
            return xml_string

    def _parse_xml(self, xml_string: str) -> Question | None:
        try:
            return parse_qti_question_for_review(xml_string)
        except Exception as e:
            logging.exception(f"XML Parse Error: {e} for xml: {xml_string}")
            return None

    def _parse_xml_cached(self, xml_string: str) -> Question | None:
        """Parse XML with simple cache to reduce repeated parsing cost."""
        cached = self.xml_parse_cache.get(xml_string)
        if cached is not None:
            return cached
        parsed = self._parse_xml(xml_string)
        if parsed is not None:
            self.xml_parse_cache[xml_string] = parsed
        return parsed

    @rx.event
    async def on_load(self):
        """Load and parse questions from source states and localStorage."""
        # Import here to avoid circular imports
        from app.states.text_questions_state import TextQuestionsState
        from app.states.image_questions_state import ImageQuestionsState

        # Pull data from TextQuestionsState only if we don't already have data
        # This preserves any edits made in ReviewState
        text_state = await self.get_state(TextQuestionsState)
        if not self.text_questions_xml and text_state.xml_questions:
            self.text_questions_xml = list(text_state.xml_questions)
            self.text_questions_data = store_questions(
                text_state.xml_questions,
                media_files=None,
                source_type="text"
            )

        # Pull data from ImageQuestionsState only if we don't already have data
        image_state = await self.get_state(ImageQuestionsState)
        if not self.image_questions_xml and image_state.xml_questions:
            self.image_questions_xml = list(image_state.xml_questions)
            self.image_questions_data = store_questions(
                image_state.xml_questions,
                media_files=image_state.media_files,
                source_type="image"
            )
            self.image_media_files = dict(image_state.media_files) if image_state.media_files else {}

        # Parse text questions
        text_parsed = []
        for xml_str in self.text_questions_xml:
            parsed_q = self._parse_xml_cached(xml_str)
            if parsed_q:
                text_parsed.append(parsed_q)
        self.text_questions = text_parsed

        # Parse image questions
        image_parsed = []
        for xml_str in self.image_questions_xml:
            parsed_q = self._parse_xml_cached(xml_str)
            if parsed_q:
                image_parsed.append(parsed_q)
        self.image_questions = image_parsed

        logging.info(f"ReviewState loaded: {len(text_parsed)} text questions, {len(image_parsed)} image questions")

        # If we still don't have questions, try localStorage (for cross-tab data)
        if not self.text_questions_xml and not self.image_questions_xml:
            self.local_storage_checked = False
            return ReviewState.load_from_local_storage

    @rx.event
    def load_from_local_storage(self):
        """Fetch question data from localStorage for cross-tab access."""
        return rx.call_script(
            get_load_all_questions_script(),
            callback=ReviewState.receive_local_storage_data
        )

    @rx.event
    async def receive_local_storage_data(self, data: dict):
        """Callback that receives localStorage data from browser and merges it."""
        if not data:
            self.local_storage_checked = True
            return

        self.pending_local_text_questions = data.get("text_questions", [])
        self.pending_local_image_questions = data.get("image_questions", [])
        self.pending_local_image_filenames = data.get("image_filenames", [])
        self.local_storage_checked = True

        # Merge localStorage data if we don't have session data
        has_local_text = bool(self.pending_local_text_questions)
        has_local_image = bool(self.pending_local_image_questions)

        if has_local_text or has_local_image:
            logging.info(f"Found localStorage data: {len(self.pending_local_text_questions)} text, {len(self.pending_local_image_questions)} image questions")
            return ReviewState.merge_local_storage_data

    @rx.event
    async def merge_local_storage_data(self):
        """Merge localStorage questions with session state questions."""
        # Merge text questions from localStorage if we don't have any
        if not self.text_questions_xml and self.pending_local_text_questions:
            self.text_questions_xml = list(self.pending_local_text_questions)
            self.text_questions_data = store_questions(
                self.pending_local_text_questions,
                media_files=None,
                source_type="text"
            )
        elif self.text_questions_xml and self.pending_local_text_questions:
            if len(self.pending_local_text_questions) != len(self.text_questions_xml):
                logging.info(
                    "Hydration conflict (text): keeping in-memory state over localStorage "
                    f"({len(self.text_questions_xml)} in-memory vs {len(self.pending_local_text_questions)} local)."
                )

        # Merge image questions from localStorage if we don't have any
        if not self.image_questions_xml and self.pending_local_image_questions:
            self.image_questions_xml = list(self.pending_local_image_questions)
            # Load media files from disk using filenames
            media_files = await self._load_media_files_from_disk(self.pending_local_image_filenames)
            self.image_media_files = media_files
            self.image_questions_data = store_questions(
                self.pending_local_image_questions,
                media_files=media_files,
                source_type="image"
            )
        elif self.image_questions_xml and self.pending_local_image_questions:
            if len(self.pending_local_image_questions) != len(self.image_questions_xml):
                logging.info(
                    "Hydration conflict (image): keeping in-memory state over localStorage "
                    f"({len(self.image_questions_xml)} in-memory vs {len(self.pending_local_image_questions)} local)."
                )

        # Parse all questions
        text_parsed = []
        for xml_str in self.text_questions_xml:
            parsed_q = self._parse_xml_cached(xml_str)
            if parsed_q:
                text_parsed.append(parsed_q)
        self.text_questions = text_parsed

        image_parsed = []
        for xml_str in self.image_questions_xml:
            parsed_q = self._parse_xml_cached(xml_str)
            if parsed_q:
                image_parsed.append(parsed_q)
        self.image_questions = image_parsed

        # Clear pending data
        self.pending_local_text_questions = []
        self.pending_local_image_questions = []
        self.pending_local_image_filenames = []

        logging.info(f"Merged localStorage data: {len(text_parsed)} text, {len(image_parsed)} image questions")

    async def _load_media_files_from_disk(self, filenames: List[str]) -> Dict[str, bytes]:
        """Load media files from disk given their filenames."""
        media_files = {}
        if not filenames:
            return media_files

        try:
            upload_dir = rx.get_upload_dir()
            for filename in filenames:
                file_path = upload_dir / filename
                if file_path.exists():
                    with file_path.open("rb") as f:
                        media_files[filename] = f.read()
                    logging.info(f"Loaded media file from disk: {filename}")
                else:
                    logging.warning(f"Media file not found on disk: {filename}")
        except Exception as e:
            logging.exception(f"Error loading media files from disk: {e}")

        return media_files

    @rx.event
    async def refresh_data(self):
        """Refresh data by re-pulling from source states."""
        await self.on_load()

    @rx.event
    def open_clear_all_modal(self):
        """Open the clear all confirmation modal."""
        self.clear_all_modal_open = True

    @rx.event
    def close_clear_all_modal(self):
        """Close the clear all confirmation modal."""
        self.clear_all_modal_open = False

    @rx.event
    async def confirm_clear_all(self):
        """Clear all questions across all states and localStorage."""
        # Clear ReviewState
        self.text_questions = []
        self.image_questions = []
        self.text_questions_xml = []
        self.image_questions_xml = []
        self.text_questions_data = {}
        self.image_questions_data = {}
        self.image_media_files = {}
        self.title = "My Assessment"
        self.xml_parse_cache = {}

        # Clear pending localStorage data
        self.pending_local_text_questions = []
        self.pending_local_image_questions = []
        self.pending_local_image_filenames = []

        # Clear TextQuestionsState
        from app.states.text_questions_state import TextQuestionsState
        text_state = await self.get_state(TextQuestionsState)
        text_state.xml_questions = []
        text_state.package_ready = False
        text_state.question_summary = []
        text_state.current_yaml = ""

        # Clear ImageQuestionsState
        from app.states.image_questions_state import ImageQuestionsState
        image_state = await self.get_state(ImageQuestionsState)
        image_state.xml_questions = []
        image_state.media_files = {}
        image_state.package_ready = False
        image_state.question_summary = []
        image_state.current_yaml = ""

        self.clear_all_modal_open = False
        logging.info("Cleared all questions from all states and localStorage")

        # Clear localStorage for cross-tab consistency
        return rx.call_script(get_clear_all_questions_script())

    @rx.event
    def clear_data(self):
        """Clear all questions and reset state (legacy - use confirm_clear_all instead)."""
        self.text_questions = []
        self.image_questions = []
        self.text_questions_xml = []
        self.image_questions_xml = []
        self.text_questions_data = {}
        self.image_questions_data = {}
        self.image_media_files = {}
        self.title = "My Assessment"
        self.xml_parse_cache = {}

    def _quality_gate_for_export(self, questions_xml: List[str]) -> tuple[bool, str]:
        """Run lightweight integrity checks before export."""
        if not questions_xml:
            return False, "No questions to export."

        ns = {"qti": "http://www.imsglobal.org/xsd/imsqti_v2p2"}
        for i, xml_str in enumerate(questions_xml, 1):
            if "__IMAGE_HTML_PLACEHOLDER__" in xml_str:
                return False, f"Question {i} has unresolved media placeholder."
            try:
                root = ET.fromstring(xml_str)
            except Exception:
                return False, f"Question {i} is not valid XML."

            prompt_el = root.find(".//qti:prompt", ns)
            if prompt_el is not None:
                prompt_text = "".join(prompt_el.itertext()).strip()
            else:
                item_body = root.find(".//qti:itemBody", ns)
                prompt_text = "".join(item_body.itertext()).strip() if item_body is not None else ""

            if not prompt_text:
                return False, f"Question {i} is missing prompt text."

        return True, ""

    @rx.event
    def download_qti(self) -> rx.download:
        """Generate and download QTI package with all questions."""
        try:
            # Combine questions from both text and image sources
            all_questions, all_media = combine_questions_from_state(
                text_questions_data=self.text_questions_data,
                image_questions_data=self.image_questions_data,
                question_types='all'
            )

            if not all_questions:
                logging.warning("No questions available to download")
                return rx.toast.error("No questions available to download")

            quality_ok, quality_msg = self._quality_gate_for_export(all_questions)
            if not quality_ok:
                return rx.toast.error(f"Export blocked: {quality_msg}")

            # Create the QTI package
            package_bytes, package_warnings = create_package_with_warnings(
                test_title=self.title,
                questions=all_questions,
                media_files=all_media,
                question_types='all',
                templates_dir="app/templates"
            )
            if package_warnings:
                self.action_status_type = "warning"
                self.action_status_message = (
                    f"{len(package_warnings)} export warning"
                    f"{'' if len(package_warnings) == 1 else 's'} detected while building QTI package."
                )

            if package_bytes:
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = "".join(c if c.isalnum() else "_" for c in self.title)
                filename = f"{safe_title}_qti_{timestamp}.zip"

                # Return download
                return rx.download(data=package_bytes, filename=filename)
            else:
                logging.error("Failed to create QTI package")
                return rx.toast.error("Failed to create QTI package")

        except Exception as e:
            logging.exception(f"Error creating QTI download: {e}")
            return rx.toast.error(f"Error: {str(e)}")

    @rx.event
    def download_docx(self) -> rx.download:
        """Generate and download DOCX document with all questions."""
        try:
            # Combine questions from both text and image sources
            all_questions, all_media = combine_questions_from_state(
                text_questions_data=self.text_questions_data,
                image_questions_data=self.image_questions_data,
                question_types='all'
            )

            if not all_questions:
                logging.warning("No questions available to download")
                return rx.toast.error("No questions available to download")

            quality_ok, quality_msg = self._quality_gate_for_export(all_questions)
            if not quality_ok:
                return rx.toast.error(f"Export blocked: {quality_msg}")

            # Create DOCX converter
            converter = QTIToDocxConverter(
                questions_xml=all_questions,
                media_files=all_media,
                title=self.title
            )

            # Generate DOCX bytes
            docx_bytes = converter.generate_docx_bytes()

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c if c.isalnum() else "_" for c in self.title)
            filename = f"{safe_title}_docx_{timestamp}.docx"

            # Return download
            return rx.download(data=docx_bytes, filename=filename)

        except Exception as e:
            logging.exception(f"Error creating DOCX download: {e}")
            return rx.toast.error(f"Error: {str(e)}")
