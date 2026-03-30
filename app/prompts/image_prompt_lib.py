import reflex as rx
import xml.etree.ElementTree as ET
from pathlib import Path
import logging


def load_prompts_from_xml(filepath: str) -> dict[str, str] | None:
    """Loads instruction prompts from an XML file."""
    try:
        prompts_path = Path(filepath)
        if not prompts_path.exists():
            logging.error(f"Prompt file not found: {filepath}")
            return None
        tree = ET.parse(prompts_path)
        root = tree.getroot()
        prompts = {}
        for prompt_elem in root.findall("prompt"):
            prompt_type = prompt_elem.get("type", "")
            prompt_text = prompt_elem.text.strip() if prompt_elem.text else ""
            if prompt_type and prompt_text:
                prompts[prompt_type] = prompt_text
        if not prompts:
            logging.warning(f"No prompts found in {filepath}. Check XML structure.")
            return None
        logging.info(f"Successfully loaded prompts from: {filepath}")
        return prompts
    except ET.ParseError as e:
        logging.exception(f"Error parsing XML prompts from {filepath}: {e}")
        return None
    except Exception as e:
        logging.exception(f"Error loading prompts from {filepath}: {e}")
        return None


def create_image_prompt(
    question_type: str, selected_subject: str, img_prompt: str
) -> str:
    """Creates a formatted prompt for generating an image-based question."""
    instruction = f"For a {selected_subject} assessment, create a {question_type} question based on the provided image. The specific prompt is: {img_prompt}."
    return instruction