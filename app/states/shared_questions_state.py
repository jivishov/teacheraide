"""
Shared Questions State

Uses Reflex's rx.SharedState for real-time state sharing across browser tabs.
All tabs linked to the same session token share the same question data.
"""

import reflex as rx
import logging
from typing import List


class SharedQuestionsState(rx.SharedState):
    """Shared state for questions across all browser tabs."""

    # Question data - shared across all linked tabs
    text_questions_xml: List[str] = []
    image_questions_xml: List[str] = []
    image_filenames: List[str] = []

    @rx.event
    async def link_to_session(self, token: str):
        """Link this client to a shared session token."""
        if token and not self._linked_to:
            try:
                await self._link_to(token)
                logging.info(f"Linked to shared session: {token}")
            except Exception as e:
                logging.error(f"Failed to link to session {token}: {e}")

    @rx.event
    async def unlink_from_session(self):
        """Unlink from shared session."""
        if self._linked_to:
            try:
                await self._unlink()
                logging.info("Unlinked from shared session")
            except Exception as e:
                logging.error(f"Failed to unlink from session: {e}")

    @rx.event
    def set_text_questions(self, questions: List[str]):
        """Called by TextQuestionsState after generation."""
        self.text_questions_xml = list(questions)
        logging.info(f"SharedState: Set {len(questions)} text questions")

    @rx.event
    def set_image_questions(self, questions: List[str], filenames: List[str]):
        """Called by ImageQuestionsState after generation."""
        self.image_questions_xml = list(questions)
        self.image_filenames = list(filenames)
        logging.info(f"SharedState: Set {len(questions)} image questions with {len(filenames)} files")

    @rx.event
    def clear_all(self):
        """Clear all shared questions."""
        self.text_questions_xml = []
        self.image_questions_xml = []
        self.image_filenames = []
        logging.info("SharedState: Cleared all questions")

    @rx.event
    def clear_text_questions(self):
        """Clear only text questions."""
        self.text_questions_xml = []
        logging.info("SharedState: Cleared text questions")

    @rx.event
    def clear_image_questions(self):
        """Clear only image questions."""
        self.image_questions_xml = []
        self.image_filenames = []
        logging.info("SharedState: Cleared image questions")

    @rx.var
    def has_text_questions(self) -> bool:
        """Check if there are text questions."""
        return len(self.text_questions_xml) > 0

    @rx.var
    def has_image_questions(self) -> bool:
        """Check if there are image questions."""
        return len(self.image_questions_xml) > 0

    @rx.var
    def total_questions(self) -> int:
        """Total number of questions across both types."""
        return len(self.text_questions_xml) + len(self.image_questions_xml)
