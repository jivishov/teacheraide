"""
Image Questions Utility

Helper functions for processing image-based question generation.
Adapted from Streamlit version - removed UI dependencies, kept core business logic.
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional


def load_prompts_from_xml(filepath: str) -> Optional[Dict[str, str]]:
    """
    Loads instruction prompts from an XML file.

    Modified from Streamlit version:
    - Removed st.error/st.info calls
    - Uses logging instead
    - Returns None on error instead of stopping execution

    Parameters:
        filepath (str): Path to the XML file containing prompts

    Returns:
        dict: Dictionary mapping prompt types to prompt text, or None on error

    XML Format Expected:
        <prompts>
            <prompt type="mcq">Prompt text for MCQ...</prompt>
            <prompt type="tf">Prompt text for T/F...</prompt>
            ...
        </prompts>
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        prompts = {}

        for prompt_elem in root.findall('prompt'):
            prompt_type = prompt_elem.get('type')
            prompt_text = prompt_elem.text.strip() if prompt_elem.text else ""

            if prompt_type and prompt_text:
                prompts[prompt_type] = prompt_text

        if not prompts:
            logging.error(f"No prompts found in {filepath}. Check XML structure.")
            return None

        logging.info(f"Successfully loaded {len(prompts)} prompts from: {filepath}")
        return prompts

    except FileNotFoundError:
        logging.error(f"Prompt file not found: {filepath}")
        logging.error(f"Current working directory: {Path.cwd()}")
        return None
    except ET.ParseError as e:
        logging.error(f"Error parsing {filepath}: {e}. Check XML syntax.")
        return None
    except Exception as e:
        logging.error(f"Error loading prompts from {filepath}: {e}")
        return None
